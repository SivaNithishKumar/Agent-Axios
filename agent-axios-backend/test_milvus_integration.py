"""
Test Milvus connection and CVE search service
"""
import sys
import os

# Add path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import services directly without going through __init__
from app.services.milvus_client import MilvusClient
from app.services.query_processor import QueryProcessor

def test_milvus_connection():
    """Test connecting to Milvus"""
    print("Testing Milvus connection...")
    
    config = {
        "collection_name": "vuln",
        "endpoint": "https://in03-6ad99fbc2869a71.serverless.aws-eu-central-1.cloud.zilliz.com",
        "token": os.getenv("MILVUS_TOKEN", "0c10dc02af7b90a3313e75db42c20269b25f7a2926877466b51f29e037315e336cab32756d681c6c6c666ac5c5b8e26c2aa8aba6"),
    }
    
    client = MilvusClient(config)
    
    if client.connect():
        print("✅ Successfully connected to Milvus!")
        return client
    else:
        print("❌ Failed to connect to Milvus")
        return None

def test_query_processor():
    """Test Gemini query embedding"""
    print("\nTesting Gemini query processor...")
    
    api_keys = [
        os.getenv("GEMINI_API_KEY_1", "AIzaSyDfF3GGdic0HeKcTEZ74PC5W1M1iVsMRCU"),
    ]
    
    processor = QueryProcessor(api_keys, model_name="models/embedding-001")
    
    test_query = "SQL injection vulnerability in web application"
    embedding = processor.generate_embedding(test_query)
    
    if embedding:
        print(f"✅ Successfully generated embedding! Dimension: {len(embedding)}")
        return embedding
    else:
        print("❌ Failed to generate embedding")
        return None

def test_cve_search(client, embedding):
    """Test CVE search with embedding"""
    print("\nTesting CVE search...")
    
    results = client.search_similar(
        query_vector=embedding,
        limit=5,
        similarity_threshold=0.5,
        output_fields=["cve_id", "summary", "cvss_score"]
    )
    
    if results:
        print(f"✅ Found {len(results)} CVE results!")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('cve_id', 'N/A')}")
            print(f"   Score: {result.get('score', 0):.4f}")
            print(f"   CVSS: {result.get('cvss_score', 0)}")
            print(f"   Summary: {result.get('summary', 'N/A')[:100]}...")
    else:
        print("❌ No CVE results found")
    
    return results

if __name__ == "__main__":
    print("=" * 60)
    print("Milvus CVE Search Test")
    print("=" * 60)
    
    # Test 1: Milvus connection
    client = test_milvus_connection()
    if not client:
        sys.exit(1)
    
    # Test 2: Query processor
    embedding = test_query_processor()
    if not embedding:
        sys.exit(1)
    
    # Test 3: CVE search
    results = test_cve_search(client, embedding)
    
    print("\n" + "=" * 60)
    if results:
        print("✅ All tests passed!")
    else:
        print("⚠️ Tests completed with warnings")
    print("=" * 60)
