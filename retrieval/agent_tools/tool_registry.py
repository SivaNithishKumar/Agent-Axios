"""
Tool Registry

Central registry for all AI agent tools.
"""

from typing import Dict, List, Any
import logging

from .base_tool import BaseTool
from .cve_retrieval_tool import CVERetrievalTool
from .codebase_indexing_tool import CodebaseIndexingTool
from .analysis_orchestrator import AnalysisOrchestratorTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing AI agent tools"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools"""
        self.register_tool("cve_retrieval", CVERetrievalTool())
        self.register_tool("codebase_indexing", CodebaseIndexingTool())
        # Register orchestrator tool last
        try:
            self.register_tool("analysis_orchestrator", AnalysisOrchestratorTool())
        except Exception:
            logger.exception("Failed to register analysis_orchestrator tool")

    def register_tool(self, name: str, tool: BaseTool):
        """
        Register a new tool

        Args:
            name: Tool name
            tool: Tool instance
        """
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> BaseTool:
        """
        Get a tool by name

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """Get list of registered tool names"""
        return list(self.tools.keys())

    def get_all_definitions(self) -> List[Dict[str, Any]]:
        """
        Get definitions for all registered tools

        Returns:
            List of tool definitions
        """
        return [tool.to_dict() for tool in self.tools.values()]

    def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all tools

        Returns:
            Dictionary mapping tool names to initialization status
        """
        results = {}
        for name, tool in self.tools.items():
            try:
                results[name] = tool.initialize()
                logger.info(f"Initialized tool '{name}': {results[name]}")
            except Exception as e:
                logger.error(f"Failed to initialize tool '{name}': {str(e)}")
                results[name] = False
        return results

    def cleanup_all(self):
        """Cleanup all tools"""
        for name, tool in self.tools.items():
            try:
                tool.cleanup()
                logger.info(f"Cleaned up tool: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up tool '{name}': {str(e)}")

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution results
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}

        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return {"error": str(e)}


# Global registry instance
_global_registry = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def get_all_tools() -> List[Dict[str, Any]]:
    """
    Get all tool definitions

    Returns:
        List of tool definitions in dictionary format
    """
    registry = get_registry()
    return registry.get_all_definitions()


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Execute a tool from the global registry

    Args:
        tool_name: Name of the tool
        **kwargs: Tool parameters

    Returns:
        Tool execution results
    """
    registry = get_registry()
    return registry.execute_tool(tool_name, **kwargs)
