from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class ProgramType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    CORPORATE = "corporate"

class TicketStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    SOLVED = "solved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EnrollmentData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    program_type: Optional[ProgramType] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    referral_source: Optional[str] = None

class ConversationMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class EnrollmentSession(BaseModel):
    session_id: str
    user_id: str
    messages: List[ConversationMessage] = []
    current_step: str = "start"
    collected_data: EnrollmentData = Field(default_factory=EnrollmentData)
    is_complete: bool = False
    ticket_generated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MembershipTicket(BaseModel):
    ticket_id: str
    subject: str
    description: str
    category: str = "MP"
    assignee: str = "membership-team"
    priority: TicketPriority = TicketPriority.NORMAL
    status: TicketStatus = TicketStatus.OPEN
    requester_email: str
    member_details: EnrollmentData
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
