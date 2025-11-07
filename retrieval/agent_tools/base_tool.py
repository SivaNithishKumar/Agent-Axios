"""
Base Tool Interface

All AI agent tools must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Parameter definition for a tool"""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: List[str] = None


class ToolDefinition(BaseModel):
    """Standard tool definition for AI agents"""

    name: str
    description: str
    parameters: List[ToolParameter]
    category: str
    examples: List[Dict[str, Any]] = []


class BaseTool(ABC):
    """Base class for all AI agent tools"""

    def __init__(self):
        self._initialized = False

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """
        Return the tool definition for AI agents

        Returns:
            ToolDefinition object describing the tool
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Dictionary with execution results
        """
        pass

    def initialize(self) -> bool:
        """
        Initialize the tool (optional)

        Returns:
            True if initialization successful
        """
        self._initialized = True
        return True

    def cleanup(self):
        """Cleanup resources (optional)"""
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize parameters

        Args:
            parameters: Input parameters

        Returns:
            Validated parameters

        Raises:
            ValueError: If parameters are invalid
        """
        definition = self.get_definition()
        validated = {}

        # Check required parameters
        for param_def in definition.parameters:
            param_name = param_def.name
            if param_def.required and param_name not in parameters:
                if param_def.default is not None:
                    validated[param_name] = param_def.default
                else:
                    raise ValueError(f"Required parameter missing: {param_name}")
            elif param_name in parameters:
                validated[param_name] = parameters[param_name]
            elif param_def.default is not None:
                validated[param_name] = param_def.default

        return validated

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool definition to dictionary format

        Returns:
            Dictionary representation of the tool
        """
        definition = self.get_definition()
        return {
            "name": definition.name,
            "description": definition.description,
            "category": definition.category,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "enum": p.enum,
                }
                for p in definition.parameters
            ],
            "examples": definition.examples,
        }
