import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, Body, APIRouter
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field  # Import Field for validation


BASE_DIR = Path(os.getcwd())
MAX_PATTERN_LENGTH = 255  # Max allowed length for glob pattern

app = FastAPI()


app = jsonrpc.API()

api_v1 = jsonrpc.Entrypoint('/api/v1/jsonrpc')
files_router = APIRouter(prefix='/api/v1/files')



class GlobRequest(BaseModel):
    base_dir: str = Field(description="The directory to search in.")
    pattern: Optional[str] = Field(
        default='*',
        description="The glob pattern to search for. Defaults to '*' (all files recursively). "
                    "Examples: '*.txt', 'folder1/**/*.log'",
        max_length=MAX_PATTERN_LENGTH
    )
class GlobResponse(BaseModel):
    files: List[str]


def rglob(request: GlobRequest) -> GlobResponse:
    """
    Recursively lists files within the BASE_DIR / request.base_dir matching the request.pattern.
    Returns a JSON object containing a list of file paths relative to the BASE_DIR.
    """
    base_dir = request.base_dir
    pattern = request.pattern

    all_files = []
    for item in Path(base_dir).rglob(pattern):
        if item.is_file():
            # Store the path relative to base_dir
            all_files.append(str(item.relative_to(base_dir)))

    return GlobResponse(files=all_files)


@files_router.get("/files/read/{file_path:path}")
async def read_file(file_path: str, request: Request):
    """
    Serves a file specified by the path relative to BASE_DIR.
    Supports range requests for partial content (e.g., for video streaming).
    """

    return FileResponse(
        path=file_path,
    )

app.bind_entrypoint(api_v1)
app.include_router(files_router)