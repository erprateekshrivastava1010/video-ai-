import os
import sys
import time
import uuid
import shutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine import (
    TTSEngine,
    AudioAnalyzer,
    FacialAnimator,
    GestureEngine,
    VideoRenderer,
    AssetFactory
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Initialize engines
asset_factory = AssetFactory(BASE_DIR)
asset_factory.ensure_default_assets()

tts_engine = TTSEngine()
audio_analyzer = AudioAnalyzer(fps=30)
facial_animator = FacialAnimator(fps=30)
gesture_engine = GestureEngine(fps=30)
video_renderer = VideoRenderer(BASE_DIR, fps=30)

app = FastAPI(title="HeyGen Local Studio", description="Local AI Avatar & Video Synthesis Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and output directories
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

class GenerateRequest(BaseModel):
    script: str
    avatar_id: str = "sophia"
    voice_id: str = "en-us-female"
    emotion: str = "warm"
    gesture_mode: str = "auto"
    gesture_intensity: float = 1.0
    background_id: str = "modern_office.jpg"
    resolution: str = "1280x720"

class PreviewAudioRequest(BaseModel):
    script: str
    voice_id: str = "en-us-female"

@app.get("/")
def get_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "HeyGen Local Studio backend running. Please build static/index.html."}

@app.get("/api/voices")
def get_voices():
    return tts_engine.get_available_voices()

@app.get("/api/avatars")
def get_avatars():
    return asset_factory.list_avatars()

@app.get("/api/backgrounds")
def get_backgrounds():
    return asset_factory.list_backgrounds()

@app.post("/api/preview-audio")
def preview_audio(req: PreviewAudioRequest):
    if not req.script.strip():
        raise HTTPException(status_code=400, detail="Script text cannot be empty.")
    
    unique_id = str(uuid.uuid4())[:8]
    wav_filename = f"preview_{unique_id}.wav"
    wav_path = os.path.join(OUTPUT_DIR, wav_filename)

    tts_engine.synthesize(req.script, voice_id=req.voice_id, output_wav_path=wav_path)
    return {
        "status": "success",
        "audio_url": f"/output/{wav_filename}"
    }

@app.post("/api/upload-avatar")
async def upload_custom_avatar(
    name: str = Form(...),
    file: UploadFile = File(...)
):
    unique_id = "custom_" + str(uuid.uuid4())[:8]
    temp_upload_path = os.path.join(OUTPUT_DIR, f"temp_{unique_id}_{file.filename}")

    with open(temp_upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        meta = asset_factory.process_custom_avatar(temp_upload_path, unique_id, name)
        if os.path.exists(temp_upload_path):
            os.remove(temp_upload_path)
        return {
            "status": "success",
            "avatar": {
                "id": meta["id"],
                "name": meta["name"],
                "preview_url": f"/static/assets/avatars/{meta['id']}/base.png"
            }
        }
    except Exception as e:
        if os.path.exists(temp_upload_path):
            os.remove(temp_upload_path)
        raise HTTPException(status_code=400, detail=f"Failed to process portrait image: {str(e)}")

@app.post("/api/upload-video-avatar")
async def upload_custom_video_avatar(
    name: str = Form(...),
    file: UploadFile = File(...)
):
    unique_id = "video_" + str(uuid.uuid4())[:8]
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    temp_upload_path = os.path.join(OUTPUT_DIR, f"temp_{unique_id}{ext}")

    with open(temp_upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        meta = asset_factory.process_video_avatar(temp_upload_path, unique_id, name)
        if os.path.exists(temp_upload_path):
            os.remove(temp_upload_path)
        return {
            "status": "success",
            "avatar": {
                "id": meta["id"],
                "name": meta["name"],
                "preview_url": f"/static/assets/avatars/{meta['id']}/base.png"
            }
        }
    except Exception as e:
        if os.path.exists(temp_upload_path):
            os.remove(temp_upload_path)
        raise HTTPException(status_code=400, detail=f"Failed to process video avatar: {str(e)}")

@app.post("/api/generate")
def generate_video(req: GenerateRequest):
    start_time = time.time()
    if not req.script.strip():
        raise HTTPException(status_code=400, detail="Script text cannot be empty.")

    unique_id = str(uuid.uuid4())[:8]
    wav_path = os.path.join(OUTPUT_DIR, f"speech_{unique_id}.wav")
    mp4_filename = f"heygen_{unique_id}.mp4"
    mp4_path = os.path.join(OUTPUT_DIR, mp4_filename)

    # 1. Speech Synthesis
    t0 = time.time()
    tts_engine.synthesize(req.script, voice_id=req.voice_id, output_wav_path=wav_path)
    tts_dur = time.time() - t0

    # 2. Acoustic Feature Extraction & Prosody Decomposition
    t1 = time.time()
    audio_data = audio_analyzer.analyze_wav(wav_path)
    audio_dur = time.time() - t1

    # 3. Facial Expression & Lip-Sync Animation Stream
    anim_stream = facial_animator.generate_animation_stream(audio_data, emotion=req.emotion)

    # 4. Kinematic Hand Gesture Stream
    gest_stream = gesture_engine.schedule_gestures(
        audio_data, gesture_mode=req.gesture_mode, intensity=req.gesture_intensity
    )

    # 5. Multi-Layer Video Compositing & H.264/AAC Encoding
    w, h = 1280, 720
    if req.resolution == "720x1280":
        w, h = 720, 1280

    t2 = time.time()
    video_renderer.render_video(
        avatar_id=req.avatar_id,
        background_file=req.background_id,
        audio_wav=wav_path,
        animation_stream=anim_stream,
        gesture_stream=gest_stream,
        output_mp4=mp4_path,
        width=w,
        height=h
    )
    render_dur = time.time() - t2

    total_time = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "video_url": f"/output/{mp4_filename}",
        "audio_url": f"/output/speech_{unique_id}.wav",
        "metadata": {
            "duration": round(audio_data["duration"], 2),
            "total_frames": audio_data["total_frames"],
            "fps": 30,
            "resolution": f"{w}x{h}",
            "processing_time": total_time,
            "tts_time": round(tts_dur, 2),
            "render_time": round(render_dur, 2),
            "stress_peaks_count": len(audio_data.get("stress_peaks", []))
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("🚀 Starting HeyGen Local Studio at http://localhost:7860")
    print("=" * 60 + "\n")
    uvicorn.run("app:app", host="127.0.0.1", port=7860, reload=False)
