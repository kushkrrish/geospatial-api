from fastapi import FastAPI
from app.api.v1.router import api_v1_router

app = FastAPI(
    title="Geospatial File Measurement API",
    version="1.0.0"
)

# Register version 1 API router
app.include_router(api_v1_router)

@app.get("/")
def root():
    return {"message": "Geospatial File Measurement API is running"}