from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import Dict, Any, List, TypedDict, Annotated
import uuid
from datetime import datetime
import logging
from app.services.openai_service import OpenAIService
from app.services.pii_service import PIIService
from app.services.pdf_service import PDFService
from app.database.qdrant_client import QdrantManager
from app.schemas.enrollment import ChatResponse

class EnrollmentState(TypedDict):
    session_id: str
    user_id: str
    current_step: str
    collected_data: Dict[str, Any]
    is_complete: bool
    ticket_generated: bool
    last_user_message: str
    response_message: str

class EnrollmentWorkflow:
    def __init__(self, qdrant_manager: QdrantManager):
        self.qdrant_manager = qdrant_manager
        self.openai_service = OpenAIService()
        self.pii_service = PIIService()
        self.pdf_service = PDFService()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(EnrollmentState)
        
        workflow.add_node("process_conversation", self._process_conversation_node)
        
        workflow.add_edge("process_conversation", END)
        
        workflow.set_entry_point("process_conversation")
        
        return workflow.compile()
    
    async def process_message(self, session_id: str, message: str, user_id: str = None) -> ChatResponse:
        try:
            if not user_id:
                user_id = str(uuid.uuid4())
            
            existing_session = await self.qdrant_manager.get_session_data(session_id)
            
            if existing_session:
                state = EnrollmentState(
                    session_id=session_id,
                    user_id=user_id,
                    current_step=existing_session.get("current_step", "start"),
                    collected_data=existing_session.get("collected_data", {}),
                    is_complete=existing_session.get("is_complete", False),
                    ticket_generated=existing_session.get("ticket_generated", False),
                    last_user_message=message,
                    response_message=""
                )
            else:
                state = EnrollmentState(
                    session_id=session_id,
                    user_id=user_id,
                    current_step="start",
                    collected_data={},
                    is_complete=False,
                    ticket_generated=False,
                    last_user_message=message,
                    response_message=""
                )
            
            result = await self.workflow.ainvoke(state, config={"recursion_limit": 5})
            
            response_message = result.get("response_message", "I'm here to help with your membership enrollment.")
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "messages": [
                    {"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()},
                    {"role": "assistant", "content": response_message, "timestamp": datetime.utcnow().isoformat()}
                ],
                "current_step": result["current_step"],
                "collected_data": result["collected_data"],
                "is_complete": result["is_complete"],
                "ticket_generated": result["ticket_generated"],
                "created_at": datetime.utcnow().isoformat() if not existing_session else existing_session.get("created_at"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            embedding = await self.openai_service.get_embedding(message)
            await self.qdrant_manager.store_session_data(session_id, user_id, session_data, embedding)
            
            return ChatResponse(
                message=response_message,
                session_id=session_id,
                is_complete=result["is_complete"],
                next_step=result["current_step"],
                collected_data=result["collected_data"]
            )
            
        except Exception as e:
            logging.error(f"Workflow processing error: {str(e)}")
            return ChatResponse(
                message="I apologize, but I encountered an error. Please try again.",
                session_id=session_id,
                is_complete=False,
                next_step="start",
                collected_data={}
            )
    
    async def _process_conversation_node(self, state: EnrollmentState) -> EnrollmentState:
        last_user_message = state["last_user_message"]
        
        if state["current_step"] == "start":
            welcome_message = "Welcome to our membership enrollment process! I'm here to help you get started. What is your full name?"
            state["response_message"] = welcome_message
            state["current_step"] = "ask_name"
            return state
        
        if state["current_step"] == "ask_name" and "name" not in state["collected_data"]:
            if last_user_message and len(last_user_message.strip()) > 1:
                if not any(greeting in last_user_message.lower() for greeting in ["hello", "hi", "hey", "want to enroll", "enroll", "i want", "help me"]):
                    state["collected_data"]["name"] = last_user_message.strip()
                    state["current_step"] = "ask_email"
                    message = f"Thank you, {state['collected_data']['name']}! What is your email address?"
                    state["response_message"] = message
                else:
                    message = "I need your full name to continue with the enrollment. What is your full name?"
                    state["response_message"] = message
        
        elif state["current_step"] == "ask_email" and "email" not in state["collected_data"]:
            if last_user_message and "@" in last_user_message:
                state["collected_data"]["email"] = last_user_message.strip()
                state["current_step"] = "ask_program_type"
                message = "Great! What type of membership program are you interested in? (e.g., Basic, Premium, Corporate)"
                state["response_message"] = message
            elif last_user_message:
                message = "Please provide a valid email address."
                state["response_message"] = message
        
        elif state["current_step"] == "ask_program_type" and "program_type" not in state["collected_data"]:
            if last_user_message and last_user_message.strip():
                state["collected_data"]["program_type"] = last_user_message.strip()
                state["current_step"] = "ask_company"
                message = f"Excellent! You're interested in the {state['collected_data']['program_type']} program. What is your company name?"
                state["response_message"] = message
        
        elif state["current_step"] == "ask_company" and "company" not in state["collected_data"]:
            if last_user_message and last_user_message.strip():
                state["collected_data"]["company"] = last_user_message.strip()
                state["current_step"] = "complete"
                
                try:
                    ticket_data = {
                        "ticket_id": str(uuid.uuid4()),
                        "subject": f"Membership Enrollment - {state['collected_data'].get('name', 'Unknown')}",
                        "description": f"New membership enrollment request for {state['collected_data'].get('program_type', 'Unknown')} program",
                        "category": "MP",
                        "assignee": "membership-team",
                        "priority": "normal",
                        "status": "open",
                        "requester_email": state["collected_data"].get("email", ""),
                        "member_details": state["collected_data"],
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    ticket_text = f"{ticket_data['subject']} {ticket_data['description']}"
                    embedding = await self.openai_service.get_embedding(ticket_text)
                    
                    await self.qdrant_manager.store_ticket_data(
                        session_id=state["session_id"],
                        ticket_data=ticket_data,
                        embedding=embedding
                    )
                    
                    state["ticket_generated"] = True
                    state["is_complete"] = True
                    
                    message = f"Perfect! I have all the information I need. Your membership enrollment ticket (ID: {ticket_data['ticket_id'][:8]}...) has been generated and is being processed by our membership team. Your enrollment is complete!"
                    state["response_message"] = message
                    
                except Exception as e:
                    logging.error(f"Ticket generation error: {str(e)}")
                    state["is_complete"] = True
                    message = "Perfect! I have all the information I need. Your membership enrollment is complete! You can download a summary of your enrollment or view your ticket details."
                    state["response_message"] = message
        
        return state
    
    def _determine_next_step(self, state: EnrollmentState) -> str:
        if state["is_complete"]:
            return END
        return "process_conversation"
    
    async def _ask_name_node(self, state: EnrollmentState) -> EnrollmentState:
        if "name" in state["collected_data"]:
            return state
        
        already_asked_for_name = False
        if "name" in state["collected_data"] or state["current_step"] != "ask_name":
            already_asked_for_name = True
        
        if not already_asked_for_name:
            message = "What is your full name?"
            state["response_message"] = message
        
        return state
    
    async def _ask_email_node(self, state: EnrollmentState) -> EnrollmentState:
        last_user_message = state.get("last_user_message", "")
        
        if "email" not in state["collected_data"]:
            message = "What is your email address?"
            state["response_message"] = message
        elif last_user_message and "@" in last_user_message:
            state["collected_data"]["email"] = last_user_message.strip()
            confirmation = "Great! I've recorded your email address."
            state["response_message"] = confirmation
        elif last_user_message:
            message = "Please provide a valid email address."
            state["response_message"] = message
        
        return state
    
    async def _ask_program_type_node(self, state: EnrollmentState) -> EnrollmentState:
        last_user_message = state.get("last_user_message", "")
        
        if "program_type" not in state["collected_data"]:
            message = "What type of membership program are you interested in? (e.g., Basic, Premium, Corporate)"
            state["response_message"] = message
        elif last_user_message and last_user_message.strip():
            state["collected_data"]["program_type"] = last_user_message.strip()
            confirmation = f"Excellent! You're interested in the {state['collected_data']['program_type']} program."
            state["response_message"] = confirmation
        
        return state
    
    async def _ask_company_node(self, state: EnrollmentState) -> EnrollmentState:
        last_user_message = state.get("last_user_message", "")
        
        if "company" not in state["collected_data"]:
            message = "What is your company name?"
            state["response_message"] = message
        elif last_user_message and last_user_message.strip():
            state["collected_data"]["company"] = last_user_message.strip()
            confirmation = "Perfect! I have all the information I need."
            state["response_message"] = confirmation
        
        return state
    
    async def _validate_profile_node(self, state: EnrollmentState) -> EnrollmentState:
        required_fields = ["name", "email", "program_type", "company"]
        missing_fields = [field for field in required_fields if field not in state["collected_data"]]
        
        if missing_fields:
            message = f"I still need the following information: {', '.join(missing_fields)}"
            state["response_message"] = message
            state["current_step"] = f"ask_{missing_fields[0]}"
        else:
            message = "Let me validate your information and prepare your membership enrollment."
            state["response_message"] = message
            state["current_step"] = "generate_ticket"
        
        return state
    
    async def _generate_ticket_node(self, state: EnrollmentState) -> EnrollmentState:
        try:
            ticket_data = {
                "ticket_id": str(uuid.uuid4()),
                "subject": f"Membership Enrollment - {state['collected_data'].get('name', 'Unknown')}",
                "description": f"New membership enrollment request for {state['collected_data'].get('program_type', 'Unknown')} program",
                "category": "MP",
                "assignee": "membership-team",
                "priority": "normal",
                "status": "open",
                "requester_email": state["collected_data"].get("email", ""),
                "member_details": state["collected_data"],
                "created_at": datetime.utcnow().isoformat()
            }
            
            ticket_text = f"{ticket_data['subject']} {ticket_data['description']}"
            embedding = await self.openai_service.get_embedding(ticket_text)
            
            await self.qdrant_manager.store_ticket_data(
                session_id=state["session_id"],
                ticket_data=ticket_data,
                embedding=embedding
            )
            
            state["ticket_generated"] = True
            state["current_step"] = "complete"
            
            message = f"Perfect! I've generated your membership enrollment ticket (ID: {ticket_data['ticket_id'][:8]}...). Your enrollment is now being processed by our membership team."
            state["response_message"] = message
            
        except Exception as e:
            logging.error(f"Ticket generation error: {str(e)}")
            message = "I encountered an issue generating your ticket. Please try again or contact support."
            state["response_message"] = message
        
        return state
    
    async def _complete_node(self, state: EnrollmentState) -> EnrollmentState:
        state["is_complete"] = True
        completion_message = "Your membership enrollment is complete! You can download a summary of your enrollment or view your ticket details. Is there anything else I can help you with?"
        state["response_message"] = completion_message
        return state
    
    def _should_continue_from_name(self, state: EnrollmentState) -> str:
        if "name" in state["collected_data"]:
            return "ask_email"
        return "ask_name"
    
    def _should_continue_from_email(self, state: EnrollmentState) -> str:
        if "email" in state["collected_data"]:
            return "ask_program_type"
        return "ask_email"
    
    def _should_continue_from_program_type(self, state: EnrollmentState) -> str:
        if "program_type" in state["collected_data"]:
            return "ask_company"
        return "ask_program_type"
    
    def _should_continue_from_company(self, state: EnrollmentState) -> str:
        if "company" in state["collected_data"]:
            return "validate_profile"
        return "ask_company"
    
    async def generate_pdf_summary(self, session_id: str) -> str:
        try:
            session_data = await self.qdrant_manager.get_session_data(session_id)
            if not session_data:
                raise ValueError("Session not found")
            
            collected_data = session_data.get("collected_data", {})
            pdf_path = self.pdf_service.generate_enrollment_summary(collected_data, session_id)
            
            summary_text = f"Enrollment summary for {collected_data.get('name', 'Unknown')}"
            embedding = await self.openai_service.get_embedding(summary_text)
            
            await self.qdrant_manager.store_summary_data(
                session_id=session_id,
                summary_text=summary_text,
                embedding=embedding
            )
            
            return pdf_path
            
        except Exception as e:
            logging.error(f"PDF summary generation error: {str(e)}")
            raise
