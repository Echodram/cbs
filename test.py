import requests
from icecream import ic

def fetch_json(url):
    try:
        # Make the GET request to the specified URL
        response = requests.get(url)
        
        # Check if the response status code is OK (200)
        if response.status_code == 200:
            # Return the JSON content
            return response.json()
        else:
            return {"error": f"Failed to fetch data, status code: {response.status_code}"}
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Specify the domain you want to request
    domain = "http://mardoche.pythonanywhere.com/blogs/"  # Replace with your target URL
    json_data = fetch_json(domain)
    
    ic(json_data)