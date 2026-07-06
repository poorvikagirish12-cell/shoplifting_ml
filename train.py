import os
import torch
from ultralytics import YOLO

def main():
    print("====================================================")
    print("Shoplifting Model Training Script")
    print("====================================================\n")

    # Check device
    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device} ({'GPU' if device == '0' else 'CPU'})")

    # Path to dataset configuration
    data_yaml_path = r"C:\chrome downloads\shoplifting.v1i.yolov8\data.yaml"
    if not os.path.exists(data_yaml_path):
        print(f"Error: Dataset data.yaml not found at {data_yaml_path}")
        return

    # Load a pre-trained YOLOv8 nano model
    print("Loading pre-trained YOLOv8 nano model...")
    model = YOLO("yolov8n.pt")

    # Train the model
    print("\nStarting training (fine-tuning)...")
    results = model.train(
        data=data_yaml_path,
        epochs=50,         # Run 50 epochs for high-accuracy custom model training
        imgsz=640,         # Image size
        device=device,     # CUDA GPU or CPU
        workers=2,         # Number of worker threads for data loading
        project="shoplifting_model",
        name="yolov8_shoplifting"
    )

    print("\nTraining completed!")
    
    # Locate the best weights
    best_weights = os.path.join("shoplifting_model", "yolov8_shoplifting", "weights", "best.pt")
    if os.path.exists(best_weights):
        print(f"Best weights saved to: {os.path.abspath(best_weights)}")
        
        # Copy to the root directory as best.pt so detector.py loads it automatically
        import shutil
        shutil.copy(best_weights, "best.pt")
        print("Copied best weights to './best.pt' for automatic detection fallback.")
    else:
        print("Could not find the weights file. Please check the shoplifting_model/ directory.")

if __name__ == "__main__":
    main()
