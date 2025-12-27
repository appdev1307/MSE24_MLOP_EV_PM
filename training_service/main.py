#!/usr/bin/env python3
"""
Training Service - API để trigger và monitor training jobs
"""

import os
import subprocess
import threading
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="Training Service API",
    description="API để trigger và monitor model training jobs",
    version="1.0.0"
)

# Check if running in Docker
IN_DOCKER = os.path.exists("/.dockerenv")
WORKSPACE_DIR = "/workspace" if IN_DOCKER else os.getcwd()

# Training state
training_state = {
    "status": "idle",  # idle, running, completed, failed
    "started_at": None,
    "completed_at": None,
    "log": []
}

TRAINER_SCRIPT = os.getenv("TRAINER_SCRIPT", "src/train.py")
USE_DOCKER = os.getenv("USE_DOCKER", "true").lower() == "true"


class TrainingRequest(BaseModel):
    """Request model cho training API."""
    force: bool = False
    rebuild: bool = True  # Có build lại Docker image không


def run_training(rebuild: bool = True):
    """Chạy training trong background thread."""
    global training_state
    
    training_state["status"] = "running"
    training_state["started_at"] = datetime.now().isoformat()
    training_state["completed_at"] = None
    training_state["log"] = []
    
    try:
        if USE_DOCKER:
            # Chạy training trong Docker container
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": "Starting training in Docker container..."
            })
            
            # Build trainer image nếu cần
            if rebuild:
                build_cmd = ["docker", "compose", "build", "trainer"]
                training_state["log"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": "Building trainer image..."
                })
                build_process = subprocess.run(
                    build_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=WORKSPACE_DIR
                )
                training_state["log"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Build output: {build_process.stdout[-500:]}"  # Last 500 chars
                })
            
            # Chạy training trong Docker container
            cmd = ["docker", "compose", "run", "--rm", "trainer"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=WORKSPACE_DIR
            )
        else:
            # Chạy training script trực tiếp
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": f"Running training script directly: {TRAINER_SCRIPT}"
            })
            process = subprocess.Popen(
                ["python", TRAINER_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=WORKSPACE_DIR
            )
        
        # Đọc log real-time
        for line in process.stdout:
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": line.strip()
            })
            # Giữ log không quá 1000 dòng
            if len(training_state["log"]) > 1000:
                training_state["log"] = training_state["log"][-1000:]
        
        process.wait()
        
        if process.returncode == 0:
            training_state["status"] = "completed"
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": "Training completed successfully!"
            })
        else:
            training_state["status"] = "failed"
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": f"Training failed with exit code {process.returncode}"
            })
            
    except Exception as e:
        training_state["status"] = "failed"
        training_state["log"].append({
            "timestamp": datetime.now().isoformat(),
            "message": f"Error: {str(e)}"
        })
    finally:
        training_state["completed_at"] = datetime.now().isoformat()


@app.get("/")
async def root():
    """API root endpoint - trả về thông tin API."""
    return JSONResponse(content={
        "service": "Training Service API",
        "version": "1.0.0",
        "description": "API để trigger và monitor model training jobs",
        "endpoints": {
            "POST /api/train": "Trigger training job",
            "GET /api/status": "Get training status",
            "GET /api/logs": "Get training logs",
            "GET /docs": "API documentation (Swagger UI)"
        },
        "current_status": training_state["status"]
    })


@app.post("/api/train")
async def start_training(request: TrainingRequest):
    """
    API endpoint để trigger training job.
    
    - **force**: Nếu True, sẽ bắt đầu training ngay cả khi đang có job đang chạy (kill job cũ)
    - **rebuild**: Nếu True, sẽ build lại Docker image trước khi chạy training
    """
    global training_state
    
    if training_state["status"] == "running" and not request.force:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Training is already running!",
                "status": training_state["status"],
                "hint": "Use force=true to stop current job and start new one"
            }
        )
    
    # Start training in background thread
    thread = threading.Thread(target=run_training, args=(request.rebuild,), daemon=True)
    thread.start()
    
    return JSONResponse(content={
        "message": "Training started! Check status at /api/status",
        "status": "running",
        "rebuild": request.rebuild
    })


@app.get("/api/status")
async def get_status():
    """API endpoint để lấy training status."""
    return JSONResponse(content=training_state)


@app.get("/api/logs")
async def get_logs():
    """API endpoint để lấy training logs."""
    return JSONResponse(content={
        "logs": training_state["log"],
        "total": len(training_state["log"])
    })

