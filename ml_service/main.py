from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os

# We need to import the detector we built
# Note: Since we moved detector.py to ml_service, we can import it directly
from detector import ShopliftingDetector

app = FastAPI(title="Shoplifting ML Engine", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the detector once at startup to keep inference fast
MODEL_PATH = os.getenv("MODEL_PATH", "best.pt")
detector = ShopliftingDetector(MODEL_PATH)

UPLOAD_DIR = "temp_frames"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("debug_output", exist_ok=True)
app.mount("/images", StaticFiles(directory="debug_output"), name="images")

@app.post("/analyze")
async def analyze_frame(file: UploadFile = File(...)):
    """
    Receives an image file, runs YOLO inference to detect shoplifting,
    and returns a JSON payload with detections.
    """
    # Save uploaded file temporarily
    temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Run inference using the pre-loaded detector
        result = detector.detect_shoplifting(temp_file_path, output_dir="debug_output")
        
        # Calculate overall confidence (highest confidence detection)
        # If no detections, confidence is 0.0
        max_conf = max([d["confidence"] for d in result["detections"]]) if result["detections"] else 0.0
        
        annotated_filename = os.path.basename(result["annotated_image_path"])
        
        # Format response to match the requested execution plan
        return JSONResponse(content={
            "theft_detected": result["suspicious"],
            "confidence": max_conf,
            "bounding_box": result["detections"],  # Sending all detections
            "annotated_image_path": f"/images/{annotated_filename}"
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        # Clean up the raw temp file to save space (keep the annotated one)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8001 (so it doesn't conflict with Django on 8000)
    uvicorn.run(app, host="127.0.0.1", port=8888)
