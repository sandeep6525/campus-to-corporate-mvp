import requests

url = "http://localhost:8000/api/auth/register"
data = {
    "email": "testlearner@example.com",
    "password": "password123",
    "role": "Learner"
}
try:
    response = requests.post(url, json=data)
    print("Status:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", str(e))
