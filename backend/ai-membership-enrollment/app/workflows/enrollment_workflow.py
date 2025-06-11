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
    messages: Annotated[List[Dict[str, str]], add_messages]
    session_id: str
    user_id: str
    current_step: str
    collected_data: Dict[str, Any]
    is_complete: bool
    ticket_generated: bool

class EnrollmentWorkflow:
    def __init__(self, qdrant_manager: QdrantManager):
        self.qdrant_manager = qdrant_manager
        self.openai_service = OpenAIService()
        self.pii_service = PIIService()
        self.pdf_service = PDFService()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(EnrollmentState)
        
        workflow.add_node("start", self._start_node)
        workflow.add_node("ask_name", self._ask_name_node)
        workflow.add_node("ask_email", self._ask_email_node)
        workflow.add_node("ask_program_type", self._ask_program_type_node)
        workflow.add_node("ask_company", self._ask_company_node)
        workflow.add_node("validate_profile", self._validate_profile_node)
        workflow.add_node("generate_ticket", self._generate_ticket_node)
        workflow.add_node("complete", self._complete_node)
        
        workflow.add_edge("start", "ask_name")
        workflow.add_conditional_edges(
            "ask_name",
            self._should_continue,
            {
                "ask_email": "ask_email",
                "ask_name": "ask_name"
            }
        )
        workflow.add_conditional_edges(
            "ask_email",
            self._should_continue,
            {
                "ask_program_type": "ask_program_type",
                "ask_email": "ask_email"
            }
        )
        workflow.add_conditional_edges(
            "ask_program_type",
            self._should_continue,
            {
                "ask_company": "ask_company",
                "ask_program_type": "ask_program_type"
            }
        )
        workflow.add_conditional_edges(
            "ask_company",
            self._should_continue,
            {
                "validate_profile": "validate_profile",
                "ask_company": "ask_company"
            }
        )
        workflow.add_edge("validate_profile", "generate_ticket")
        workflow.add_edge("generate_ticket", "complete")
        workflow.add_edge("complete", END)
        
        workflow.set_entry_point("start")
        
        return workflow.compile()
    
    async def process_message(self, session_id: str, message: str, user_id: str = None) -> ChatResponse:
        try:
            if not user_id:
                user_id = str(uuid.uuid4())
            
            existing_session = await self.qdrant_manager.get_session_data(session_id)
            
            if existing_session:
                state = EnrollmentState(
                    messages=existing_session.get("messages", []),
                    session_id=session_id,
                    user_id=user_id,
                    current_step=existing_session.get("current_step", "start"),
                    collected_data=existing_session.get("collected_data", {}),
                    is_complete=existing_session.get("is_complete", False),
                    ticket_generated=existing_session.get("ticket_generated", False)
                )
            else:
                state = EnrollmentState(
                    messages=[],
                    session_id=session_id,
                    user_id=user_id,
                    current_step="start",
                    collected_data={},
                    is_complete=False,
                    ticket_generated=False
                )
            
            state["messages"].append({"role": "user", "content": message})
            
            result = await self.workflow.ainvoke(state)
            
            response_message = result["messages"][-1]["content"] if result["messages"] else "I'm here to help with your membership enrollment."
            
            session_data = {
                "messages": result["messages"],
                "current_step": result["current_step"],
                "collected_data": result["collected_data"],
                "is_complete": result["is_complete"],
                "ticket_generated": result["ticket_generated"],
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
    
    async def _start_node(self, state: EnrollmentState) -> EnrollmentState:
        welcome_message = "Welcome to our membership enrollment process! I'm here to help you get started. Let's begin by collecting some basic information."
        state["messages"].append({"role": "assistant", "content": welcome_message})
        state["current_step"] = "ask_name"
        return state
    
    async def _ask_name_node(self, state: EnrollmentState) -> EnrollmentState:
        if "name" not in state["collected_data"]:
            message = "What is your full name?"
            state["messages"].append({"role": "assistant", "content": message})
        else:
            last_user_message = next((msg["content"] for msg in reversed(state["messages"]) if msg["role"] == "user"), "")
            if last_user_message and not state["collected_data"].get("name"):
                state["collected_data"]["name"] = last_user_message.strip()
                state["current_step"] = "ask_email"
                confirmation = f"Thank you, {state['collected_data']['name']}! "
                state["messages"].append({"role": "assistant", "content": confirmation})
        return state
    
    async def _ask_email_node(self, state: EnrollmentState) -> EnrollmentState:
        if "email" not in state["collected_data"]:
            message = "What is your email address?"
            state["messages"].append({"role": "assistant", "content": message})
        else:
            last_user_message = next((msg["content"] for msg in reversed(state["messages"]) if msg["role"] == "user"), "")
            if last_user_message and "@" in last_user_message:
                state["collected_data"]["email"] = last_user_message.strip()
                state["current_step"] = "ask_program_type"
                confirmation = "Great! I've recorded your email address."
                state["messages"].append({"role": "assistant", "content": confirmation})
            else:
                message = "Please provide a valid email address."
                state["messages"].append({"role": "assistant", "content": message})
        return state
    
    async def _ask_program_type_node(self, state: EnrollmentState) -> EnrollmentState:
        if "program_type" not in state["collected_data"]:
            message = "What type of membership program are you interested in? (e.g., Basic, Premium, Corporate)"
            state["messages"].append({"role": "assistant", "content": message})
        else:
            last_user_message = next((msg["content"] for msg in reversed(state["messages"]) if msg["role"] == "user"), "")
            if last_user_message:
                state["collected_data"]["program_type"] = last_user_message.strip()
                state["current_step"] = "ask_company"
                confirmation = f"Excellent! You're interested in the {state['collected_data']['program_type']} program."
                state["messages"].append({"role": "assistant", "content": confirmation})
        return state
    
    async def _ask_company_node(self, state: EnrollmentState) -> EnrollmentState:
        if "company" not in state["collected_data"]:
            message = "What is your company name?"
            state["messages"].append({"role": "assistant", "content": message})
        else:
            last_user_message = next((msg["content"] for msg in reversed(state["messages"]) if msg["role"] == "user"), "")
            if last_user_message:
                state["collected_data"]["company"] = last_user_message.strip()
                state["current_step"] = "validate_profile"
                confirmation = "Perfect! I have all the information I need."
                state["messages"].append({"role": "assistant", "content": confirmation})
        return state
    
    async def _validate_profile_node(self, state: EnrollmentState) -> EnrollmentState:
        required_fields = ["name", "email", "program_type", "company"]
        missing_fields = [field for field in required_fields if field not in state["collected_data"]]
        
        if missing_fields:
            message = f"I still need the following information: {', '.join(missing_fields)}"
            state["messages"].append({"role": "assistant", "content": message})
            state["current_step"] = f"ask_{missing_fields[0]}"
        else:
            message = "Let me validate your information and prepare your membership enrollment."
            state["messages"].append({"role": "assistant", "content": message})
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
            state["messages"].append({"role": "assistant", "content": message})
            
        except Exception as e:
            logging.error(f"Ticket generation error: {str(e)}")
            message = "I encountered an issue generating your ticket. Please try again or contact support."
            state["messages"].append({"role": "assistant", "content": message})
        
        return state
    
    async def _complete_node(self, state: EnrollmentState) -> EnrollmentState:
        state["is_complete"] = True
        completion_message = "Your membership enrollment is complete! You can download a summary of your enrollment or view your ticket details. Is there anything else I can help you with?"
        state["messages"].append({"role": "assistant", "content": completion_message})
        return state
    
    def _should_continue(self, state: EnrollmentState) -> str:
        current_step = state["current_step"]
        collected_data = state["collected_data"]
        
        if current_step == "ask_name" and "name" in collected_data:
            return "ask_email"
        elif current_step == "ask_email" and "email" in collected_data:
            return "ask_program_type"
        elif current_step == "ask_program_type" and "program_type" in collected_data:
            return "ask_company"
        elif current_step == "ask_company" and "company" in collected_data:
            return "validate_profile"
        
        return current_step
    
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
