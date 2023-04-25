import pandas as pd
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import sqlite3
from sqlite3 import Connection
import schema, userdb, db_model, oauth2
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from get_database_files import get_userdb_file
from hashing import Hash
from s3 import upload_to_s3
import uuid
import time
from io import BytesIO

router = APIRouter(
    prefix="/user",
    tags = ['Users']
)

get_db = userdb.get_db

@router.post('/create', response_model= schema.ShowUser)
def create_user(request: schema.User, db: Session = Depends(get_db)):
    """Creates a User in the User_Table inside the SQLite DB. The function stores the Name, Username and
        hashed password in the table to maintain privacy of the user.
    -----
    Input parameters:
    file_name : str
        string containg the filename (including extensions, if any) to fetch URL for
    Session : db
        current session of db
    -----
    Returns:
    new_user : db
        new user entry in the User_Table of the database
    """
    user = db.query(db_model.User_Table).filter(db_model.User_Table.username == request.username).first()  #query to db to match usernames
    if not user:
        new_user = db_model.User_Table(name = request.name, username = request.username, password = Hash.bcrypt(request.password)) #creates a new user 
        db.add(new_user) 
        db.commit()
        db.refresh(new_user) #new user in the existing table
        return new_user
        #raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Invalid Credentials") 

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Username already exists, please login")

@router.patch('/update',response_model= schema.ShowUser)
def update_password(username : str, new_password: schema.UpdateUserPassword, db: Session = Depends(get_db)):
    """ Function to change the user password and store the hashed password in the db
    Input parameters:
    username : str
        string containing the username of the user that requires a password update
    new_password : class 
        instance of a class containing the UserUpdatePassword
    
    -----
    Returns:
    user_in_db : db
        updates the user in the User_Table of the database
    """
    user_in_db = db.query(db_model.User_Table).filter(username == db_model.User_Table.username).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user_data = dict(username = username, password = Hash.bcrypt(new_password.password)) #dictionary to store the user and hashes the new password
    for key, value in updated_user_data.items(): 
            setattr(user_in_db, key, value) #set attributes of user based on their username and new password
    db.add(user_in_db)
    db.commit()
    db.refresh(user_in_db)
    return user_in_db

@router.post("/uploadfile/")
async def create_upload_file(username: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """ Function to change the user password and store the hashed password in the db
    Input parameters:
    username : str
         The username of the user whose resume file name will be updated.
    file : UploadFile
        The uploaded file.
    -----
    Returns:
    filename : dict
        A dictionary containing the filename of the uploaded file.
    """

    # generate filename with "resume_{username}"
    filename = f"resume_{username}"

    # store the file on S3
    upload_to_s3(file, filename)

    # retrieve user object by username
    user = db.query(db_model.User_Table).filter(db_model.User_Table.username == username).first()

    # update resume_filename field
    user.resume_file = filename

    # commit changes to database
    db.add(user)
    db.commit()

    return {"filename": filename}
