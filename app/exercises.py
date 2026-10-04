from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .services.exercise_library import ExerciseLibrary, LibraryExercise

router = APIRouter()


@lru_cache
def library():
    return ExerciseLibrary()


@router.get('/api/exercises', response_model=list[LibraryExercise])
def list_exercises(category: str | None = None, priority: str | None = None,
                   analysis_status: str | None = None):
    return library().list(category, priority, analysis_status)


@router.get('/api/exercise-categories', response_model=list[str])
def exercise_categories():
    return library().categories


@router.get('/api/exercises/{exercise_id}', response_model=LibraryExercise)
def exercise_detail(exercise_id: str):
    try:
        return library().get(exercise_id)
    except KeyError:
        raise HTTPException(404, 'Ejercicio desconocido')


@router.get('/exercises', include_in_schema=False)
def exercise_library_page():
    return FileResponse(Path(__file__).parent / 'static' / 'exercise-library.html')
