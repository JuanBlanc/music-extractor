# Generated manually

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('url', models.URLField(max_length=500)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('processing', 'Procesando'), ('completed', 'Completado'), ('failed', 'Fallido')], default='pending', max_length=20)),
                ('total_tracks', models.IntegerField(default=0)),
                ('completed_tracks', models.IntegerField(default=0)),
                ('current_track', models.CharField(blank=True, max_length=255)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Track',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('file_path', models.CharField(max_length=500)),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('source_url', models.URLField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracks', to='extractor.job')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
