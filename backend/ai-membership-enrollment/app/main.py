from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
from app.database.qdrant_client import QdrantManager
from app.workflows.enrollment_workflow import EnrollmentWorkflow
from app.services.zendesk_service import ZendeskService
from app.schemas.enrollment import ChatRequest, ChatResponse, SessionResponse, TicketResponse
import uuid
import logging

load_dotenv()

app = FastAPI(title="AI Membership Enrollment", version="1.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

qdrant_manager = QdrantManager()
enrollment_workflow = EnrollmentWorkflow(qdrant_manager)
zendesk_service = ZendeskService(qdrant_manager)

@app.on_event("startup")
async def startup_event():
    await qdrant_manager.initialize()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await enrollment_workflow.process_message(
            session_id=request.session_id,
            message=request.message,
            user_id=request.user_id
        )
        return response
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    try:
        session_data = await qdrant_manager.get_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionResponse(**session_data)
    except Exception as e:
        logging.error(f"Session retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ticket/{session_id}", response_model=TicketResponse)
async def get_ticket(session_id: str):
    try:
        ticket_data = await qdrant_manager.get_ticket_data(session_id)
        if not ticket_data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return TicketResponse(**ticket_data)
    except Exception as e:
        logging.error(f"Ticket retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/summary/{session_id}")
async def get_summary(session_id: str):
    try:
        pdf_path = await enrollment_workflow.generate_pdf_summary(session_id)
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Summary not found")
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"enrollment_summary_{session_id}.pdf"
        )
    except Exception as e:
        logging.error(f"Summary generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zendesk/datadump")
async def import_zendesk_datadump(file: UploadFile = File(...)):
    try:
        result = await zendesk_service.import_datadump(file)
        return {"message": "Datadump imported successfully", "imported_count": result}
    except Exception as e:
        logging.error(f"Zendesk datadump import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/zendesk/tickets")
async def get_zendesk_tickets(limit: int = 50, offset: int = 0):
    try:
        tickets = await zendesk_service.get_tickets(limit=limit, offset=offset)
        return {"tickets": tickets, "total": len(tickets)}
    except Exception as e:
        logging.error(f"Zendesk tickets retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zendesk/ticket")
async def create_zendesk_ticket(ticket_data: dict):
    return {"message": "Zendesk real-time API integration - Coming Soon", "ticket_id": str(uuid.uuid4())}
