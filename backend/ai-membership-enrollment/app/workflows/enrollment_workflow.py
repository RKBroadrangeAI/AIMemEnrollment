from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import Dict, Any, List, TypedDict, Annotated, Optional
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
    wants_program_info: bool
    employment_status: str  # "self_employed", "advisor", "contractor", "full_time_employee"
    linkedin_profile_updated: bool
    board_positions: str
    consent_signed: bool
    role_clarification: Dict[str, Any]

class EnrollmentWorkflow:
    def __init__(self, qdrant_manager: QdrantManager):
        self.qdrant_manager = qdrant_manager
        self.openai_service = OpenAIService()
        self.pii_service = PIIService()
        self.pdf_service = PDFService()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(EnrollmentState)
        
        workflow.add_node("ask_program_interest", self._ask_program_interest_node)
        workflow.add_node("ask_employment_status", self._ask_employment_status_node)
        workflow.add_node("linkedin_check", self._linkedin_check_node)
        workflow.add_node("collect_board_info", self._board_positions_node)
        workflow.add_node("consent_check", self._consent_check_node)
        workflow.add_node("collect_role_info", self._role_clarification_node)
        workflow.add_node("generate_ticket", self._generate_ticket_node)
        workflow.add_node("complete", self._complete_node)
        
        workflow.set_entry_point("ask_program_interest")
        
        workflow.add_conditional_edges(
            "ask_program_interest",
            self._route_from_program_interest,
            {
                "ask_employment_status": "ask_employment_status",
                "ask_program_interest": "ask_program_interest",
                "__end__": END
            }
        )
        
        workflow.add_conditional_edges(
            "ask_employment_status",
            self._route_from_employment_status,
            {
                "linkedin_check": "linkedin_check",
                "consent_check": "consent_check", 
                "collect_role_info": "collect_role_info",
                "ask_employment_status": "ask_employment_status",
                "__end__": END
            }
        )
        
        workflow.add_conditional_edges(
            "linkedin_check",
            self._route_from_linkedin_check,
            {
                "collect_board_info": "collect_board_info",
                "complete": "complete",
                "linkedin_check": "linkedin_check",
                "__end__": END
            }
        )
        
        workflow.add_conditional_edges(
            "collect_board_info",
            self._route_from_board_positions,
            {
                "collect_role_info": "collect_role_info"
            }
        )
        
        workflow.add_conditional_edges(
            "consent_check",
            self._route_from_consent_check,
            {
                "collect_role_info": "collect_role_info",
                "consent_check": "consent_check",
                "__end__": END
            }
        )
        
        workflow.add_conditional_edges(
            "collect_role_info",
            self._route_from_role_clarification,
            {
                "generate_ticket": "generate_ticket",
                "collect_role_info": "collect_role_info"
            }
        )
        
        workflow.add_edge("generate_ticket", "complete")
        workflow.add_edge("complete", END)
        
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
                    response_message="",
                    wants_program_info=existing_session.get("wants_program_info", False),
                    employment_status=existing_session.get("employment_status", ""),
                    linkedin_profile_updated=existing_session.get("linkedin_profile_updated", False),
                    board_positions=existing_session.get("board_positions", ""),
                    consent_signed=existing_session.get("consent_signed", False),
                    role_clarification=existing_session.get("role_clarification", {})
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
                    response_message="",
                    wants_program_info=False,
                    employment_status="",
                    linkedin_profile_updated=False,
                    board_positions="",
                    consent_signed=False,
                    role_clarification={}
                )
            
            result = await self.workflow.ainvoke(state, config={"recursion_limit": 5})
            
            response_message = result.get("response_message", "I'm here to help with your membership enrollment.")
            
            existing_messages = existing_session.get("messages", []) if existing_session else []
            new_messages = existing_messages + [
                {"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()},
                {"role": "assistant", "content": response_message, "timestamp": datetime.utcnow().isoformat()}
            ]
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "messages": new_messages,
                "current_step": result["current_step"],
                "collected_data": result["collected_data"],
                "is_complete": result["is_complete"],
                "ticket_generated": result["ticket_generated"],
                "wants_program_info": result.get("wants_program_info", False),
                "employment_status": result.get("employment_status", ""),
                "linkedin_profile_updated": result.get("linkedin_profile_updated", False),
                "board_positions": result.get("board_positions", ""),
                "consent_signed": result.get("consent_signed", False),
                "role_clarification": result.get("role_clarification", {}),
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
    



    


    async def _start_node(self, state: EnrollmentState) -> EnrollmentState:
        """Initial welcome node"""
        message = "Welcome! Would you like to learn more about our Members Program?"
        state["response_message"] = message
        state["current_step"] = "ask_program_interest"
        return state

    async def _ask_program_interest_node(self, state: EnrollmentState) -> EnrollmentState:
        """Q1: Ask if user wants to learn about Members Program"""
        last_user_message = state.get("last_user_message", "").lower()
        
        if state.get("current_step") == "start":
            message = "Welcome! Would you like to learn more about our Members Program?"
            state["response_message"] = message
            state["current_step"] = "ask_program_interest"
            return state
        
        # Process user response to program interest question
        elif state.get("current_step") == "ask_program_interest" and last_user_message.strip():
            if any(word in ["yes", "y", "yeah", "yep"] for word in last_user_message.split()):
                state["wants_program_info"] = True
                state["current_step"] = "ask_employment_status"
                message = "Great! Here's more information about our Members Program: https://services.glgresearch.com/council-members/member-programs?lang=en\n\nNow, what is your current employment status?\nA. Self-Employed\nB. Advisor\nC. Contractor\nD. Full Time Employee\n\nPlease choose A, B, C, or D."
                state["response_message"] = message
            elif any(word in ["no", "n", "nope", "nah"] for word in last_user_message.split()):
                state["wants_program_info"] = False
                state["current_step"] = "ask_employment_status"
                message = "No problem! What is your current employment status?\nA. Self-Employed\nB. Advisor\nC. Contractor\nD. Full Time Employee\n\nPlease choose A, B, C, or D."
                state["response_message"] = message
            else:
                message = "Please answer yes or no: Would you like to learn more about our Members Program?"
                state["response_message"] = message
        
        return state

    async def _ask_employment_status_node(self, state: EnrollmentState) -> EnrollmentState:
        """Q2: Ask employment status with 4-way branching"""
        last_user_message = state.get("last_user_message", "").lower()
        
        if not state.get("employment_status") and state["current_step"] != "ask_employment_status":
            message = "What is your current employment status?\nA. Self-Employed\nB. Advisor\nC. Contractor\nD. Full Time Employee\n\nPlease choose A, B, C, or D."
            state["response_message"] = message
            state["current_step"] = "ask_employment_status"
            return state
        
        # Process user response to employment status question (only if employment_status is not set)
        if not state.get("employment_status") and state["current_step"] == "ask_employment_status":
            if ("a" in last_user_message and len(last_user_message) < 10) or "self" in last_user_message or "self-employed" in last_user_message:
                state["employment_status"] = "self_employed"
                message = "Great! Since you're self-employed, I need to ask: Are your LinkedIn and GLG profiles up to date?"
                state["response_message"] = message
            elif ("b" in last_user_message and len(last_user_message) < 10) or "advisor" in last_user_message:
                state["employment_status"] = "advisor"
                message = "Thank you! As an advisor, I need to collect some additional information about your role."
                state["response_message"] = message
            elif ("c" in last_user_message and len(last_user_message) < 10) or "contractor" in last_user_message:
                state["employment_status"] = "contractor"
                message = "Thank you! As a contractor, I need to collect some additional information about your role."
                state["response_message"] = message
            elif ("d" in last_user_message and len(last_user_message) < 10) or "full" in last_user_message or "employee" in last_user_message:
                state["employment_status"] = "full_time_employee"
                message = "Thank you! As a full-time employee, I need to ask: Do you have a consent signed by an authorized person at your organization using the recommended language?\n\nFor more information: https://services.glgresearch.com/council-members/member-programs?lang=en"
                state["response_message"] = message
            else:
                message = "Please choose A (Self-Employed), B (Advisor), C (Contractor), or D (Full Time Employee)."
                state["response_message"] = message
        
        return state

    async def _linkedin_check_node(self, state: EnrollmentState) -> EnrollmentState:
        """Q3A: Check LinkedIn profile for self-employed users"""
        last_user_message = state.get("last_user_message", "").lower()
        
        if state.get("linkedin_profile_updated") is None:
            if not state.get("response_message") or "LinkedIn" not in state.get("response_message", ""):
                message = "Are your LinkedIn and GLG profiles up to date?"
                state["response_message"] = message
                return state
            
            # Process the user's response
            if "yes" in last_user_message or "y" in last_user_message:
                state["linkedin_profile_updated"] = True
                state["current_step"] = "collect_board_info"
                message = "Great! Please share your Board of Directors positions (if any). Include:\n- Designation/Title (Non-Executive/Executive)\n- Organization name\n- Start Date (MM/YY)\n- End Date (MM/YY) if applicable\n\nIf you don't have any board positions, please type 'None'."
                state["response_message"] = message
            elif "no" in last_user_message or "n" in last_user_message:
                state["linkedin_profile_updated"] = False
                state["current_step"] = "complete"
                message = "Please update your profiles first. You can update your LinkedIn profile at linkedin.com and your GLG profile in your account settings. Once updated, please restart the enrollment process."
                state["response_message"] = message
                state["is_complete"] = True
            else:
                message = "Please answer yes or no: Are your LinkedIn and GLG profiles up to date?"
                state["response_message"] = message
        
        return state

    async def _board_positions_node(self, state: EnrollmentState) -> EnrollmentState:
        """Q4A: Collect board positions for self-employed users"""
        last_user_message = state.get("last_user_message", "")
        
        if not state.get("board_positions") and not state.get("response_message"):
            message = "Great! Please share your Board of Directors positions (if any). Include:\n- Designation/Title (Non-Executive/Executive)\n- Organization name\n- Start Date (MM/YY)\n- End Date (MM/YY) if applicable\n\nIf you don't have any board positions, please type 'None'."
            state["response_message"] = message
            return state
        
        if not state.get("board_positions") and last_user_message.strip():
            state["board_positions"] = last_user_message.strip()
            state["current_step"] = "collect_role_info"
            message = "Thank you! Now I need to collect some additional information about your role."
            state["response_message"] = message
        
        return state

    async def _consent_check_node(self, state: EnrollmentState) -> EnrollmentState:
        """Q3D: Check consent for full-time employees"""
        last_user_message = state.get("last_user_message", "").lower()
        
        if state.get("consent_signed") is None:
            if not state.get("response_message") or "consent" not in state.get("response_message", ""):
                message = "Do you have a consent signed by an authorized person at your organization using the recommended language?\n\nFor more information: https://services.glgresearch.com/council-members/member-programs?lang=en"
                state["response_message"] = message
                return state
            
            # Process the user's response
            if "yes" in last_user_message or "y" in last_user_message:
                state["consent_signed"] = True
                state["current_step"] = "collect_role_info"
                message = "Excellent! Now I need to collect some additional information about your role."
                state["response_message"] = message
            elif "no" in last_user_message or "n" in last_user_message:
                state["consent_signed"] = False
                state["current_step"] = "collect_role_info"
                message = "I understand. Let me collect some information about your role."
                state["response_message"] = message
            else:
                message = "Please answer yes or no: Do you have a consent signed by an authorized person at your organization?"
                state["response_message"] = message
        
        return state

    async def _role_clarification_node(self, state: EnrollmentState) -> EnrollmentState:
        """Role Clarification Macro - collect comprehensive employment information"""
        last_user_message = state.get("last_user_message", "")
        role_data = state.get("role_clarification", {})
        
        role_questions = [
            ("company", "What is your company name?"),
            ("role_title", "What is your role/title?"),
            ("start_date", "What is your start date? (MM/DD/YYYY)"),
            ("end_date", "What is your end date? (MM/DD/YYYY or 'Current' if ongoing)"),
            ("nature_of_association", f"What is your nature of association? ({state.get('employment_status', 'Unknown')})"),
            ("work_schedule", "Are you part-time or full-time?"),
            ("hours_per_week", "Approximately how many hours per week do you work?"),
            ("employee_status", "What is your employee status? (1099, W-2, etc.)"),
            ("benefits_eligible", "Are you benefits eligible? (Y/N)")
        ]
        
        if last_user_message.strip():
            for field, question in role_questions:
                if field not in role_data:
                    role_data[field] = last_user_message.strip()
                    state["role_clarification"] = role_data
                    break
        
        if len(role_data) >= len(role_questions):
            state["current_step"] = "generate_ticket"
            message = "Thank you for providing all the information! I'm now generating your membership ticket."
            state["response_message"] = message
            return state
        
        # Ask the next question
        for field, question in role_questions:
            if field not in role_data:
                state["response_message"] = question
                return state
        
        state["current_step"] = "generate_ticket"
        message = "Thank you for providing all the information! I'm now generating your membership ticket."
        state["response_message"] = message
        
        return state



    async def _generate_ticket_node(self, state: EnrollmentState) -> EnrollmentState:
        """Generate membership ticket with all collected data"""
        try:
            member_details = {
                **state["collected_data"],
                "employment_status": state.get("employment_status"),
                "wants_program_info": state.get("wants_program_info"),
                "linkedin_profile_updated": state.get("linkedin_profile_updated"),
                "board_positions": state.get("board_positions"),
                "consent_signed": state.get("consent_signed"),
                "role_clarification": state.get("role_clarification", {})
            }
            
            ticket_data = {
                "ticket_id": str(uuid.uuid4()),
                "subject": f"MP Enrollment - {state.get('employment_status', 'Unknown')} - {member_details.get('role_clarification', {}).get('company', 'Unknown')}",
                "description": f"New membership enrollment request with employment status: {state.get('employment_status', 'Unknown')}",
                "category": "MP",
                "assignee": "MSA",  # Changed from "membership-team" to "MSA" as per flowchart
                "priority": "normal",
                "status": "open",
                "requester_email": member_details.get("email", ""),
                "member_details": member_details,
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
            state["is_complete"] = True
            
            message = f"Perfect! Your membership enrollment ticket (ID: {ticket_data['ticket_id'][:8]}...) has been created and assigned to MSA. Your enrollment is now being processed."
            state["response_message"] = message
            
        except Exception as e:
            logging.error(f"Ticket generation error: {str(e)}")
            message = "I encountered an issue generating your ticket. Please try again or contact support."
            state["response_message"] = message
        
        return state












    
    async def _generate_ticket_logic(self, state: EnrollmentState):
        """Generate ticket logic extracted from the node"""
        try:
            member_details = {
                **state["collected_data"],
                "employment_status": state.get("employment_status"),
                "wants_program_info": state.get("wants_program_info"),
                "linkedin_profile_updated": state.get("linkedin_profile_updated"),
                "board_positions": state.get("board_positions"),
                "consent_signed": state.get("consent_signed"),
                "role_clarification": state.get("role_clarification", {})
            }
            
            company_name = state.get("role_clarification", {}).get("company", "Unknown")
            
            ticket_data = {
                "ticket_id": str(uuid.uuid4()),
                "subject": f"MP Enrollment - {state.get('employment_status', 'Unknown')} - {company_name}",
                "description": f"New membership enrollment request with employment status: {state.get('employment_status', 'Unknown')}",
                "category": "MP",
                "assignee": "MSA",
                "priority": "normal",
                "status": "open",
                "requester_email": member_details.get("email", ""),
                "member_details": member_details,
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
            state["is_complete"] = True
            
            message = f"Perfect! Your membership enrollment ticket (ID: {ticket_data['ticket_id'][:8]}...) has been created and assigned to MSA. Your enrollment is now being processed."
            state["response_message"] = message
            
        except Exception as e:
            logging.error(f"Ticket generation error: {str(e)}")
            message = "I encountered an issue generating your ticket. Please try again or contact support."
            state["response_message"] = message
    

    

    

    
    async def _complete_node(self, state: EnrollmentState) -> EnrollmentState:
        if state.get("current_step") == "complete" and state.get("ticket_generated", False):
            state["is_complete"] = True
            if not state.get("response_message"):
                state["response_message"] = "Your membership enrollment is complete! You can download a summary of your enrollment or view your ticket details. Is there anything else I can help you with?"
        return state
    
    def _route_from_start(self, state: EnrollmentState) -> str:
        """Route from start node"""
        return "ask_program_interest"
    
    def _route_from_program_interest(self, state: EnrollmentState) -> str:
        """Route from program interest question"""
        current_step = state.get("current_step")
        wants_program_info = state.get("wants_program_info")
        
        if current_step == "ask_employment_status":
            return "ask_employment_status"
        
        if wants_program_info is not None:
            return "ask_employment_status"
        
        return "ask_program_interest"
    
    def _route_from_employment_status(self, state: EnrollmentState) -> str:
        """Route based on employment status (4-way branching)"""
        employment_status = state.get("employment_status")
        
        if employment_status == "self_employed":
            return "linkedin_check"
        elif employment_status == "full_time_employee":
            return "consent_check"
        elif employment_status in ["advisor", "contractor"]:
            return "collect_role_info"
        else:
            return "ask_employment_status"
    
    def _route_from_linkedin_check(self, state: EnrollmentState) -> str:
        """Route from LinkedIn check"""
        linkedin_updated = state.get("linkedin_profile_updated")
        
        if linkedin_updated is True:
            return "collect_board_info"
        elif linkedin_updated is False:
            return "complete"
        else:
            return "linkedin_check"
    
    def _route_from_board_positions(self, state: EnrollmentState) -> str:
        """Route from board positions"""
        return "collect_role_info"
    
    def _route_from_consent_check(self, state: EnrollmentState) -> str:
        """Route from consent check"""
        consent_signed = state.get("consent_signed")
        
        if consent_signed is not None:
            return "collect_role_info"
        else:
            return "consent_check"
    
    def _route_from_role_clarification(self, state: EnrollmentState) -> str:
        """Route from role clarification"""
        role_data = state.get("role_clarification", {})
        required_fields = ["company", "role_title", "start_date", "end_date", "nature_of_association", 
                          "work_schedule", "hours_per_week", "employee_status", "benefits_eligible"]
        
        response_msg = state.get("response_message", "")
        has_all_fields = all(field in role_data for field in required_fields)
        has_completion_message = "generating your membership ticket" in response_msg.lower()
        
        if has_all_fields or has_completion_message:
            return "generate_ticket"
        
        return "collect_role_info"


    
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
