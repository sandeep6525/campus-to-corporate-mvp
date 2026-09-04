import requests

r = requests.get('http://127.0.0.1:8000/api/learner/certifications', headers={'x-user-id': '1'})
print(r.json())
