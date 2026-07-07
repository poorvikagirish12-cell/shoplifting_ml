import os
import cv2
from ultralytics import YOLO

# Default paths
DEFAULT_MODEL_NAME = "yolov8n.pt"  # Fallback pre-trained COCO model
CUSTOM_MODEL_PATH = "best.pt"      # Place custom model weights here once trained

class ShopliftingDetector:
    def __init__(self, model_path=None):
        """
        Initializes the detector. It will try to load the model in this order:
        1. Explicitly provided model_path.
        2. Local 'best.pt' (custom fine-tuned model).
        3. Pre-trained 'yolov8n.pt' (standard COCO model).
        """
        self.is_custom_model = False
        
        if model_path and os.path.exists(model_path):
            print(f"Loading user-specified model: {model_path}")
            self.model = YOLO(model_path)
            self.is_custom_model = self._check_if_custom()
        elif os.path.exists(CUSTOM_MODEL_PATH):
            print(f"Loading custom fine-tuned model: {CUSTOM_MODEL_PATH}")
            self.model = YOLO(CUSTOM_MODEL_PATH)
            self.is_custom_model = self._check_if_custom()
        else:
            print(f"Custom model not found. Falling back to pre-trained COCO: {DEFAULT_MODEL_NAME}")
            self.model = YOLO(DEFAULT_MODEL_NAME)
            self.is_custom_model = False

        print(f"Model classes: {list(self.model.names.values())}")

    def _check_if_custom(self):
        """
        Checks if the loaded model is fine-tuned on the shoplifting dataset
        by inspecting class names.
        """
        names = list(self.model.names.values())
        return "shoplifting" in names or "picking" in names

    def detect_shoplifting(self, image_path: str, output_dir: str = "debug_output") -> dict:
        """
        Runs inference on an image and returns a dict with predictions
        conforming to the inference contract. Also saves an annotated debug image.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")

        # Run inference with reduced image size to prevent OOM crashes on free tier VMs
        results = self.model(image_path, imgsz=320)[0]
        
        # Load image for drawing
        image = cv2.imread(image_path)
        h, w, _ = image.shape

        detections = []
        suspicious = False
        
        # We'll use these lists for the COCO heuristic fallback
        persons = []
        items = []
        bags = []

        # Target items that might be shoplifted in standard COCO dataset
        coco_target_items = {"bottle", "cup", "banana", "apple", "sandwich", "orange", 
                             "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
                             "cell phone", "book", "scissors", "teddy bear", "hair drier", "toothbrush"}
        coco_bag_items = {"backpack", "handbag", "suitcase"}

        for box in results.boxes:
            coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            conf = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]

            x1, y1, x2, y2 = map(int, coords)

            detections.append({
                "class": class_name,
                "confidence": conf,
                "box": [x1, y1, x2, y2]
            })

            # Check for suspicious behavior based on model type
            if self.is_custom_model:
                # Custom model has direct class for 'shoplifting' or 'picking'
                if class_name in ["shoplifting", "picking"] and conf > 0.4:
                    suspicious = True
                    # Draw red box for suspicious detection
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(image, f"SUSPICIOUS: {class_name} ({conf:.2f})", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    # Draw green box for normal behavior
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(image, f"{class_name} ({conf:.2f})", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            else:
                # Fallback COCO heuristic: check relationships between detections
                if class_name == "person":
                    persons.append((x1, y1, x2, y2))
                elif class_name in coco_target_items:
                    items.append((x1, y1, x2, y2, class_name))
                elif class_name in coco_bag_items:
                    bags.append((x1, y1, x2, y2, class_name))

                # Draw default boxes for COCO model
                cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(image, f"{class_name} ({conf:.2f})", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # Apply COCO heuristic if using fallback model
        if not self.is_custom_model and persons:
            # Hackathon demo heuristic:
            # If a person is detected, AND a target item is detected, AND a bag is detected
            # we consider it "suspicious" for demonstration purposes without requiring strict bounding box overlaps.
            if items and bags:
                suspicious = True
                # Highlight the suspicious interaction
                cv2.putText(image, "WARNING: Suspicious Interaction", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save annotated image
        base_name = os.path.basename(image_path)
        annotated_path = os.path.join(output_dir, f"annotated_{base_name}")
        cv2.imwrite(annotated_path, image)

        return {
            "suspicious": suspicious,
            "detections": detections,
            "annotated_image_path": os.path.abspath(annotated_path)
        }

if __name__ == "__main__":
    # Test execution when run directly
    import argparse
    parser = argparse.ArgumentParser(description="Test Shoplifting Detector Prototype")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--model", type=str, default=None, help="Path to custom model weights")
    args = parser.parse_args()

    try:
        detector = ShopliftingDetector(args.model)
        result = detector.detect_shoplifting(args.image)
        print("\n--- Detection Results ---")
        print(f"Suspicious: {result['suspicious']}")
        print(f"Annotated Image Saved To: {result['annotated_image_path']}")
        print("Detections:")
        for det in result['detections']:
            print(f"  - {det['class']} (Conf: {det['confidence']:.2f}) at {det['box']}")
    except Exception as e:
        print(f"Error running detector: {e}")
