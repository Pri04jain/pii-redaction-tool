"""Test Flask upload endpoint"""
import requests

print("Testing Flask upload endpoint...")
print("="*60)

url = "http://localhost:5000/upload"
files = {'file': open('tests/test_data/part_3.docx', 'rb')}
data = {'mode': 'hybrid'}

print("Uploading part_3.docx (UNSEEN data)...")
try:
    response = requests.post(url, files=files, data=data, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS!")
        print(f"Total Redactions: {result.get('total_redactions')}")
        print(f"Stats: {result.get('stats')}")
        print(f"Output File: {result.get('filename')}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"\n❌ Exception: {e}")

files['file'].close()
