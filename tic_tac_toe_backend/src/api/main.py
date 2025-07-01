from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    PUBLIC_INTERFACE
    Initialize the database at startup.
    """
    init_db()

@app.get("/")
def health_check():
    """PUBLIC_INTERFACE
    Health check endpoint for the Tic Tac Toe backend.
    """
    return {"message": "Healthy"}
