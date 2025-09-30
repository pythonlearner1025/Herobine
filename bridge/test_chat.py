import requests
import time
import base64
from PIL import Image
import io

# Wait for bridge to start
time.sleep(2)

# Test chat endpoint
print("Testing /chat/instructions...")
response = requests.post('http://localhost:3333/chat/instructions')
print(f"Chat: {response.status_code} - {response.json()}")

# Test screenshot endpoint  
print("\nTesting /screenshot...")
response = requests.post('http://localhost:3333/screenshot', timeout=10)
data = response.json()
print(f"Screenshot: success={data.get('success')}, width={data.get('width')}, height={data.get('height')}")

if data.get('success') and data.get('image'):
    img_data = base64.b64decode(data['image'])
    img = Image.open(io.BytesIO(img_data))
    print(f"Image size: {img.size}, mode: {img.mode}")
else:
    print(f"Screenshot failed: {data.get('error')}")
