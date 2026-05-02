from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config.config import settings
from fastapi import status
from app.core.app.app_health import app_health_router
from app.modules.auth.router import auth_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for Mistri Nepal",
    docs_url="/docs",
    redoc_url="/redocs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        content={"detail": str(exc), "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.exception_handler(
    RequestValidationError,
)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_list = []
    for err in exc.errors():
        error_list.append(err["msg"])
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": error_list,
            "status": status.HTTP_400_BAD_REQUEST,
        },
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(
    request: Request, exc: ResponseValidationError
):
    error_list = []
    for err in exc.errors():
        error_list.append(err["msg"])
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_list,
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )

app.router.prefix = settings.API_VERSION_PREFIX
app.include_router(app_health_router)
app.include_router(auth_router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
