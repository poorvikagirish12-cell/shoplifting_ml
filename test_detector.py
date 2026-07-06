import os
import glob
import json
from detector import ShopliftingDetector

# Default paths
DATASET_TEST_DIR = r"C:\chrome downloads\shoplifting.v1i.yolov8\test\images"
OUTPUT_DIR = "debug_output"

def main():
    print("====================================================")
    print("Testing Shoplifting Detector Prototype")
    print("====================================================\n")

    # Initialize the detector
    detector = ShopliftingDetector()

    # Search for images to test
    test_images = []
    if os.path.exists(DATASET_TEST_DIR):
        print(f"Scanning dataset test folder: {DATASET_TEST_DIR}")
        # Find all jpg, jpeg, png files
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            test_images.extend(glob.glob(os.path.join(DATASET_TEST_DIR, ext)))
    else:
        print(f"Dataset test directory not found: {DATASET_TEST_DIR}")
        print("Please place a test image in this directory or run with standard arguments.")

    # Select the first 3 images if available
    selected_images = test_images[:3]
    
    if not selected_images:
        print("\nNo test images found. Please run the script and specify an image using:")
        print("python test_detector.py --image <path_to_image>")
        return

    print(f"\nFound {len(test_images)} test images. Selecting {len(selected_images)} for prototype testing:\n")

    for i, img_path in enumerate(selected_images, 1):
        print(f"[{i}/{len(selected_images)}] Processing: {os.path.basename(img_path)}")
        try:
            result = detector.detect_shoplifting(img_path, output_dir=OUTPUT_DIR)
            
            # Print short summary
            print(f"  - Suspicious: {result['suspicious']}")
            print(f"  - Total Objects Detected: {len(result['detections'])}")
            print(f"  - Annotated Output: {result['annotated_image_path']}")
            
            # Show a few detections
            top_detections = result['detections'][:5]
            if top_detections:
                print("  - Sample Detections:")
                for d in top_detections:
                    print(f"    * {d['class']} ({d['confidence']:.2f})")
            print("-" * 50)
            
        except Exception as e:
            print(f"  - Error processing image: {e}")
            print("-" * 50)

    print(f"\nAll tests completed. Output files are saved in the './{OUTPUT_DIR}' directory.")
    print("====================================================")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Shoplifting Detector")
    parser.add_argument("--image", type=str, default=None, help="Optionally test a specific image path")
    args = parser.parse_args()

    if args.image:
        # Test specific image
        detector = ShopliftingDetector()
        try:
            result = detector.detect_shoplifting(args.image, output_dir=OUTPUT_DIR)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error testing image {args.image}: {e}")
    else:
        # Run default test suite on dataset images
        main()
