import requests
import json
import os
import warnings
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from main import app

test_name = "test"
test_username = "testuser"
test_password = "userpass"
test_resume = "testuser"
test_user_type = "user"

client = TestClient(app)

#first generate token for test user
payload = {'name': test_name, 'username': test_username, 'password': test_password, 'user_type': test_user_type, 'resume_filename': test_resume}
response = client.post("/user/create", json=payload)    #first sign up the test user
response2 = client.post("/login", data=payload)     #next login to get the access token
json_data = json.loads(response2.text)
ACCESS_TOKEN = json_data["access_token"]    #capture test user's access token
header = {}
header['Authorization'] = f"Bearer {ACCESS_TOKEN}"

#unit test cases for every endpoint of the API

#Router: authenticate
def test_incorrect_login():
    payload={'username': 'nouser', 'password': 'incorrectpass'}
    response = client.post("/login", data=payload)
    assert response.status_code == 404

#Router: user, Endpoint 2
def test_incorrect_password_change():
    pass_payload = {'password': 'newpass'}
    response = client.patch("/user/update?username=doesnotexist", json=pass_payload)
    assert response.status_code == 404  #404 since the user 'doesnotexist' does not exist

#Router: user, Endpoint 3
def test_user_details_admin():
    response = client.get("/user/details?username=admin", headers=header)   #username 'admin' already exists
    assert response.status_code == 200
    json_resp = json.loads(response.text)
    assert json_resp == "admin"  #single resume file for each user which is named as resume_username.docx

#Router: user, Endpoint 3
def test_user_details_incorrect():
    response = client.get("/user/details?username=doesnotexist", headers=header)
    assert response.status_code == 404  #404 since the user 'doesnotexist' does not exist

#Router: user, Endpoint 4
def test_check_resume():
    response = client.get("/user/checkresume?username=testuser", headers=header)
    assert response.status_code == 200
    json_resp = json.loads(response.text)
    assert json_resp == "resume_testuser.docx"  #single resume file for each user which is named as resume_username.docx

#Router: user, Endpoint 4
def test_check_resume_incorrect():
    response = client.get("/user/checkresume?username=nouser", headers=header)
    assert response.status_code == 404  #resume not found for user 'nouser' since such a user does not exist

#Router: model, Endpoint 1
def test_model_as_a_service():
    job_title = "Data Analyst"
    response = client.get(f"/model/relevantjobs?username=testuser&jobtitle={job_title}", headers=header)
    assert response.status_code == 200  #since this dataset for the testuser & Data Engineer jobs is available
    json_resp = json.loads(response.text)
    assert len(json_resp['link']) == 3  #3 job links are returned
    assert len(json_resp['company']) == 3  #3 companies for each of 3 jobs are returned

#Router: model, Endpoint 1
def test_model_as_a_service_incorrect():
    job_title = "Data Scientist"
    response = client.get(f"/model/relevantjobs?username=testuser&jobtitle={job_title}", headers=header)
    assert response.status_code == 404  #since this dataset for the testuser & Data Scientist jobs is NOT available

#Router: logs, Endpoint 1
def test_logs_admin():
    response = client.get(f"/logs/admin?username=admin", headers=header)
    assert response.status_code == 200  #since this dataset for the testuser & Data Scientist jobs is NOT available

#Router: logs, Endpoint 1
def test_logs_user():
    response = client.get(f"/logs/admin?username=tesuser", headers=header)
    assert response.status_code == 400  #since this logs dashboard access is only available for user 'admin' 