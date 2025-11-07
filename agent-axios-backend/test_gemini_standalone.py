"""
Standalone test for Gemini embedding generation
"""
import os
import time
import google.generativeai as genai

# Gemini API configuration
api_keys = [
    os.getenv("GEMINI_API_KEY_1", "AIzaSyDfF3GGdic0HeKcTEZ74PC5W1M1iVsMRCU"),
    os.getenv("GEMINI_API_KEY_2", "AIzaSyDtRxzdQ1RLZNH2KSMtsNWP8ZKyIrtDBUo"),
]

def test_embedding():
    """Test Gemini embedding generation"""
    print("Testing Gemini embedding generation...")
    
    # Configure API
    genai.configure(api_key=api_keys[0])
    
    test_query = "SQL injection vulnerability in web application"
    
    try:
        print(f"Generating embedding for: '{test_query}'")
        
        start_time = time.time()
        response = genai.embed_content(
            model="models/embedding-001",
            content=test_query,
            task_type="retrieval_query",
        )
        elapsed = time.time() - start_time
        
        embedding = response["embedding"]
        
        print(f"✅ Successfully generated embedding!")
        print(f"   Dimension: {len(embedding)}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   First 5 values: {embedding[:5]}")
        
        return embedding
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {str(e)}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("Gemini Embedding Test")
    print("=" * 60 + "\n")
    
    embedding = test_embedding()
    
    print("\n" + "=" * 60)
    if embedding:
        print("✅ Test passed!")
    else:
        print("❌ Test failed!")
    print("=" * 60)
