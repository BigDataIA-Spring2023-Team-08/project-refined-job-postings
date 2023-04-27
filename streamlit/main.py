import streamlit as st
import requests
import json
import time
import os
from pydotenvs import load_env
import boto3

#load local environment
load_env()

# Define API URL
API_URL = os.environ.get('FASTAPI_URL')
airflow_url = os.environ.get('AIRFLOW_URL')
airflow_credentials = os.environ.get('AIRFLOW_CREDENTIALS')

#authenticate S3 client for logging with your user credentials that are stored in your .env config file
clientLogs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                        )

# Define function to check if user is logged in
def is_authenticated():
    if 'if_logged' not in st.session_state:
        st.session_state['if_logged'] = False
        st.session_state['access_token'] = ''
        st.session_state['username'] = ''

    return st.session_state['if_logged']

# Define function to handle logout
def logout():

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "ui",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "User logged out"
                    }
                ]
        )

    st.session_state['if_logged'] = False
    st.session_state['access_token'] = None
    st.session_state['username'] = None
    st.experimental_rerun()

def user_upload_resume(header):
    st.write("Upload your resume here:")
    uploaded_file = st.file_uploader("Choose a file", type="docx")
    if uploaded_file is not None:
        files = {"file": uploaded_file}

        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "ui",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/uploadfile invoked from UI"
                    }
                ]
        )

        response = requests.request("POST", f"{API_URL}/user/uploadfile?username={st.session_state['username']}", files=files, headers=header)
        if response.status_code == 200:
            #RESUMES[st.session_state["username"]] = uploaded_file.name   ##################
            with st.spinner("Wait.."):
                st.success("Resume uploaded successfully!")   #success message
            #return True
            #st.experimental_rerun()
        elif response.status_code == 401:   #when token is not authorized
            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/uploadfile Response: 401 Unauthorized access"
                    }
                ]
            )
            st.error("Session token expired, please login again")   #display error
            st.stop()
        else:# response.status_code == 400:
            st.warning("Unable to perform operation, please try again file, please try again")     #user does not exist
            #return False

# Define function to handle resume upload
# def upload_resume():
#     uploaded_file = st.file_uploader("Choose a file")
#     if uploaded_file is not None:
#         with st.spinner("Uploading..."):
#             try:
#                 response = requests.post(
#                     f"{API_URL}/upload_resume",
#                     files={"resume": uploaded_file},
#                     headers={"Authorization": f"Bearer {st.session_state['access_token']}"}
#                 )
#                 clientLogs.put_log_events(      #logging to AWS CloudWatch logs
#                             logGroupName = "project-refined-job-postings",
#                             logStreamName = "ui",
#                             logEvents = [
#                                 {
#                                 'timestamp' : int(time.time() * 1e3),
#                                 'message' : "User uploaded resume"
#                                 }
#                             ]
#                         )
#             except:
#                 st.error("Service unavailable, please try again later") #in case the API is not running
#                 st.stop()   #stop the application
#             if response.status_code == 200:
#                 st.success("Resume uploaded successfully")
#                 st.experimental_rerun()
#             else:
#                 st.error("Failed to upload resume. Please try again.")

# Define function to handle job recommendations
def get_job_recommendations():
    st.write('done')
    #pass  # Replace with your own function for job recommendations

# Define app layout
def app():

    st.set_page_config(page_title="Job Recommender App", page_icon=":guardsman:", layout="wide")
    st.title("Job Recommender App")

    RESUMES = {}

    # Check if user is logged in
    if not is_authenticated():

        # Render login/signup form
        login_or_signup = st.selectbox("Please select an option", ["Login", "Signup", "Forgot Password?"])

        if login_or_signup == "Login":
            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "ui",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "Login page opened"
                    }
                ]
            )
            st.write("Enter your credentials to login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if username == '' or password == '':
                    st.warning("Please enter both username and password.")
                else:
                    with st.spinner("Wait.."):
                        payload = {'username': username, 'password': password}
                        try:
                            response = requests.request("POST", f"{API_URL}/login", data=payload)
                            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                logGroupName = "project-refined-job-postings",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "Login page: User called /login endpoint to validate login"
                                    }
                                ]
                            )
                            #print(response.status_code)
                        except:
                            st.error("Service unavailable, please try again later") #in case the API is not running
                            st.stop()   #stop the application
                    if response.status_code == 200:
                        json_data = json.loads(response.text)
                        st.session_state['if_logged'] = True
                        st.session_state['access_token'] = json_data['access_token']
                        st.session_state['username'] = username
                        st.success("Login successful")
                        st.experimental_rerun()
                    else:
                        st.error("Incorrect username or password.")

        elif login_or_signup == "Signup":
            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                logGroupName = "project-refined-job-postings",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "Signup page opened"
                                    }
                                ]
                            )
            st.write("Create an account to get started")
            name = st.text_input("Name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.button("Signup"):
                if len(password) < 4:
                    st.warning("Password should be of 4 characters minimum")
                elif name == '' or username == '' or password == '' or confirm_password == '':
                    st.warning("Please fill all the fields.")
                elif password != confirm_password:
                    with st.spinner("Wait.."):
                        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                logGroupName = "project-refined-job-postings",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "Signup page: Passwords do not match"
                                    }
                                ]
                            )
                        st.warning("Passwords do not match.")
                else:
                    with st.spinner("Wait.."):
                        try:
                            payload = {'name': name, 'username': username, 'password': password}
                            response = requests.request("POST", f"{API_URL}/user/create", json=payload)
                            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                logGroupName = "project-refined-job-postings",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "User called /user/create endpoint to create a new account"
                                    }
                                ]
                            )
                        except:
                            st.error("Service unavailable, please try again later") #in case the API is not running
                            st.stop()   #stop the application
                    if response.status_code == 200:
                        st.success("Account created successfully")
                    elif response.status_code == 400:
                        st.error("Username already exists, please login")
                    else:
                        st.error("Failed to create account. Please try again.")

        elif login_or_signup=="Forgot Password?":
            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                logGroupName = "project-refined-job-postings",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "Forgot Password page opened"
                                    }
                                ]
                            )
            st.write("Enter your details to reset password")
            username2 = st.text_input("Enter username to reset password for")
            password2 = st.text_input("Enter new password", type="password")
            if st.button("Reset"):
                if username2 == '' or password2 == '':  #sanity check
                    st.warning("Please enter both username and password.")
                elif len(password2) < 4:    #password length check
                    st.warning("Password should be of 4 characters minimum")
                else:
                    with st.spinner("Wait.."):
                        pass_payload = {'password': password2}
                        try:
                            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                logGroupName = "project-refined-job-postings",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "User called /user/update endpoint to create a new account"
                                    }
                                ]
                            )
                            response = requests.request("PATCH", f"{API_URL}/user/update?username={username2}", json=pass_payload)  #call to relevant fastapi endpoint with authorization
                        except:
                            st.error("Service unavailable, please try again later") #in case the API is not running
                            st.stop()   #stop the application
                    if response.status_code == 200:
                        st.success("Reset password successful! Please login")   #success message
                    elif response.status_code == 404:
                        st.warning("User not found, please check username")     #user does not exist
                    else:
                        st.error("Something went wrong, try again later.")
    else:  # User is logged in
    
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "ui",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "User successfully logged in"
                    }
                ]
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col5:
            logout_button = st.button(label='Logout', disabled=False)

        if logout_button:
            # st.session_state['if_logged'] = False
            # st.experimental_rerun()
            logout()

        #st.set_page_config(page_title="Job Recommender App", page_icon=":guardsman:", layout="wide")
        #st.title("Job Recommender App")

        st.header(f"Welcome, {st.session_state['username']}!")
        
        # Check if user already uploaded a resume
        header = {}
        header['Authorization'] = f"Bearer {st.session_state['access_token']}"

        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "ui",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "UI invoked user/checkresume API endpoint"
                    }
                ]
        )
        response = requests.request("GET", f"{API_URL}/user/checkresume?username={st.session_state['username']}", headers=header)
        if response.status_code == 200:
            jobtype = st.selectbox('Select a Job Title:',
                ('--','Data Scientist', 'Data Engineer', 'Data Analyst'))
            
            if jobtype != '--':
                st.write('Job title selected:', jobtype)
                if st.button("Get top job recommendations"):
                    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                            logGroupName = "project-refined-job-postings",
                            logStreamName = "ui",
                            logEvents = [
                                {
                                'timestamp' : int(time.time() * 1e3),
                                'message' : "User invked get job recommendations"
                                }
                            ]
                    )
                    #Todo: Add function to generate job recommendations
                    #call the Airflow API to trigger a DAG run
                    dag_id_prep_dataset = "prepare-dataset-for-user_v1" #DAG id for the adhoc dag already defined on airflow
                    dag_run_id_prep_dataset = "triggered_using_ui_" + str(time.time() * 1e3)    #unique run id for each dag run using current time
                    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                            logGroupName = "project-refined-job-postings",
                            logStreamName = "ui",
                            logEvents = [
                                {
                                'timestamp' : int(time.time() * 1e3),
                                'message' : f"Application trigged Airflow DAG with id: {dag_id_prep_dataset}"
                                }
                            ]
                    )
                    response = requests.post(url=f"{airflow_url}/api/v1/dags/{dag_id_prep_dataset}/dagRuns",
                                            headers={"Authorization": f"Basic {airflow_credentials}"},    #base 64 encoded value of username:password for Airflow instance
                                            json = {
                                                    "dag_run_id": dag_run_id_prep_dataset,
                                                    "conf": {"username": st.session_state['username'], "job_title": jobtype}
                                                    }
                                            #payload data in json
                                        )

                    resp_json_ds = response.json() #get the response json of the API call done
                    #wait until the DAG run finishes
                    with st.spinner('Finding you the top job postings...'):  #waiting for adhoc dag run to finish, might take a minute
                        while(True):    #check status of the DAG run just executed recursively to check when it is successfully completed
                            #call the Airflow API to get the dag run we just executed above
                            #trigger Airflow's adhoc DAG to transcribe this audio file & storing the general questions responses got from OpenAI's ChatGPT API into the processed-text-files folder
                            response_dag_status = requests.get(url=f"{airflow_url}/api/v1/dags/{dag_id_prep_dataset}/dagRuns/{dag_run_id_prep_dataset}",
                                                            headers={"Authorization": f"Basic {airflow_credentials}"},    #base 64 encoded
                                                            )
                            #st.write(response_dag_status.json())
                            resp_json_ds1 = response_dag_status.json() #get the response json
                            if(resp_json_ds1['state'] == 'success'):   #if the 'state' of this dag run is 'success', it has executed
                                clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                        logGroupName = "project-refined-job-postings",
                                        logStreamName = "ui",
                                        logEvents = [
                                            {
                                            'timestamp' : int(time.time() * 1e3),
                                            'message' : f"Airflow DAG with id: {dag_id_prep_dataset} run successfully"
                                            }
                                        ]
                                )
                                break   #break spinner once dag executed
            #st.button("Get relevant jobs!")
            
        elif response.status_code == 404:
            st.warning("No resume uploaded, please upload one")     #user does not exist
            #user_upload_resume(header)
            st.write("Upload your resume here:")
            uploaded_file = st.file_uploader("Choose a file", type="docx")
            if uploaded_file is not None:
                #with st.spinner("Wait.."):
                files = {"file": uploaded_file}
                response = requests.request("POST", f"{API_URL}/user/uploadfile?username={st.session_state['username']}", files=files, headers=header)
                clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                            logGroupName = "project-refined-job-postings",
                            logStreamName = "ui",
                            logEvents = [
                                {
                                'timestamp' : int(time.time() * 1e3),
                                'message' : f"User called user/uploadfile endpoint"
                                }
                            ]
                    )
                if response.status_code == 200:
                    st.success("Resume uploaded successfully!")   #success message
        
                    #call the Airflow API to trigger a DAG run
                    dag_id = "resume-preprocess_v1" #DAG id for the adhoc dag already defined on airflow
                    dag_run_id = "triggered_using_ui_" + str(time.time() * 1e3)    #unique run id for each dag run using current time
                    response = requests.post(url=f"{airflow_url}/api/v1/dags/{dag_id}/dagRuns",
                                            headers={"Authorization": f"Basic {airflow_credentials}"},    #base 64 encoded value of username:password for Airflow instance
                                            json = {
                                                    "dag_run_id": dag_run_id,
                                                    "conf": {"username": st.session_state['username']}
                                                    }
                                            #payload data in json
                                        )
                    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                            logGroupName = "project-refined-job-postings",
                            logStreamName = "ui",
                            logEvents = [
                                {
                                'timestamp' : int(time.time() * 1e3),
                                'message' : f"Application trigged Airflow DAG with id: {dag_id}"
                                }
                            ]
                    )
                    resp_json = response.json() #get the response json of the API call done
                    #wait until the DAG run finishes
                    with st.spinner('Processing resume...'):  #waiting for adhoc dag run to finish, might take a minute
                        while(True):    #check status of the DAG run just executed recursively to check when it is successfully completed
                            #call the Airflow API to get the dag run we just executed above
                            #trigger Airflow's adhoc DAG to transcribe this audio file & storing the general questions responses got from OpenAI's ChatGPT API into the processed-text-files folder
                            response_dag_status = requests.get(url=f"{airflow_url}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}",
                                                            headers={"Authorization": f"Basic {airflow_credentials}"},    #base 64 encoded
                                                            )
                            #st.write(response_dag_status.json())
                            resp_json1 = response_dag_status.json() #get the response json
                            if(resp_json1['state'] == 'success'):   #if the 'state' of this dag run is 'success', it has executed
                                clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                        logGroupName = "project-refined-job-postings",
                                        logStreamName = "ui",
                                        logEvents = [
                                            {
                                            'timestamp' : int(time.time() * 1e3),
                                            'message' : f"Airflow DAG with id: {dag_id} run successfully"
                                            }
                                        ]
                                )
                                break   #break spinner once dag executed
                        st.experimental_rerun()
                elif response.status_code == 401:   #when token is not authorized
                    st.error("Session token expired, please login again")   #display error
                    st.stop()
                else:# response.status_code == 400:
                    st.warning("Unable to perform operation, please try again file, please try again")  #user does not exist

        elif response.status_code == 401:   #when token is not authorized
            st.error("Session token expired, please login again")   #display error
            st.stop()

        else:
            st.error("Service unavailable, please check later")

if __name__ == '__main__' :
    app() 