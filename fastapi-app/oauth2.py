from fastapi import Depends, HTTPException, status
import jwttoken
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "login")
def get_current_user(token: str = Depends(oauth2_scheme)):
    """Function to get the current user in session by verifying their JWT token. 
    Raises exception if the token does not match or if user does not exist
    -----
    Input parameters:
    token : str
        string token depending on the current user in session
    -----
    Returns:
    pwd_context.hash(password) : bool
        True if token is verified, Raises 401_unauthorized exception if False
    """
    credentials_exception = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials",
        headers = {"WWW-Authenticate": "Bearer"}
    )

    return jwttoken.verify_token(token, credentials_exception)