"""
AI Agent Server

FastAPI server that exposes AI agent tools through REST API.
AI agents can call these endpoints to execute tools.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_tools import get_all_tools, execute_tool, get_registry
from config import API_HOST, API_PORT, API_DEBUG, LOGGING_CONFIG

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    handlers=[logging.FileHandler(LOGGING_CONFIG["file"]), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global registry
tool_registry = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global tool_registry

    # Startup
    logger.info("Starting AI Agent Tool Server...")
    tool_registry = get_registry()

    # Initialize all tools
    init_results = tool_registry.initialize_all()
    logger.info(f"Tool initialization results: {init_results}")

    yield

    # Shutdown
    logger.info("Shutting down AI Agent Tool Server...")
    if tool_registry:
        tool_registry.cleanup_all()


# Create FastAPI app
app = FastAPI(
    title="AI Agent Tool Server",
    description="Server providing AI agent tools for CVE retrieval and codebase indexing",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ToolExecutionRequest(BaseModel):
    """Request to execute a tool"""

    tool: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(
        {}, description="Parameters for the tool execution"
    )


class ToolListResponse(BaseModel):
    """Response containing list of available tools"""

    tools: list
    total_tools: int


# API endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AI Agent Tool Server",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/tools", response_model=ToolListResponse)
async def list_tools():
    """
    Get list of all available tools with their definitions

    Returns detailed information about each tool including:
    - Tool name and description
    - Required and optional parameters
    - Example usages
    """
    if not tool_registry:
        raise HTTPException(status_code=503, detail="Tool registry not initialized")

    tools = get_all_tools()
    return {"tools": tools, "total_tools": len(tools)}


@app.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """
    Get detailed information about a specific tool

    Args:
        tool_name: Name of the tool (e.g., 'cve_retrieval', 'codebase_indexing')
    """
    if not tool_registry:
        raise HTTPException(status_code=503, detail="Tool registry not initialized")

    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    return tool.to_dict()


@app.post("/execute")
async def execute_tool_endpoint(request: ToolExecutionRequest):
    """
    Execute a tool with given parameters

    This is the main endpoint AI agents use to execute tools.

    Example request:
    ```json
    {
      "tool": "cve_retrieval",
      "parameters": {
        "action": "search_by_text",
        "query": "SQL injection",
        "limit": 10
      }
    }
    ```
    """
    if not tool_registry:
        raise HTTPException(status_code=503, detail="Tool registry not initialized")

    try:
        logger.info(f"Executing tool: {request.tool} with params: {request.parameters}")

        result = execute_tool(request.tool, **request.parameters)

        if "error" in result:
            logger.error(f"Tool execution error: {result['error']}")
            return {
                "success": False,
                "tool": request.tool,
                "error": result["error"],
                "result": None,
            }

        return {
            "success": result.get("success", True),
            "tool": request.tool,
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error executing tool '{request.tool}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check"""
    if not tool_registry:
        raise HTTPException(status_code=503, detail="Tool registry not initialized")

    return {
        "status": "healthy",
        "tools_available": tool_registry.list_tools(),
        "total_tools": len(tool_registry.list_tools()),
    }


def run_server():
    """Run the FastAPI server"""
    logger.info(f"Starting AI Agent Tool Server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=API_DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
