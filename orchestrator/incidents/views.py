import os
import requests
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import IncidentReport
from .serializers import IncidentReportSerializer

class IncidentListView(generics.ListAPIView):
    """
    Returns a list of all recorded shoplifting incidents, newest first.
    """
    queryset = IncidentReport.objects.all().order_by('-timestamp')
    serializer_class = IncidentReportSerializer

class ProcessFrameView(APIView):
    """
    Receives a video frame from the frontend, sends it to the FastAPI ML engine,
    and logs an incident in the database if theft is detected.
    """
    def post(self, request, *args, **kwargs):
        frame = request.FILES.get('frame')
        if not frame:
            return Response({"error": "No frame provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        # The URL where our FastAPI ML engine is running
        base_fastapi_url = os.getenv("FASTAPI_URL", "http://127.0.0.1:8888").rstrip('/')
        fastapi_url = f"{base_fastapi_url}/analyze"
        
        try:
            # Forward the exact image bytes to the ML engine
            files = {'file': (frame.name, frame.read(), frame.content_type)}
            response = requests.post(fastapi_url, files=files)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if the ML engine flagged this as a shoplifting incident
                if data.get("theft_detected", False):
                    annotated_path = data.get("annotated_image_path", "")
                    
                    # Prepend the FASTAPI_URL to the image path if it's a relative path
                    if annotated_path.startswith("/images/"):
                        full_image_url = f"{base_fastapi_url}{annotated_path}"
                    else:
                        full_image_url = annotated_path
                    
                    # Create and save a new incident record in SQLite/PostgreSQL
                    incident = IncidentReport.objects.create(
                        camera_id=request.data.get("camera_id", "CAM-01"),
                        confidence_score=data.get("confidence", 0.0),
                        image_url=full_image_url,
                        theft_detected=True
                    )
                    
                    # Step 5: Push WebSocket message to frontend instantly
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "security_alerts",
                        {
                            "type": "new_alert",
                            "message": {
                                "incident_id": incident.id,
                                "camera_id": incident.camera_id,
                                "confidence_score": incident.confidence_score,
                                "timestamp": incident.timestamp.isoformat(),
                            }
                        }
                    )
                    
                    return Response({
                        "status": "incident_recorded", 
                        "incident_id": incident.id,
                        "data": data
                    }, status=status.HTTP_201_CREATED)
                
                # If no theft was detected, just return OK without saving to DB
                return Response({"status": "clean", "data": data}, status=status.HTTP_200_OK)
            else:
                return Response({"error": f"FastAPI engine returned an error: {response.status_code} - {response.text}"}, status=status.HTTP_502_BAD_GATEWAY)
                
        except requests.exceptions.ConnectionError:
            return Response({"error": "FastAPI ML Engine is offline"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
