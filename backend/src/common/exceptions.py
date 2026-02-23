from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from src.models.error_schemas import (Error400, Error401,
                                                         Error403, Error404,
                                                         Error408, Error409,
                                                         Error422, Error500,
                                                         Error501)


# Method to raise the exception based on statuscode, errorcode and errormessage
def raise_exception(status_msg_code, message, reason, reference_error, message_code, property_path):

    if status_msg_code in (400, 401, 403, 404, 409, 500, 501, 408, 413, 415):

        error_data = {
            "message": str(message),
            "reason": reason,
            "referenceError": reference_error,
            "code": message_code
            }
        
        if status_msg_code == 400:
            response_data = jsonable_encoder(Error400(**error_data))
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
        
        elif status_msg_code == 401:
            response_data = jsonable_encoder(Error401(**error_data))
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
        
        elif status_msg_code == 403:
            response_data = jsonable_encoder(Error403(**error_data))
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
        
        elif status_msg_code == 404:
            response_data = jsonable_encoder(Error404(**error_data))
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
        
        elif status_msg_code == 409:
            response_data = jsonable_encoder(Error409(**error_data))
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
        
        elif status_msg_code == 501:
            response_data = jsonable_encoder(Error501(**error_data))
            return JSONResponse(
                status_code=status.HTTP_501_NOT_IMPLEMENTED, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
        elif status_msg_code == 408:
            response_data = jsonable_encoder(Error408(**error_data))
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
            
        elif status_msg_code == 413:
            response_data = jsonable_encoder(error_data)
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
        
        elif status_msg_code == 415:
            response_data = jsonable_encoder(error_data)
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, 
                content=response_data,
                media_type="application/json;charset=utf-8"
                )
            
        
        else:
            response_data = jsonable_encoder(Error500(**error_data))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_data,
                media_type="application/json;charset=utf-8"
            )
    
    elif status_msg_code == 422:
        error_data = {
            "message": str(message),
            "reason": reason,
            "referenceError": reference_error,
            "code": message_code,
            "propertyPath": property_path
            }
        
        response_data = jsonable_encoder(Error422(**error_data))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response_data,
            media_type="application/json;charset=utf-8"
        )
    else:
        error_data = {
            "message": f"{status_msg_code} status code is not allowed.",
            "reason": "Not allowed",
            "referenceError": "https://example.com",
            "code": "unexpectedProperty"
            }
        response_data = jsonable_encoder(Error422(**error_data))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response_data,
            media_type="application/json;charset=utf-8"
        )