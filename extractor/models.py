import uuid
from django.db import models


class Job(models.Model):
    """Trabajo de extraccion de audio"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        PROCESSING = 'processing', 'Procesando'
        COMPLETED = 'completed', 'Completado'
        FAILED = 'failed', 'Fallido'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_tracks = models.IntegerField(default=0)
    completed_tracks = models.IntegerField(default=0)
    current_track = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def progress(self):
        if self.total_tracks == 0:
            return 0
        return int((self.completed_tracks / self.total_tracks) * 100)


class Track(models.Model):
    """Pista de audio extraida"""

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='tracks')
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    duration = models.IntegerField(null=True, blank=True)  # segundos
    source_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
