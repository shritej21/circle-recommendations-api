
from fastapi import FastAPI

from app.routers.recommendations import router as recommendations_router


app = FastAPI(
    title="Circle Recommendations API",
    description=(
        "An API that recommends relevant and active Circles "
        "based on member interests and community activity."
    ),
    version="1.0.0",
)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "message": "Circle Recommendations API is running",
    }


app.include_router(recommendations_router)
