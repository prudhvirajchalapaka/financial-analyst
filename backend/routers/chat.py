"""
Chat Router - Handles conversation with the RAG system
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from services.rag import get_rag_chain
from routers.upload import sessions

router = APIRouter(prefix="/api", tags=["chat"])

# Store for LangChain message histories
message_stores: dict = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

class SourceEvidence(BaseModel):
    source_type: str
    content: str
    image_path: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceEvidence]

class ChatHistoryItem(BaseModel):
    role: str
    content: str

class ChatHistoryResponse(BaseModel):
    history: list[ChatHistoryItem]

def get_session_history(session_id: str):
    """Get or create message history for a session."""
    if session_id not in message_stores:
        message_stores[session_id] = ChatMessageHistory()
    return message_stores[session_id]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get an AI response."""
    session_id = request.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] != "ready":
        raise HTTPException(
            status_code=400, 
            detail=f"Session not ready. Current status: {session['status']}"
        )
    
    try:
        # Get RAG chain
        rag_chain = get_rag_chain(session["db_path"])
        
        # Wrap with message history
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        # Invoke chain
        response = conversational_rag_chain.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": session_id}}
        )
        
        # Store in session history for UI
        if "chat_history" not in session:
            session["chat_history"] = []
        session["chat_history"].append({"role": "user", "content": request.message})
        session["chat_history"].append({"role": "assistant", "content": response["answer"]})
        
        # Extract sources
        sources = []
        for doc in response.get("context", []):
            source_type = doc.metadata.get("source", "unknown")
            sources.append(SourceEvidence(
                source_type=source_type,
                content=doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                image_path=doc.metadata.get("image_path") if source_type == "image" else None
            ))
        
        return ChatResponse(
            answer=response["answer"],
            sources=sources[:5]  # Limit to 5 sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    history = session.get("chat_history", [])
    
    return ChatHistoryResponse(
        history=[ChatHistoryItem(role=h["role"], content=h["content"]) for h in history]
    )
