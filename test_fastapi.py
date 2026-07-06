import requests
import json
import os

API_URL = "http://127.0.0.1:8888/analyze"
# Grab one of the test images we copied to the artifacts folder earlier
TEST_IMAGE = r"C:\chrome downloads\shoplifting.v1i.yolov8\test\images\close-up-the-consumer-thiefs-hands-putting-the-new-gadget-in-the-pocket-in-the-store-2AETMAX_jpg.rf.5723bc8665cbb22265aab1c8a37ef2e3.jpg"

def main():
    print(f"Testing FastAPI Shoplifting Engine at {API_URL}...")
    
    if not os.path.exists(TEST_IMAGE):
        print(f"Error: Test image not found at {TEST_IMAGE}")
        return

    try:
        with open(TEST_IMAGE, "rb") as image_file:
            files = {"file": ("test_image.jpg", image_file, "image/jpeg")}
            
            print("Sending POST request with image...")
            response = requests.post(API_URL, files=files)
            
            if response.status_code == 200:
                print("Success! Received JSON response:\n")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"Failed with status code {response.status_code}")
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print(f"Connection Error: Is the FastAPI server running on {API_URL}?")

if __name__ == "__main__":
    main()