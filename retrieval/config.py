"""
Configuration file for the CVE retrieval microservice
"""

import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv not installed, use system environment variables

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 5000  # API server port
API_DEBUG = False  # Set to False to disable auto-reload

# Codebase Configuration (from .env)
CODEBASE_CONFIG = {
    "codebase_path": os.getenv("CODEBASE_PATH", "F:\\Programs\\Vuln_detection\\app\\retrieval"),
    "faiss_db_path": os.getenv("FAISS_DB_PATH", "codebase_faiss_db"),
}

# MongoDB Configuration (from .env)
MONGODB_CONFIG = {
    "uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017/vanij_db"),
}

# Milvus Configuration
MILVUS_CONFIG = {
    "cluster_id": "in03-6ad99fbc2869a71",
    "cloud_region": "aws-eu-central-1",
    "endpoint": "https://in03-6ad99fbc2869a71.serverless.aws-eu-central-1.cloud.zilliz.com",
    "token": "0c10dc02af7b90a3313e75db42c20269b25f7a2926877466b51f29e037315e336cab32756d681c6c6c666ac5c5b8e26c2aa8aba6",
    "user": "krish1312",
    "password": "",
    "collection_name": "vuln",
}

# Google Gemini API Configuration
GEMINI_API_KEYS = [
    # Add your Gemini API keys here for rotation
    "AIzaSyDfF3GGdic0HeKcTEZ74PC5W1M1iVsMRCU",
    "AIzaSyDtRxzdQ1RLZNH2KSMtsNWP8ZKyIrtDBUo",
    "AIzaSyBd1fyIyu6gINkNIsIDHibq-8H2BVWYCWc",
    "AIzaSyBb0Gg_ReSx9h6v1XKBpaz8PrDEjOTs9kQ",
    "AIzaSyCla6N_yYwDtESrgmXte3HgGOhOctOCfHM",
    "AIzaSyCfsSZqF33E9rIKXl6Zyi2Krzm6GX2TgZc",
]

# Embedding Configuration
EMBEDDING_CONFIG = {
    "model_name": "gemini-embedding-001",
    "dimension": 3072,  # Updated to match actual Gemini embedding dimension
    "batch_size": 50,  # Reduced for API usage
    "max_retries": 3,
    "retry_delay": 2,
}

# Retrieval Configuration
RETRIEVAL_CONFIG = {
    "default_limit": 10,
    "max_limit": 100,
    "similarity_threshold": 0.7,
    "search_params": {"metric_type": "COSINE", "params": {"nprobe": 10}},
}

# API Response Configuration
RESPONSE_CONFIG = {
    "max_results": 50,
    "default_results": 10,
    "include_scores": True,
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/retrieval.log",
}

# Milvus Schema Configuration
MILVUS_SCHEMA = {
    "fields": [
        {"name": "id", "type": "INT64", "is_primary": True, "auto_id": True},
        {"name": "embedding", "type": "FLOAT_VECTOR", "dimension": 3072},
        {"name": "cve_id", "type": "VARCHAR", "max_length": 50},
        {"name": "summary", "type": "VARCHAR", "max_length": 10000},
        {"name": "cvss_score", "type": "FLOAT"},
        {"name": "cvss_vector", "type": "VARCHAR", "max_length": 200},
    ],
    "collection_name": "vuln",
    "description": "CVE vulnerability collection with embeddings",
}
