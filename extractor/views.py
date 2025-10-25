import logging
import os
import tempfile
import subprocess
import json
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


logger = logging.getLogger(__name__)


class ExtractAudioView(APIView):
    def post(self, request):
        video_url = request.data.get("url")
        if not video_url:
            logger.warning("POST /extract-audio/ without url")
            return Response({"error": "Falta la URL"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info("Starting audio extraction", extra={"url": video_url})

        try:
            metadata_process = subprocess.run(
                [
                    "yt-dlp",
                    "--no-warnings",
                    "--skip-download",
                    "--print-json",
                    video_url,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug(
                "yt-dlp metadata stdout: %s",
                metadata_process.stdout.strip(),
            )

            metadata = json.loads(metadata_process.stdout)
            title = metadata.get("title", "audio").replace("/", "-").replace("\\", "-")
            logger.info("Metadata retrieved", extra={"title": title})

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, f"{title}.mp3")
                logger.debug("Generated temporary path", extra={"path": output_path})

                download_process = subprocess.run(
                    [
                        "yt-dlp",
                        "-x",
                        "--audio-format",
                        "mp3",
                        "--audio-quality",
                        "0",
                        "-o",
                        output_path,
                        video_url,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if download_process.stdout:
                    logger.debug(
                        "yt-dlp download stdout: %s",
                        download_process.stdout.strip(),
                    )
                if download_process.stderr:
                    logger.debug(
                        "yt-dlp download stderr: %s",
                        download_process.stderr.strip(),
                    )

                with open(output_path, "rb") as f:
                    file_content = f.read()

                saved_path = default_storage.save(f"{title}.mp3", ContentFile(file_content))
                file_url = settings.MEDIA_URL + saved_path
                logger.info("File stored", extra={"saved_path": saved_path})

            return Response({"file_url": file_url}, status=status.HTTP_200_OK)

        except subprocess.CalledProcessError as exc:
            logger.error(
                "yt-dlp command failed",
                extra={
                    "cmd": exc.cmd,
                    "returncode": exc.returncode,
                    "stdout": (exc.stdout or "").strip(),
                    "stderr": (exc.stderr or "").strip(),
                },
            )
            return Response({"error": "Error procesando el video"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception:
            logger.exception("Unexpected error extracting audio", extra={"url": video_url})
            return Response({"error": "Error procesando el video"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
