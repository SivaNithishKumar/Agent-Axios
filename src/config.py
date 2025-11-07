"""
Configuration module for Repository Analyzer.
Handles Azure OpenAI setup and environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from rich.console import Console

# Load environment variables
load_dotenv()

console = Console()


class Config:
    """Configuration class for Repository Analyzer."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.azure_openai_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        
        # LangSmith tracking configuration
        self.langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "Repository-Analyzer-ReAct")
        self.langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        # Set LangSmith environment variables if tracing is enabled
        if self.langsmith_tracing and self.langsmith_api_key:
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key
            os.environ["LANGSMITH_PROJECT"] = self.langsmith_project
            os.environ["LANGSMITH_ENDPOINT"] = self.langsmith_endpoint
        
        # Validate required environment variables
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate that all required configuration is present."""
        required_vars = [
            ("AZURE_OPENAI_API_KEY", self.azure_openai_api_key),
            ("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            console.print(f"[red]Missing required environment variables: {', '.join(missing_vars)}[/red]")
            console.print("[yellow]Please check your .env file and ensure all required variables are set.[/yellow]")
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    def get_azure_openai_client(self) -> AzureChatOpenAI:
        """Create and return an Azure OpenAI client."""
        try:
            client = AzureChatOpenAI(
                azure_endpoint=self.azure_openai_endpoint,
                api_key=self.azure_openai_api_key,
                api_version=self.azure_openai_api_version,
                azure_deployment=self.azure_openai_model,
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=4000,  # Reasonable limit for responses
            )
            console.print("[green]✅ Azure OpenAI client initialized successfully[/green]")
            return client
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize Azure OpenAI client: {str(e)}[/red]")
            raise
    
    def display_config(self) -> None:
        """Display current configuration (without sensitive data)."""
        console.print("\n[bold blue]🔧 Configuration Status[/bold blue]")
        console.print(f"[green]Endpoint:[/green] {self.azure_openai_endpoint}")
        console.print(f"[green]API Version:[/green] {self.azure_openai_api_version}")
        console.print(f"[green]Model:[/green] {self.azure_openai_model}")
        console.print(f"[green]API Key:[/green] {'✅ Set' if self.azure_openai_api_key else '❌ Missing'}")
        console.print(f"[green]Tavily API Key:[/green] {'✅ Set' if self.tavily_api_key else '⚠️  Not Set (web search disabled)'}")
        console.print(f"[green]LangSmith Tracking:[/green] {'✅ Enabled' if self.langsmith_tracing else '⚠️  Disabled'}")
        if self.langsmith_tracing:
            console.print(f"[green]LangSmith Project:[/green] {self.langsmith_project}")
            console.print(f"[green]LangSmith API Key:[/green] {'✅ Set' if self.langsmith_api_key else '❌ Missing'}")
        console.print()


# Global configuration instance
config = Config()

# Convenience function to get the LLM client
def get_llm() -> AzureChatOpenAI:
    """Get the Azure OpenAI LLM client."""
    return config.get_azure_openai_client()

# Convenience function to get full config dict
def get_config() -> dict:
    """Get configuration dictionary with LLM and API keys."""
    return {
        'llm': config.get_azure_openai_client(),
        'tavily_api_key': config.tavily_api_key,
        'azure_endpoint': config.azure_openai_endpoint,
        'model': config.azure_openai_model
    }


if __name__ == "__main__":
    # Test configuration
    config.display_config()
    try:
        llm = get_llm()
        console.print("[green]✅ Configuration test successful![/green]")
    except Exception as e:
        console.print(f"[red]❌ Configuration test failed: {str(e)}[/red]")
