from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    is_complete: bool
    next_step: str
    collected_data: Dict[str, Any]

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    messages: List[Dict[str, str]]
    current_step: str
    collected_data: Dict[str, Any]
    is_complete: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TicketResponse(BaseModel):
    ticket_id: str
    subject: str
    description: str
    category: str
    assignee: str
    priority: str
    status: str
    requester_email: str
    member_details: Dict[str, Any]
    created_at: str

class ZendeskTicket(BaseModel):
    id: str
    subject: str
    description: str
    status: str
    priority: str
    requester_email: str
    created_at: str
    updated_at: str
    tags: List[str]
