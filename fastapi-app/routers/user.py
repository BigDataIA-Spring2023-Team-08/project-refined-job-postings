import pandas as pd
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3
from sqlite3 import Connection
import schema, userdb, db_model, oauth2
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from get_database_files import get_userdb_file
from hashing import Hash

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

# @router.get('/details', status_code=status.HTTP_200_OK)
# async def user_details(username : str, current_user: schema.User = Depends(oauth2.get_current_user), userdb_conn : Connection = Depends(get_userdb_file)):
#     """Function to get user plan of the given username by accessing it through the user database
#     -----
#     Input parameters:
#     username : str
#         User name of currnet logged in user
#     -----
#     Returns:
#     A list containing the plan of the user"""
#     query = "SELECT user_type FROM users WHERE username==\'" + username +"\'"  #sql query to execute
#     df_user = pd.read_sql_query(query, userdb_conn)
#     if df_user['user_type'].to_list() == ['admin']:
#         return df_user['user_type'].to_list()
#     else:
#         query2 = "SELECT plan FROM users WHERE username==\'" + username +"\'"  #sql query to execute
#         df_user2 = pd.read_sql_query(query2, userdb_conn)
#         plan = df_user2['plan'].tolist()    #convert the returned df to a list
#         return plan

# @router.post('/updateplan', status_code=status.HTTP_200_OK)
# async def update_plan(username : str, current_user: schema.User = Depends(oauth2.get_current_user), userdb_conn : Connection = Depends(get_userdb_file)):
#     """ Function to upgrade the user plan associated with the user to the next level
#     Input parameters:
#     username : str
#         string containing the username of the user that requires a password update
#     -----
#     Returns:
#     user_in_db : db
#         updates the user in the User_Table of the database
#     """
#     #print(username)
#     query = "SELECT plan FROM users WHERE username=\'" + username +"\'"  #sql query to execute
#     df_user = pd.read_sql_query(query, userdb_conn)
#     if df_user['plan'].iloc[0] == 'Free':
#         df_user['plan'].iloc[0] = 'Gold' 

#     elif df_user['plan'].iloc[0] == 'Gold':
#         df_user['plan'].iloc[0] = 'Platinum' 


#     cursor = userdb_conn.cursor()
#     update_query = "UPDATE users SET plan = ? WHERE username = ?"

#     # Define the values to substitute in the query
#     new_plan = df_user['plan'].iloc[0]
#     username = username

#     # Execute the update query with parameter substitution
#     cursor.execute(update_query, (new_plan, username))
#     # # Define the update query to update the user's plan
#     # update_query = "UPDATE users SET plan =\'"+df_user['plan']+"\' WHERE username=\'" + username +"\'"  #sql query to execute

#     # # Execute the update query
#     # cursor.execute(update_query)

#     # Commit the changes to the database
#     userdb_conn.commit()
#     # Close the cursor and the database connection
#     cursor.close()
#     return True
# userdb_conn.close()
#     query2 = "UPDATE users SET plan =\'"+df_user['plan']+"\' WHERE username==\'" + username +"\'"  #sql query to execute
#     df_user = pd.read_sql_query(query, userdb_conn)
#     user_in_db = db.query(db_model.User_Table).filter(username == db_model.User_Table.username).first()
#     if not user_in_db:
#         raise HTTPException(status_code=404, detail="User not found")
#     updated_user_data = dict(username = username, password = Hash.bcrypt(new_password.password)) #dictionary to store the user and hashes the new password
#     for key, value in updated_user_data.items(): 
#             setattr(user_in_db, key, value) #set attributes of user based on their username and new password
#     db.add(user_in_db)
#     db.commit()
#     db.refresh(user_in_db)
#     return user_in_db