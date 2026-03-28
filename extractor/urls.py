from django.urls import path
from .views import ExtractAudioView, JobDetailView, JobListView

urlpatterns = [
    path('extract-audio/', ExtractAudioView.as_view(), name='extract-audio'),
    path('jobs/', JobListView.as_view(), name='job-list'),
    path('jobs/<uuid:job_id>/', JobDetailView.as_view(), name='job-detail'),
]
