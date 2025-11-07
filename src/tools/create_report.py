"""
Create Report Tool for generating comprehensive technical reports using Azure OpenAI GPT-4.1.
Takes aggregated analysis context and creates a detailed, readable technical summary.
"""

import os
from typing import Optional
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import get_llm

console = Console()


class ReportGenerator:
    """Class to generate technical reports using Azure OpenAI."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.llm = None
        self.system_prompt = """You are an expert technical analyst and security vulnerability specialist. Your task is to analyze repository data and create comprehensive technical reports optimized for CVE vulnerability matching and security analysis.

PRIMARY OBJECTIVE:
Generate reports that enable:
1. Semantic similarity matching against CVE vulnerability summaries
2. Tag-based filtering for vulnerability retrieval
3. Systematic security assessment

CRITICAL REQUIREMENTS:

A. TECHNOLOGY INVENTORY (with exact versions):
- List ALL technologies, frameworks, libraries with specific version numbers
- Include programming languages, web frameworks, databases, authentication systems
- Specify dependency versions from requirements.txt, package.json, etc.
- Format: "Technology: Version" (e.g., "Flask: 2.3.0", "SQLAlchemy: 1.4.25")

B. SECURITY SURFACE ANALYSIS:
- Identify all security-relevant components: web endpoints, authentication, authorization, input validation, database access, file operations, API integrations
- Describe how data flows through the system
- Identify potential attack surfaces (user inputs, API endpoints, file uploads, etc.)
- Use security terminology that matches CVE descriptions (e.g., "SQL query construction", "password hashing", "session management")

C. VULNERABILITY CATEGORIES & CWE MAPPING:
- Identify potential vulnerability types relevant to the codebase
- Map to CWE categories: SQL Injection (CWE-89), XSS (CWE-79), CSRF (CWE-352), Buffer Overflow (CWE-119), Authentication Issues (CWE-287), etc.
- Describe specific code patterns that could be vulnerable

D. ATTACK VECTOR CLASSIFICATION:
- Categorize by CVSS attack vectors:
  * Network (AV:N): Remotely exploitable
  * Adjacent (AV:A): Local network access
  * Local (AV:L): Local system access
  * Physical (AV:P): Physical access required

E. STRUCTURED METADATA FOR CVE MATCHING:
Provide machine-readable tags in a dedicated section:
- TECHNOLOGIES: [framework1, framework2, library1, ...]
- VERSIONS: [tech1:version1, tech2:version2, ...]
- SECURITY_COMPONENTS: [authentication, authorization, input_validation, ...]
- VULNERABILITY_KEYWORDS: [sql, injection, xss, csrf, buffer_overflow, ...]
- ATTACK_SURFACES: [web_api, database, file_system, network, ...]
- CWE_RELEVANT: [CWE-89, CWE-79, CWE-352, ...]
- LANGUAGES: [python, javascript, ...]

F. TECHNICAL DESCRIPTIONS FOR SEMANTIC MATCHING:
- Write detailed descriptions of security-critical functionality using terminology similar to CVE summaries
- Example: "The application accepts user input for SQL query construction without proper sanitization in the search functionality"
- Describe authentication mechanisms, data validation approaches, privilege management

REPORT STRUCTURE:
1. Executive Summary
2. Technology Inventory & Versions
3. Security Surface Analysis
4. Component-Level Security Assessment
5. Potential Vulnerability Categories (CWE-Mapped)
6. Attack Vector Analysis
7. Structured Metadata for CVE Matching
8. Detailed Security Observations
9. Recommendations
10. Conclusion

Make the report detailed, security-focused, and optimized for vulnerability database matching."""
    
    def initialize_llm(self):
        """Initialize the Azure OpenAI client."""
        if self.llm is None:
            try:
                self.llm = get_llm()
                console.print("[green]✅ Azure OpenAI client initialized[/green]")
            except Exception as e:
                console.print(f"[red]❌ Failed to initialize Azure OpenAI: {str(e)}[/red]")
                raise
    
    def generate_report(self, analysis_context: str, repo_path: str = None) -> str:
        """Generate a comprehensive technical report using Azure OpenAI."""
        console.print("[blue]🤖 Generating technical report with Azure OpenAI GPT-4.1...[/blue]")
        
        try:
            # Initialize LLM if not already done
            self.initialize_llm()
            
            # Prepare the user prompt
            user_prompt = f"""Please analyze the following repository data and create a comprehensive technical report:

REPOSITORY PATH: {repo_path or 'Not specified'}

ANALYSIS DATA:
{analysis_context}

Please create a detailed technical report following the specified structure. Focus on providing valuable insights and actionable recommendations based on the analysis data."""
            
            # Create messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Generate the report
            console.print("[blue]🔄 Calling Azure OpenAI API...[/blue]")
            response = self.llm.invoke(messages)
            
            # Extract the report content
            if hasattr(response, 'content'):
                report_content = response.content
            else:
                report_content = str(response)
            
            console.print("[green]✅ Technical report generated successfully[/green]")
            return report_content
            
        except Exception as e:
            console.print(f"[red]❌ Error generating report: {str(e)}[/red]")
            return f"""# Technical Report Generation Error

An error occurred while generating the technical report:

**Error**: {str(e)}

**Analysis Context Summary**: 
{analysis_context[:500]}...

Please check the Azure OpenAI configuration and try again."""
    
    def generate_report_with_context(self, repo_path: Optional[str] = None) -> str:
        """Generate report by first creating analysis context, then generating report."""
        try:
            # Import the summary context generator
            from .summary_context import summary_generator
            
            # Use provided path or current directory
            if repo_path is None:
                repo_path = os.getcwd()
            
            console.print(f"[blue]📊 Creating analysis context for: {repo_path}[/blue]")
            
            # Generate analysis summary
            analysis_summary = summary_generator.aggregate_analysis_results(repo_path)
            analysis_context = summary_generator.format_for_llm(analysis_summary)
            
            # Generate the report
            report = self.generate_report(analysis_context, repo_path)
            
            return report
            
        except Exception as e:
            console.print(f"[red]❌ Error in report generation workflow: {str(e)}[/red]")
            return f"""# Technical Report Generation Error

An error occurred during the report generation workflow:

**Error**: {str(e)}

**Repository Path**: {repo_path}

Please ensure all analysis tools are working correctly and try again."""
    
    def save_report(self, report_content: str, output_path: str) -> bool:
        """Save the generated report to a file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            console.print(f"[green]✅ Report saved to {output_path}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error saving report: {str(e)}[/red]")
            return False


# Global generator instance
report_generator = ReportGenerator()


@tool
def create_technical_report_tool(repo_path: Optional[str] = None, analysis_context: Optional[str] = None) -> str:
    """
    Generate a comprehensive technical report using Azure OpenAI GPT-4.1.
    
    Args:
        repo_path: Optional path to repository. If not provided, uses current directory.
        analysis_context: Optional pre-generated analysis context. If not provided, will generate it.
    
    Returns:
        Comprehensive technical report generated by Azure OpenAI based on repository analysis.
    """
    try:
        if analysis_context:
            # Use provided analysis context
            if repo_path is None:
                repo_path = os.getcwd()
            report = report_generator.generate_report(analysis_context, repo_path)
        else:
            # Generate analysis context and then create report
            report = report_generator.generate_report_with_context(repo_path)
        
        return report
        
    except Exception as e:
        return f"Error creating technical report: {str(e)}"


@tool
def save_report_tool(report_content: str, output_path: str) -> str:
    """
    Save a generated report to a file.
    
    Args:
        report_content: The report content to save.
        output_path: Path where to save the report file.
    
    Returns:
        Success or error message.
    """
    try:
        success = report_generator.save_report(report_content, output_path)
        if success:
            return f"Report successfully saved to {output_path}"
        else:
            return f"Failed to save report to {output_path}"
    except Exception as e:
        return f"Error saving report: {str(e)}"


if __name__ == "__main__":
    # Test the tool
    console.print("[bold blue]Testing Report Generator Tool[/bold blue]")
    
    # Test with current directory
    test_path = "/home/ubuntu/sem"
    console.print(f"\n[yellow]Testing report generation for: {test_path}[/yellow]")
    
    try:
        # Generate a simple test report
        test_context = """# Test Repository Analysis

## Project Overview
- Primary Language: Python
- Project Type: LangChain Repository Analyzer
- Total Files: 15
- Total Dependencies: 18

## Key Features
- Repository loading and analysis
- Dependency extraction
- Framework detection
- Technical report generation

This is a test analysis context for report generation."""
        
        report = report_generator.generate_report(test_context, test_path)
        
        print("\n" + "="*50)
        print("GENERATED REPORT PREVIEW:")
        print("="*50)
        print(report[:1000] + "..." if len(report) > 1000 else report)
        
    except Exception as e:
        console.print(f"[red]❌ Test failed: {str(e)}[/red]")
