import requests
import sys
import json

def test_auth(api_url, api_key=None, pdf_file=None):
    """
    Test the API's authentication requirements
    
    Args:
        api_url: Base URL of the API (e.g., http://localhost:8080)
        api_key: API key to test with (or None to test without a key)
        pdf_file: Optional PDF file path to test with
    """
    headers = {}
    if api_key:
        headers['x-api-key'] = api_key
    
    print(f"\n--- Testing API Authentication ---")
    print(f"URL: {api_url}")
    print(f"API Key: {'None' if api_key is None else api_key}")
    
    # First test the auth-info endpoint
    try:
        info_response = requests.get(f"{api_url}/auth-info")
        if info_response.status_code == 200:
            print("\nAuth Info Response:")
            print(json.dumps(info_response.json(), indent=2))
        else:
            print(f"\nAuth Info Request Failed: {info_response.status_code}")
            print(info_response.text)
    except Exception as e:
        print(f"Error connecting to /auth-info: {str(e)}")
    
    # Then test the unstructured endpoint
    if pdf_file:
        try:
            print(f"\nTesting /unstructured endpoint with file: {pdf_file}")
            
            with open(pdf_file, 'rb') as f:
                files = {'file': (pdf_file.split('/')[-1], f, 'application/pdf')}
                response = requests.post(f"{api_url}/unstructured", headers=headers, files=files)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Received {len(data)} document elements.")
                if len(data) > 0:
                    print(f"\nSample element:")
                    print(json.dumps(data[0], indent=2))
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Error testing /unstructured endpoint: {str(e)}")
    else:
        print("\nSkipping /unstructured endpoint test (no PDF file provided)")
    
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auth_test.py <api_url> [api_key] [pdf_file]")
        print("Example: python auth_test.py http://localhost:8080 default-dev-key test.pdf")
        print("Example (no key): python auth_test.py http://localhost:8080 '' test.pdf")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    api_key = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '' else None
    pdf_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    test_auth(api_url, api_key, pdf_file)