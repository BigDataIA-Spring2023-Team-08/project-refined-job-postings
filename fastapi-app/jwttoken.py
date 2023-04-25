from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import schema

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1

def create_access_token(data: dict):
    """Function to create a JWT Access token. It generates a token that expires after a 
    specified amount of time. 
    -----
    Input parameters:
    data : dict
        dictionary containing data during login 
    -----
    Returns:
    encoded_jwt : str
        string containing encoded JWT Token 
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  #token encoded using specified algorithm and stored in variable
    return encoded_jwt

def verify_token(token:str, credentials_exception):
    """Function to handle JWTError by verifying the username and token data raising a credentials exception
    -----
    Input parameters:
    token : str
       string containing token 

    -----
    Returns:
     None. Raises exception if the username does not match
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schema.TokenData(username=username)
    except JWTError:
        raise credentials_exception