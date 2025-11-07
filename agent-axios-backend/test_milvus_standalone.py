"""
Standalone test for Milvus connection
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, utility

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Milvus configuration
config = {
    "collection_name": "vuln",
    "endpoint": "https://in03-6ad99fbc2869a71.serverless.aws-eu-central-1.cloud.zilliz.com",
    "token": os.getenv("MILVUS_TOKEN", "0c10dc02af7b90a3313e75db42c20269b25f7a2926877466b51f29e037315e336cab32756d681c6c6c666ac5c5b8e26c2aa8aba6"),
}

def test_connection():
    """Test Milvus connection"""
    print("Testing Milvus connection...")
    
    try:
        connections.connect(
            alias="default",
            uri=config["endpoint"],
            token=config["token"],
        )
        print("✅ Successfully connected to Milvus!")
        
        # Check collection exists
        collection_name = config["collection_name"]
        if utility.has_collection(collection_name):
            print(f"✅ Collection '{collection_name}' exists!")
            
            # Load collection
            collection = Collection(collection_name)
            collection.load()
            print(f"✅ Collection loaded successfully!")
            
            # Get collection stats
            print(f"\n📊 Collection stats:")
            print(f"   Name: {collection.name}")
            print(f"   Number of entities: {collection.num_entities}")
            
            return True
        else:
            print(f"❌ Collection '{collection_name}' not found!")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False
    finally:
        try:
            connections.disconnect("default")
        except:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("Milvus Connection Test")
    print("=" * 60 + "\n")
    
    success = test_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test passed!")
    else:
        print("❌ Test failed!")
    print("=" * 60)
