from fastapi import APIRouter

router = APIRouter(prefix="/students", tags=["Students"])

students = [
    {
        "id": 1,
        "name": "Nisarga",
        "branch": "Mechanical"
    },
    {
        "id": 2,
        "name": "Rakshita",
        "branch": "ECE"
    }
]

@router.get("/")
def get_students():
    return students