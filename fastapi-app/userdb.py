from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
# commenting these lines out because it creates and erases db contents everytime file is run
# dir_path = os.path.dirname(os.path.realpath(__file__)) 
# f = open(os.path.join(dir_path, 'user_info.db'), 'w')
# f.close()



user_db_url = 'sqlite:///./user_info.db'  #defining database url
engine = create_engine(user_db_url, connect_args={"check_same_thread": False}) #creating engine 

#creating a session
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

#declaring mapping
Base = declarative_base()

def get_db():
    """Function to create a database session and close it after finishing.
    -----
    Input parameters:
    None
    -----
    Returns:
    None
    """
    db = SessionLocal()
    try:
        yield db  #return session object using yield
    finally:
        db.close