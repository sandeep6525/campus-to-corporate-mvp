import requests

r1 = requests.post("http://127.0.0.1:8000/api/auth/login", json={"email": "testlearner01@example.com", "password": "abc"})
print(r1.status_code)
print(r1.text)

r2 = requests.post("http://127.0.0.1:8000/api/auth/login", json={"email": "testlearner01@example.com", "password": "abc"})
print(r2.status_code)
print(r2.text)
