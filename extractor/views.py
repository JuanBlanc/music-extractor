import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Job, Track
from .services import start_job_async


logger = logging.getLogger(__name__)


class ExtractAudioView(APIView):
    """
    POST: Crear un nuevo trabajo de extraccion
    Acepta videos individuales o playlists
    """

    def post(self, request):
        video_url = request.data.get("url")
        if not video_url:
            logger.warning("POST /extract-audio/ without url")
            return Response(
                {"error": "Falta la URL"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info("Creating extraction job", extra={"url": video_url})

        # Crear job
        job = Job.objects.create(url=video_url)

        # Iniciar procesamiento en background
        start_job_async(str(job.id))

        return Response(
            {
                "job_id": str(job.id),
                "status": job.status,
                "message": "Trabajo creado. Usa /jobs/{job_id}/ para ver el progreso.",
            },
            status=status.HTTP_202_ACCEPTED
        )


class JobDetailView(APIView):
    """
    GET: Obtener estado y progreso de un trabajo
    DELETE: Cancelar/eliminar un trabajo
    """

    def get(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Trabajo no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        tracks_data = []
        if job.status == Job.Status.COMPLETED or job.completed_tracks > 0:
            tracks_data = [
                {
                    "title": track.title,
                    "file_url": f"{settings.MEDIA_URL}{track.file_path}",
                    "duration": track.duration,
                }
                for track in job.tracks.all()
            ]

        return Response({
            "job_id": str(job.id),
            "url": job.url,
            "status": job.status,
            "progress": job.progress,
            "total_tracks": job.total_tracks,
            "completed_tracks": job.completed_tracks,
            "current_track": job.current_track,
            "error_message": job.error_message,
            "tracks": tracks_data,
            "created_at": job.created_at.isoformat(),
        })

    def delete(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
            job.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Job.DoesNotExist:
            return Response(
                {"error": "Trabajo no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )


class JobListView(APIView):
    """
    GET: Listar todos los trabajos
    """

    def get(self, request):
        jobs = Job.objects.all()[:50]  # Ultimos 50 trabajos

        return Response({
            "jobs": [
                {
                    "job_id": str(job.id),
                    "url": job.url,
                    "status": job.status,
                    "progress": job.progress,
                    "total_tracks": job.total_tracks,
                    "completed_tracks": job.completed_tracks,
                    "created_at": job.created_at.isoformat(),
                }
                for job in jobs
            ]
        })
