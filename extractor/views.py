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


class ExtractAudioView(APIView):
    def post(self, request):
        video_url = request.data.get("url")
        if not video_url:
            return Response({"error": "Falta la URL"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Obtener metadatos del vídeo en JSON
            result = subprocess.run(
                ["yt-dlp", "--no-warnings", "--skip-download",
                    "--print-json", video_url],
                capture_output=True,
                text=True,
                check=True
            )
            metadata = json.loads(result.stdout)
            title = metadata.get("title", "audio").replace(
                "/", "-").replace("\\", "-")

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, f"{title}.mp3")

                subprocess.run([
                    "yt-dlp",
                    "-x",
                    "--audio-format", "mp3",
                    "--audio-quality", "0",  # 0 = mejor calidad, ~320 kbps
                    "-o", output_path,
                    video_url
                ], check=True)

                with open(output_path, "rb") as f:
                    file_content = f.read()

                saved_path = default_storage.save(
                    f"{title}.mp3", ContentFile(file_content))
                file_url = settings.MEDIA_URL + saved_path

            return Response({"file_url": file_url}, status=status.HTTP_200_OK)

        except subprocess.CalledProcessError:
            return Response({"error": "Error procesando el video"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
