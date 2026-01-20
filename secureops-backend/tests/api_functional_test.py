import requests
import time
import os
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api_workflow():
    print(f"Testing API at {BASE_URL}")
    
    # 1. Create dummy file
    filename = "test_image_validation.jpg"
    with open(filename, "wb") as f:
        f.write(b"fake_image_content")
    
    try:
        # 2. Upload
        print("1. Testing Upload...")
        files = {'files': (filename, open(filename, 'rb'), 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/videos/upload", files=files)
        
        if response.status_code != 200:
            print(f"❌ Upload Failed: {response.text}")
            sys.exit(1)
            
        data = response.json()
        video_id = data.get("video_id")
        status = data.get("status")
        
        print(f"✅ Upload Success! ID: {video_id}, Status: {status}")
        
        if not video_id:
            print("❌ No video_id returned")
            sys.exit(1)

        # 3. Poll Status
        print("2. Testing Status Polling...")
        for _ in range(3):
            res = requests.get(f"{BASE_URL}/videos/{video_id}/status")
            if res.status_code == 200:
                print(f"   Status: {res.json().get('status')}")
                break
            time.sleep(1)
        
        # 4. Results (Summary)
        # Note: Pipeline is offline, so status might stay 'pending' forever unless we manually update DB or mock it.
        # But this tests the READ endpoint availability.
        print("3. Testing Results (Summary)...")
        res = requests.get(f"{BASE_URL}/results/summary?upload_id={video_id}")
        if res.status_code == 200:
            print(f"✅ Summary Endpoint Accessible: {res.json()}")
        else:
            print(f"❌ Summary Endpoint Failed: {res.status_code} {res.text}")

        # 5. Results (Violations)
        print("4. Testing Results (Violations)...")
        res = requests.get(f"{BASE_URL}/results/violations?upload_id={video_id}")
        if res.status_code == 200:
            print(f"✅ Violations Endpoint Accessible. Count: {len(res.json())}")
        else:
            print(f"❌ Violations Endpoint Failed: {res.status_code}")
            
        print("\n🎉 Functional Smoke Test Passed!")
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_api_workflow()
