from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME,
               version=settings.APP_VERSION, 
               description="API for Mistri Nepal", 
               docs_url="/docs", 
               redoc_url="/redocs", 
               openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={"status": "ok",
                                 "app_name": settings.APP_NAME,
                                 "app_version": settings.APP_VERSION}, status_code=200)
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return JSONResponse(content={"message": "Welcome to the Mistri Nepal API",
                                 "docs": "/docs",
                                 "redocs": "/redocs"}, status_code=200)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(content={"error": str(exc)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)