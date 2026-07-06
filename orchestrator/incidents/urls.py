from django.urls import path
from .views import IncidentListView, ProcessFrameView

urlpatterns = [
    path('incidents/', IncidentListView.as_view(), name='incident-list'),
    path('process_frame/', ProcessFrameView.as_view(), name='process-frame'),
]
