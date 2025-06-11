from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import os
import uuid
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

class QdrantManager:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = "enrollment_data"
        
    async def initialize(self):
        try:
            collections = self.client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)
            
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                logging.info(f"Created collection: {self.collection_name}")
                
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if openai_api_key and openai_api_key != "your_openai_api_key_here":
                    await self._initialize_sample_data()
                else:
                    logging.warning("OpenAI API key not configured - skipping sample data initialization")
                    await self._initialize_sample_data_without_embeddings()
            else:
                logging.info(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logging.error(f"Failed to initialize Qdrant: {str(e)}")
            raise
    
    async def _initialize_sample_data(self):
        sample_questions = [
            "What is your full name?",
            "What is your email address?",
            "What type of membership program are you interested in?",
            "What is your company name?",
            "What is your job title?",
            "How did you hear about our program?"
        ]
        
        from app.services.openai_service import OpenAIService
        openai_service = OpenAIService()
        
        points = []
        for i, question in enumerate(sample_questions):
            embedding = await openai_service.get_embedding(question)
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "type": "question",
                    "text": question,
                    "category": "enrollment",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            points.append(point)
        
        self.client.upsert(collection_name=self.collection_name, points=points)
        logging.info("Initialized sample questions in Qdrant")
    
    async def _initialize_sample_data_without_embeddings(self):
        """Initialize sample data with dummy embeddings when OpenAI is not available"""
        sample_questions = [
            "What is your full name?",
            "What is your email address?",
            "What type of membership program are you interested in?",
            "What is your company name?",
            "What is your job title?",
            "How did you hear about our program?"
        ]
        
        points = []
        for i, question in enumerate(sample_questions):
            dummy_embedding = [0.0] * 1536
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=dummy_embedding,
                payload={
                    "type": "question",
                    "text": question,
                    "category": "enrollment",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            points.append(point)
        
        self.client.upsert(collection_name=self.collection_name, points=points)
        logging.info("Initialized sample questions in Qdrant with dummy embeddings")
    
    async def store_session_data(self, session_id: str, user_id: str, data: Dict[str, Any], embedding: List[float]):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "type": "session",
                "session_id": session_id,
                "user_id": user_id,
                "data": data,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])
    
    async def store_ticket_data(self, session_id: str, ticket_data: Dict[str, Any], embedding: List[float]):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "type": "ticket",
                "session_id": session_id,
                "ticket_data": ticket_data,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])
    
    async def store_summary_data(self, session_id: str, summary_text: str, embedding: List[float]):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "type": "summary",
                "session_id": session_id,
                "summary_text": summary_text,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])
    
    async def store_zendesk_ticket(self, ticket_id: str, ticket_data: Dict[str, Any], embedding: List[float]):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "type": "zendesk_ticket",
                "ticket_id": ticket_id,
                "data": ticket_data,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="type", match=MatchValue(value="session")),
                        FieldCondition(key="session_id", match=MatchValue(value=session_id))
                    ]
                ),
                limit=1
            )
            
            if results[0]:
                return results[0][0].payload.get("data")
            return None
        except Exception as e:
            logging.error(f"Error retrieving session data: {str(e)}")
            return None
    
    async def get_ticket_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="type", match=MatchValue(value="ticket")),
                        FieldCondition(key="session_id", match=MatchValue(value=session_id))
                    ]
                ),
                limit=1
            )
            
            if results[0]:
                return results[0][0].payload.get("ticket_data")
            return None
        except Exception as e:
            logging.error(f"Error retrieving ticket data: {str(e)}")
            return None
    
    async def get_zendesk_tickets(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value="zendesk_ticket"))]
                ),
                limit=limit,
                offset=offset
            )
            
            tickets = []
            for point in results[0]:
                tickets.append(point.payload.get("data", {}))
            return tickets
        except Exception as e:
            logging.error(f"Error retrieving Zendesk tickets: {str(e)}")
            return []
    
    async def semantic_search(self, query_vector: List[float], filter_type: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            search_filter = None
            if filter_type:
                search_filter = Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value=filter_type))]
                )
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit
            )
            
            return [{"payload": result.payload, "score": result.score} for result in results]
        except Exception as e:
            logging.error(f"Error in semantic search: {str(e)}")
            return []
