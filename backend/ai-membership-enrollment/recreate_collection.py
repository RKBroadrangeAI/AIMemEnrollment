
import sys
sys.path.append('.')
from qdrant_client import QdrantClient
import os

try:
    host = os.getenv('QDRANT_HOST', 'localhost')
    port = int(os.getenv('QDRANT_PORT', '6333'))
    client = QdrantClient(host=host, port=port)
    
    # Check if collection exists and get its configuration
    collections = client.get_collections()
    for col in collections.collections:
        if col.name == 'enrollment_data':
            collection_info = client.get_collection('enrollment_data')
            current_size = collection_info.config.params.vectors.size
            print(f'Current collection vector size: {current_size}')
            
            if current_size != 1536:
                print('Collection needs to be recreated with 1536 dimensions')
                print('Deleting existing collection...')
                client.delete_collection('enrollment_data')
                print('Collection deleted successfully')
            else:
                print('Collection already has correct dimensions')
            break
    else:
        print('Collection does not exist - will be created with correct dimensions')
        
except Exception as e:
    print(f'Error: {e}')

