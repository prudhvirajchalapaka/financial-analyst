"""
Upload Router - Handles PDF upload and processing
"""
import os
import uuid
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from services.ingest import load_pdf_elements
from services.summarize import generate_image_summaries
from services.rag import create_vector_db

router = APIRouter(prefix="/api", tags=["upload"])

# In-memory session storage (use Redis in production)
sessions: dict = {}

class SessionStatus(BaseModel):
    session_id: str
    status: str  # "processing", "ready", "error"
    message: Optional[str] = None
    document_name: Optional[str] = None

class UploadResponse(BaseModel):
    session_id: str
    message: str

def process_pdf_background(session_id: str, file_path: str, file_name: str, temp_dir: str):
    """Background task to process PDF."""
    try:
        sessions[session_id]["status"] = "processing"
        sessions[session_id]["message"] = "Extracting text and images..."
        
        # Create Image Directory
        temp_img_dir = os.path.join(temp_dir, "images")
        os.makedirs(temp_img_dir, exist_ok=True)
        
        # Run Pipeline
        texts, tables = load_pdf_elements(file_path, temp_img_dir)
        
        sessions[session_id]["message"] = "Analyzing charts with AI..."
        img_summaries, img_paths = generate_image_summaries(temp_img_dir)
        
        sessions[session_id]["message"] = "Building knowledge base..."
        db_path = os.path.join(temp_dir, "chroma_db")
        create_vector_db(texts, img_summaries, img_paths, db_path)
        
        sessions[session_id]["status"] = "ready"
        sessions[session_id]["message"] = "Ready for questions!"
        sessions[session_id]["db_path"] = db_path
        sessions[session_id]["document_name"] = file_name
        
    except Exception as e:
        sessions[session_id]["status"] = "error"
        sessions[session_id]["message"] = str(e)

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a PDF file for processing."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create session
    session_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp()
    
    # Save uploaded file
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Initialize session
    sessions[session_id] = {
        "status": "uploading",
        "message": "File uploaded, starting processing...",
        "temp_dir": temp_dir,
        "file_path": file_path,
        "chat_history": []
    }
    
    # Start background processing
    background_tasks.add_task(
        process_pdf_background, 
        session_id, 
        file_path, 
        file.filename,
        temp_dir
    )
    
    return UploadResponse(
        session_id=session_id,
        message="Upload successful. Processing started."
    )

@router.get("/status/{session_id}", response_model=SessionStatus)
async def get_status(session_id: str):
    """Get the processing status of a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return SessionStatus(
        session_id=session_id,
        status=session["status"],
        message=session.get("message"),
        document_name=session.get("document_name")
    )

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and clean up resources."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Cleanup temp directory
    if "temp_dir" in session:
        shutil.rmtree(session["temp_dir"], ignore_errors=True)
    
    del sessions[session_id]
    
    return {"message": "Session deleted successfully"}
