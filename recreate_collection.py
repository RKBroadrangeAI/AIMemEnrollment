#!/usr/bin/env python3
"""
Script to recreate the Qdrant collection with correct vector dimensions
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os

def recreate_collection():
    client = QdrantClient(host='localhost', port=6333)
    collection_name = "enrollment_data"
    
    try:
        client.delete_collection(collection_name)
        print(f'Deleted existing collection: {collection_name}')
    except Exception as e:
        print(f'Collection deletion (expected if not exists): {e}')
    
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        print(f'Created new collection: {collection_name} with 1536 dimensions')
        
        info = client.get_collection(collection_name)
        print(f'Collection info: {info}')
        
    except Exception as e:
        print(f'Error creating collection: {e}')

if __name__ == "__main__":
    recreate_collection()
