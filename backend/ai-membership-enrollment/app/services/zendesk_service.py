from fastapi import UploadFile
import json
import csv
from typing import List, Dict, Any
import logging
from app.database.qdrant_client import QdrantManager
from app.services.openai_service import OpenAIService
import uuid

class ZendeskService:
    def __init__(self, qdrant_manager: QdrantManager):
        self.qdrant_manager = qdrant_manager
        self.openai_service = OpenAIService()
    
    async def import_datadump(self, file: UploadFile) -> int:
        try:
            content = await file.read()
            
            if file.filename.endswith('.json'):
                data = json.loads(content.decode('utf-8'))
                tickets = data if isinstance(data, list) else [data]
            elif file.filename.endswith('.csv'):
                csv_content = content.decode('utf-8').splitlines()
                reader = csv.DictReader(csv_content)
                tickets = list(reader)
            else:
                raise ValueError("Unsupported file format. Please upload JSON or CSV files.")
            
            imported_count = 0
            for ticket in tickets:
                await self._process_ticket(ticket)
                imported_count += 1
            
            logging.info(f"Successfully imported {imported_count} tickets from Zendesk datadump")
            return imported_count
            
        except Exception as e:
            logging.error(f"Zendesk datadump import error: {str(e)}")
            raise
    
    async def _process_ticket(self, ticket_data: Dict[str, Any]):
        ticket_text = f"{ticket_data.get('subject', '')} {ticket_data.get('description', '')}"
        embedding = await self.openai_service.get_embedding(ticket_text)
        
        ticket_id = ticket_data.get('id', str(uuid.uuid4()))
        
        await self.qdrant_manager.store_zendesk_ticket(
            ticket_id=str(ticket_id),
            ticket_data=ticket_data,
            embedding=embedding
        )
    
    async def get_tickets(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return await self.qdrant_manager.get_zendesk_tickets(limit=limit, offset=offset)
    
    def create_sample_datadump(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "12345",
                "subject": "Membership Enrollment Question",
                "description": "User asking about premium membership benefits",
                "status": "open",
                "priority": "normal",
                "requester_email": "user@example.com",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "tags": ["membership", "enrollment", "premium"]
            },
            {
                "id": "12346",
                "subject": "Corporate Membership Inquiry",
                "description": "Company interested in bulk membership enrollment",
                "status": "pending",
                "priority": "high",
                "requester_email": "corporate@company.com",
                "created_at": "2024-01-16T14:20:00Z",
                "updated_at": "2024-01-16T15:45:00Z",
                "tags": ["membership", "corporate", "bulk"]
            }
        ]
