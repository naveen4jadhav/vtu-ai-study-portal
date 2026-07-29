from fastapi import FastAPI

app = FastAPI(
    title="VTU AI Study Portal API",
    version="0.1.0",
    description="Backend API for the VTU AI Study Portal"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to VTU AI Study Portal 🚀"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }