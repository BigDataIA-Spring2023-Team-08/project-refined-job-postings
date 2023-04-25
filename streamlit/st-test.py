import streamlit as st

# Define a list of existing users for demo purposes
EXISTING_USERS = {"john": "password123", "jane": "password456"}

# Define a dictionary to store uploaded resumes by user
RESUMES = {}

# Define the main function to run the app
def main():
    st.set_page_config(page_title="Resume Recommender App", page_icon=":guardsman:", layout="wide")
    st.title("Resume Recommender App")

    # Show login page by default
    if "username" not in st.session_state:
        show_login_page()
    else:
        # Show dashboard page if user is logged in
        col1, col2, col3, col4, col5 = st.columns(5)

        with col5:
            if st.button("Logout"):
                st.session_state.pop("username")
                st.info("Logged out successfully.")
        show_dashboard_page()

# Define a function to show the login page
def show_login_page():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in EXISTING_USERS and password == EXISTING_USERS[username]:
            st.success(f"Logged in as {username}")
            st.session_state["username"] = username
        else:
            st.error("Invalid username or password")

    st.header("Sign Up")
    new_username = st.text_input("New username")
    new_password = st.text_input("New password", type="password")
    if st.button("Sign Up"):
        if new_username in EXISTING_USERS:
            st.error("Username already exists")
        else:
            EXISTING_USERS[new_username] = new_password
            st.success(f"Account created for {new_username}. Please login.")
    
# Define a function to show the dashboard page
def show_dashboard_page():

    
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
    
    
if __name__ == "__main__":
    main()
