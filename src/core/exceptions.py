from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

class BusinessException(Exception):
    def __init__(self, detail: str, code: int = 400):
        self.detail = detail
        self.code = code

async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200, 
        content={
            "code": exc.code,
            "message": exc.detail,
            "data": None
        },
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=200,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Serialize errors to make sure they are JSON serializable
    serializable_errors = []
    for error in errors:
        err = dict(error)
        if 'input' in err and isinstance(err['input'], bytes):
            err['input'] = err['input'].decode('utf-8', errors='replace')
        serializable_errors.append(err)
        
    return JSONResponse(
        status_code=200,
        content={
            "code": 422,
            "message": "Validation Error",
            "data": serializable_errors
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": None
        },
    )
