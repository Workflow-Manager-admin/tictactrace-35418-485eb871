from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .user import router as user_router
from .game import router as game_router

app = FastAPI(
    title="Tic Tac Toe Backend API",
    description="API backend for Tic Tac Toe fullstack app. Features: create/join games, submit moves, track state and results, user management.",
    version="1.0.0"
)

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

# Include routers for users and games
app.include_router(user_router)
app.include_router(game_router)

@app.get("/")
def health_check():
    """PUBLIC_INTERFACE
    Health check endpoint for the Tic Tac Toe backend.
    """
    return {"message": "Healthy"}
