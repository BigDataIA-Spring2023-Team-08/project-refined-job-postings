from diagrams.custom import Custom
from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.client import User
from diagrams.aws.storage import S3
from diagrams.onprem.workflow import Airflow
from diagrams.onprem.container import Docker
from diagrams.programming.framework import Fastapi as Fastapi 
from diagrams.generic.database import SQL as SQL
from diagrams.oci.monitoring import Telemetry


with Diagram("CareerCompass Architecture", show=False,direction="LR"):
    user = User("User")
    with Cluster("Compute Instance Resume Uploads"):

        with Cluster("Applications"):
            streamlit_app = Custom("Streamlit", "./streamlit-icon.png")
            backend = Fastapi("FastAPI")
            streamlit_app - Edge(label = "API Calls", color = "red", style = "dashed") - backend

        with Cluster("Docker"):
            streamlit_docker = Docker("Dockerized Streamlit")
            docker_fastapi = Docker("Dockerized FASTAPI")
            backend - docker_fastapi
            streamlit_app - streamlit_docker
        
        with Cluster("Storage"):
            s3 = S3("CareerCompass S3 Bucket")
            user_db = SQL("User DB")

        with Cluster("Batch Process"):     
            airflow = Airflow("Airflow")
            GE = Telemetry("Data Quality Check")
        with Cluster("Model"):
            ml_model = Custom("ML Model", "./ml-icon2.png")
        with Cluster("Scraper"):
            scraper = Custom("Linkedin Scraper", "./pip-icon.png")
            scraper >> Edge(Label ="Job Scrapping stored as CSV")  >> s3

        


    backend << Edge(label = "Verify Login") >> user_db   
    backend << Edge(label = "Store user Resume") << s3 
    backend << Edge(label = "API call to run model and get results") >> ml_model
    admin = User("Admin") 
    

    airflow << Edge(Label = " ")>> s3  
    backend >> Edge(Label ="User gets top 3 job recommendations after model runs") >> user
    streamlit_app >> Edge(Label ="Process uploaded resume and store dataset for user resume and job title") >> airflow
    streamlit_app >> Edge(Label ="Prepare and store dataset for user resume and job title") >> airflow

    GE >> s3   
    airflow >> Edge(label = "Run Great Expectations") >> GE 

    user << Edge(label = "User Login & getting best matched jobs", color="darkgreen") >> streamlit_app  

    admin << Edge(label = "Admin Login to view dashboard for API", color = "blue") >> streamlit_app 
