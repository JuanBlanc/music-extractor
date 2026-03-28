import logging
import os
import subprocess
import json
import threading
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import Job, Track

logger = logging.getLogger(__name__)


def extract_metadata(url: str) -> list[dict]:
    """Extrae metadata de un video o playlist"""
    result = subprocess.run(
        [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            url,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"yt-dlp metadata failed: {result.stderr}")
        raise Exception(f"yt-dlp error: {result.stderr}")

    entries = []
    for line in result.stdout.strip().split('\n'):
        if line:
            entries.append(json.loads(line))

    return entries


def download_single_track(url: str, output_dir: str) -> dict:
    """Descarga y convierte un solo track a MP3"""
    # Obtener metadata
    meta_result = subprocess.run(
        [
            "yt-dlp",
            "--no-warnings",
            "--skip-download",
            "--print-json",
            url,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads(meta_result.stdout)
    title = metadata.get("title", "audio").replace("/", "-").replace("\\", "-").replace(":", "-").replace('"', "")
    duration = metadata.get("duration")

    output_path = os.path.join(output_dir, f"{title}.mp3")

    # Descargar y convertir
    subprocess.run(
        [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_path,
            url,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return {
        "title": title,
        "path": output_path,
        "duration": duration,
        "source_url": url,
    }


def process_job(job_id: str):
    """Procesa un trabajo de extraccion en background"""
    try:
        job = Job.objects.get(id=job_id)
        job.status = Job.Status.PROCESSING
        job.save()

        logger.info(f"Starting job {job_id} for URL: {job.url}")

        # Obtener lista de videos
        entries = extract_metadata(job.url)
        job.total_tracks = len(entries)
        job.save()

        logger.info(f"Job {job_id}: Found {len(entries)} tracks")

        # Crear directorio para este job
        job_media_dir = os.path.join(settings.MEDIA_ROOT, str(job_id))
        os.makedirs(job_media_dir, exist_ok=True)

        for i, entry in enumerate(entries):
            try:
                # Construir URL del video
                video_url = entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                video_title = entry.get('title', f'Track {i+1}')

                job.current_track = video_title
                job.save()

                logger.info(f"Job {job_id}: Downloading track {i+1}/{len(entries)}: {video_title}")

                # Descargar
                track_info = download_single_track(video_url, job_media_dir)

                # Guardar archivo en storage
                with open(track_info['path'], 'rb') as f:
                    file_content = f.read()

                saved_path = default_storage.save(
                    f"{job_id}/{track_info['title']}.mp3",
                    ContentFile(file_content)
                )

                # Crear registro de track
                Track.objects.create(
                    job=job,
                    title=track_info['title'],
                    file_path=saved_path,
                    duration=track_info['duration'],
                    source_url=video_url,
                )

                job.completed_tracks = i + 1
                job.save()

                logger.info(f"Job {job_id}: Completed track {i+1}/{len(entries)}")

            except subprocess.CalledProcessError as e:
                logger.warning(f"Job {job_id}: Failed to download track {i+1}: {e.stderr}")
                continue
            except Exception as e:
                logger.warning(f"Job {job_id}: Error processing track {i+1}: {str(e)}")
                continue

        # Marcar como completado
        job.status = Job.Status.COMPLETED
        job.current_track = ""
        job.save()

        logger.info(f"Job {job_id}: Completed successfully with {job.completed_tracks} tracks")

    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found")
    except Exception as e:
        logger.exception(f"Job {job_id}: Fatal error")
        try:
            job = Job.objects.get(id=job_id)
            job.status = Job.Status.FAILED
            job.error_message = str(e)
            job.save()
        except Job.DoesNotExist:
            pass


def start_job_async(job_id: str):
    """Inicia el procesamiento de un job en un thread separado"""
    thread = threading.Thread(target=process_job, args=(job_id,), daemon=True)
    thread.start()
