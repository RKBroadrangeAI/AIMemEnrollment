
import sys
sys.path.append('.')
from qdrant_client import QdrantClient
import os

try:
    host = os.getenv('QDRANT_HOST', 'localhost')
    port = int(os.getenv('QDRANT_PORT', '6333'))
    client = QdrantClient(host=host, port=port)
    collections = client.get_collections()
    print(f'Available collections: {[col.name for col in collections.collections]}')
    
    for col in collections.collections:
        if col.name == 'enrollment_data':
            print(f'Collection exists: {col.name}')
            collection_info = client.get_collection('enrollment_data')
            print(f'Current vector size: {collection_info.config.params.vectors.size}')
            print(f'Distance metric: {collection_info.config.params.vectors.distance}')
            print('Collection needs to be recreated with 1536 dimensions')
            break
    else:
        print('enrollment_data collection does not exist - will be created with correct dimensions')
except Exception as e:
    print(f'Error checking collection: {e}')

