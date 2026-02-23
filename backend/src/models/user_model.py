import re

from pydantic import field_validator, BaseModel, Field
import string


class AuthModel(BaseModel):
   
    username: str = Field(..., min_length=3, max_length=50, examples=["username"])
    psswrd: str = Field(..., min_length=8, examples=["StrongPass1"])

    @field_validator("psswrd")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Ensure password has at least one uppercase, one lowercase, and one digit"""
        
        # if not any(c.islower() for c in value) and not any(c.isupper() for c in value) and not any(c in string.punctuation for c in value):
        #     raise ValueError("Password must contain at least one lowercase letter and  uppercase letter and special character") 
        
        check_v=dict()
        
        if not any(c.islower() for c in value):
           check_v['lowerchase'] =False
        if not any(c.isupper() for c in value) :
            # raise ValueError("Password must contain at least one uppercase letter")
            check_v['uppercase'] =False
        if not any(c.isdigit() for c in value):
            # raise ValueError("Password must contain at least one number")
            check_v['number'] =False
        if not any(c in string.punctuation for c in value):
            # raise ValueError("Password must contain at least one special character (!@#$%^&* etc.)")
            check_v['special_character'] =False
       
        f_string =""
        
        for item_key in check_v.keys(): 
            f_string += item_key + " "
            
        if f_string :  
            
            raise ValueError(f'Password must contain at least one {f_string}')
        return value

class Login_AuthModel(BaseModel):
   
    username: str = Field(..., min_length=3, max_length=50, examples=["username"])
    psswrd: str = Field(..., min_length=1, examples=["psswd"])