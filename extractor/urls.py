from django.urls import path
from .views import ExtractAudioView

urlpatterns = [
    path('extract-audio/', ExtractAudioView.as_view(), name='extract-audio'),
]