from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('manager', 'Manager'), ('guard', 'Guard')], default='guard')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class IncidentReport(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    camera_id = models.CharField(max_length=100, default='CAM-01')
    confidence_score = models.FloatField()
    image_url = models.CharField(max_length=500)
    theft_detected = models.BooleanField(default=True)

    def __str__(self):
        return f"Incident at {self.timestamp} - Conf: {self.confidence_score:.2f}"
