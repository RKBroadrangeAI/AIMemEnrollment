from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
import os
from typing import List, Dict, Any
import logging

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.is_configured = self.api_key and self.api_key != "your_openai_api_key_here"
        
        if self.is_configured:
            self.chat_model = ChatOpenAI(
                model="gpt-4",
                temperature=0.7,
                api_key=self.api_key
            )
            
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                api_key=self.api_key
            )
        else:
            logging.warning("OpenAI API key not configured - AI features will use fallback responses")
            self.chat_model = None
            self.embeddings = None
    
    async def generate_response(self, system_prompt: str, user_message: str, context: Dict[str, Any] = None) -> str:
        if not self.is_configured:
            return "Thank you for your message. I'm currently in demo mode - please configure OpenAI API key for full AI functionality."
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            if context:
                context_message = f"Context: {context}"
                messages.insert(1, SystemMessage(content=context_message))
            
            response = await self.chat_model.ainvoke(messages)
            return response.content
        except Exception as e:
            logging.error(f"OpenAI generation error: {str(e)}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        if not self.is_configured:
            return [0.0] * 1536
        
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logging.error(f"OpenAI embedding error: {str(e)}")
            raise
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.is_configured:
            return [[0.0] * 1536 for _ in texts]
        
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logging.error(f"OpenAI batch embedding error: {str(e)}")
            raise
