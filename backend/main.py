from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.upload import router as upload_router
from routes.flagged import router as flagged_router

app = FastAPI(
    title="SentinelAI Backend",
    version="1.0.0",
)

# -----------------------------------
# CORS
# -----------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# Routers
# -----------------------------------

app.include_router(upload_router)
app.include_router(flagged_router)


# -----------------------------------
# Health Check
# -----------------------------------

@app.get("/")
def root():
    return {
        "message": "SentinelAI Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }