from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from manim import *
import tempfile
import os
import shutil
from starlette.background import BackgroundTask
from pydantic import BaseModel
import ast
import uuid  # Add this import at the top
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
app.mount("/public", StaticFiles(directory="public"), name="public")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

class ManimCode(BaseModel):
    code: str

def is_safe_code(code: str) -> bool:
    """Basic security check for the input code"""
    try:
        tree = ast.parse(code)
        # Check if the code only contains a class definition
        if not all(isinstance(node, ast.ClassDef) for node in tree.body):
            return False
        return True
    except:
        return False

@app.post("/api/py/generate-animation")
async def generate_animation(manim_code: ManimCode):
    try:
        if not is_safe_code(manim_code.code):
            raise HTTPException(status_code=400, detail="Invalid Manim code")

        # Set permanent output directory
        public_videos_dir = os.path.join(os.getcwd(), "public")
        video_output_dir = os.path.join(public_videos_dir, "videos", "1080p60")
        os.makedirs(video_output_dir, exist_ok=True)
        config.media_dir = public_videos_dir

        # Import and execute the scene
        namespace = {}
        globals_dict = dict(globals())
        exec(manim_code.code, globals_dict, namespace)
        scene_class = next(
            v for v in namespace.values()
            if isinstance(v, type) and issubclass(v, Scene)
        )
        scene = scene_class()

        # Render the scene without 'file_name' argument
        scene.render()
        
        # Get the actual output file path
        output_file_path = scene.renderer.file_writer.movie_file_path  # Updated line
        output_filename = os.path.basename(output_file_path)

        # Check if the rendered video file exists
        if not os.path.exists(output_file_path):
            raise HTTPException(status_code=500, detail="Video generation failed")

        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}.mp4"
        unique_video_path = os.path.join(video_output_dir, unique_filename)

        # Move and rename the rendered video to the unique filename
        shutil.move(output_file_path, unique_video_path)

        # Return the unique filename in JSON response
        return {"filename": unique_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}
