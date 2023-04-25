from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated= "auto")  #instance of cryptcontext which uses the bcrypt scheme for hashing


class Hash():
    def bcrypt(password: str):
        """Function to hash the plain text password created by the user to maintain privacy.
    -----
    Input parameters:
    password : str
        string containing password entered by the user 
    -----
    Returns:
    pwd_context.hash(password) : str
        string containing hashed password 
    """
        return  pwd_context.hash(password)
    
    def verify(hashed_password, plain_password):
        """Function to verify the plain text password against the hashed password stored in the Database. This
        is to check if the password entered by the user is correct"
    -----
    Input parameters:
    hashed_password : str
        string containing hashed password of the user fetched from the database
    plain_password:
        string containing password entered by the user during login in plain text
    -----
    Returns:
    pwd_context.verify(plain_password,hashed_password) : bool
        True if password matched the hash
    """
        return pwd_context.verify(plain_password,hashed_password)