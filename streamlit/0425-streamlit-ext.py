import streamlit as st
import requests
import json
import time

# Define API URL
API_URL = "http://your_api_url.com"

# Define function to check if user is logged in
def is_authenticated():
    if 'if_logged' not in st.session_state:
        st.session_state['if_logged'] = False
    return st.session_state['if_logged']

# Define function to handle logout
def logout():
    st.session_state['if_logged'] = False
    st.session_state['access_token'] = None
    st.session_state['username'] = None
    st.experimental_rerun()

# Define function to handle resume upload
def upload_resume():
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        with st.spinner("Uploading..."):
            try:
                response = requests.post(
                    f"{API_URL}/upload_resume",
                    files={"resume": uploaded_file},
                    headers={"Authorization": f"Bearer {st.session_state['access_token']}"}
                )
                clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                            logGroupName = "assignment-03",
                            logStreamName = "ui",
                            logEvents = [
                                {
                                'timestamp' : int(time.time() * 1e3),
                                'message' : "User uploaded resume"
                                }
                            ]
                        )
            except:
                st.error("Service unavailable, please try again later") #in case the API is not running
                st.stop()   #stop the application
            if response.status_code == 200:
                st.success("Resume uploaded successfully")
                st.experimental_rerun()
            else:
                st.error("Failed to upload resume. Please try again.")

# Define function to handle job recommendations
def get_job_recommendations():
    pass  # Replace with your own function for job recommendations

# Define app layout
def app():
    st.set_page_config(page_title="Login/Signup App", page_icon=":guardsman:", layout="wide")
    st.title("Login/Signup App")

    # Check if user is logged in
    if not is_authenticated():
        # Render login/signup form
        login_or_signup = st.selectbox("Please select an option", ["Login", "Signup", "Forgot Password?"])

        if login_or_signup == "Login":
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
                                logGroupName = "assignment-03",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "User called /login endpoint to validate login"
                                    }
                                ]
                            )
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
            st.write("Create an account to get started")
            name = st.text_input("Name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.button("Signup"):
                if name == '' or username == '' or password == '' or confirm_password == '':
                    st.warning("Please fill all the fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Wait.."):
                        payload = {'name': name, 'username': username, 'password': password}
                        try:
                            response = requests.request("POST", f"{API_URL}/signup", data=payload)
                            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                                logGroupName = "assignment-03",
                                logStreamName = "ui",
                                logEvents = [
                                    {
                                    'timestamp' : int(time.time() * 1e3),
                                    'message' : "User called /signup endpoint to create a new account"
                                    }
                                ]
                            )
                        except:
                            st.error("Service unavailable, please try again later") #in case the API is not running
                            st.stop()   #stop the application
                    if response.status_code == 200:
                        st.success("Account created successfully")
                    else:
                        st.error("Failed to create account. Please try again.")
        elif login_or_signup=="Forgot Password?":
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
            # Render user dashboard
            #show_dashboard_page()

            col1, col2, col3, col4, col5 = st.columns(5)

            with col5:
                if st.button("Logout"):
                    st.session_state.pop("username")
                    st.info("Logged out successfully.")

            st.set_page_config(page_title="Resume Recommender App", page_icon=":guardsman:", layout="wide")
            st.title("Resume Recommender App")

            st.header(f"Welcome, {st.session_state['username']}!")
            st.write("Upload your resume here:")
            uploaded_file = st.file_uploader("Choose a file", type="docx")
            if uploaded_file is not None:
                RESUMES[st.session_state["username"]] = uploaded_file
                st.success("Resume uploaded successfully!")
            
            # Check if user already uploaded a resume
            if st.session_state["username"] in RESUMES:
                st.write(f"Current resume: {RESUMES[st.session_state['username']].name}")
                if st.button("Change resume"):
                    del RESUMES[st.session_state["username"]]
                    st.info("Resume deleted. Please upload a new one.")


            jobtype = st.selectbox('Select a Job Type',
                ('--','Data Scientist', 'Data Engineer', 'Data Analyst'))

            st.write('You selected:', jobtype)
            
            if jobtype!='--':
                if st.button("Get job recommendations"):
                    #Todo: Add function to generate job recommendations
                    pass
            
            

            # st.write(f"Welcome, {st.session_state['username']}!")
            # st.write("What would you like to do today?")

            # # Show options for resume upload and job recommendations
            # option = st.selectbox("Please select an option", ["Upload Resume", "Get Job Recommendations"])

            # if option == "Upload Resume":
            #     upload_resume()

            # elif option == "Get Job Recommendations":
            #     get_job_recommendations()

            # # Add logout button
            # if st.button("Logout"):
            #     logout()

if __name__ == '__main__' :
    app() 

