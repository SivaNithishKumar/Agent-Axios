"""
ReAct Agent for Autonomous Repository Analysis
Uses LangGraph's create_react_agent for full autonomy in tool selection and execution.
"""

import os
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langsmith import traceable
from rich.console import Console

# Import our custom tools
from react_agent_tools import ALL_TOOLS

console = Console()


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """State for the ReAct agent"""
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    repo_path: str  # Store the repository path once cloned


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are an expert repository analysis agent specializing in security-focused technical reports for CVE matching.

Your mission is to autonomously explore and analyze code repositories, then generate comprehensive technical reports.

WORKFLOW GUIDELINES (EFFICIENT - Aim for 15-20 steps total):
1. START (1 step): Clone/load the repository using clone_repository

2. EXPLORE (3-5 steps): 
   - List the root directory to understand structure
   - Search for key files (README, package.json, requirements.txt, etc.)
   - Read ONLY README and main config file (2 files maximum)

3. ANALYZE (4 steps - call these in parallel if possible):
   - detect_project_type (identifies language/type)
   - analyze_dependencies (extracts ALL dependencies - no need to read files!)
   - detect_frameworks (finds ALL frameworks - no need to read files!)
   - analyze_structure (provides structure overview - no need to explore manually!)

4. COMPLETE (1 step): 
   - Call generate_final_report immediately after step 3
   - You have all information needed from the analysis tools!

TOTAL TARGET: 10-15 steps maximum. The analysis tools do the heavy lifting!
Do NOT read source code files - the tools analyze them automatically.

AVAILABLE TOOLS:
- clone_repository: Load the repository (Git URL or local path)
- list_directory: Explore directory contents
- read_file: Read specific files (README, configs, source files)
- search_files: Find files matching patterns (*.py, package.json, etc.)
- get_file_info: Get file metadata without reading contents
- analyze_dependencies: Extract all dependencies (Python, Node.js, Java, etc.)
- detect_project_type: Identify programming language and project type
- analyze_structure: Get comprehensive structure analysis
- detect_frameworks: Identify frameworks and libraries
- tavily_search_results_json: Search the web for information
- generate_final_report: Generate the final technical report (FINAL STEP)

IMPORTANT RULES:
✅ YOU decide which tools to call and when
✅ Be EFFICIENT - gather essential information, then generate the report
✅ Read 2-3 key files (README.md, main config file, main source file)
✅ Use web search ONLY if absolutely necessary for critical unknowns
✅ Analyze dependencies and frameworks using dedicated tools (don't read every file)
✅ Generate report after you have: project overview, dependencies, frameworks, and structure
✅ The report should focus on: project overview, tech stack, dependencies, frameworks, architecture, security considerations

❌ Don't read too many files - use analysis tools instead
❌ Don't skip dependency analysis
❌ Don't explore endlessly - be decisive
❌ After analyzing dependencies, frameworks, structure, and reading 2-3 key files, GENERATE THE REPORT

ANALYSIS DEPTH (BE EFFICIENT):
Sufficient information means you have:
- Project purpose from README
- Dependencies from analyze_dependencies tool
- Frameworks from detect_frameworks tool
- Project type from detect_project_type tool
- Structure from analyze_structure tool
- Read 2-3 key files maximum (README, main config, main source file)

You DO NOT need to read every source file - use the analysis tools!
After gathering the above, GENERATE THE REPORT immediately.

REPORT REQUIREMENTS:
The final report must include:
- Project Overview (purpose, language, type)
- Technology Stack (frameworks, libraries, tools)
- Dependencies (complete list with versions)
- Architecture (structure, patterns, organization)
- Security Considerations (CVE-relevant information)
- Key Components (entry points, important modules)

START: Begin by cloning the repository, then systematically explore and analyze it.
"""


# ============================================================================
# AGENT CREATION
# ============================================================================

@traceable(
    name="Create ReAct Agent",
    run_type="chain",
    tags=["setup", "initialization"]
)
def create_repository_analysis_agent(llm: AzureChatOpenAI, tavily_api_key: str):
    """
    Create a ReAct agent for autonomous repository analysis.
    
    Args:
        llm: Azure OpenAI LLM instance
        tavily_api_key: API key for Tavily search
    
    Returns:
        Compiled LangGraph agent
    """
    console.print("[blue]🤖 Initializing ReAct Agent...[/blue]")
    
    # Initialize Tavily search tool
    web_search = TavilySearchResults(
        max_results=3,
        api_key=tavily_api_key,
        name="tavily_search_results_json",
        description="Search the web for information about technologies, frameworks, security vulnerabilities, or any other relevant information."
    )
    
    # Combine all tools
    tools = ALL_TOOLS + [web_search]
    
    console.print(f"[green]✓ Loaded {len(tools)} tools[/green]")
    for tool in tools:
        console.print(f"  - {tool.name}")
    
    # Create the ReAct agent with checkpointing
    memory = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory
    )
    
    console.print("[green]✓ ReAct agent created successfully[/green]")
    
    return agent


# ============================================================================
# AGENT EXECUTION
# ============================================================================

@traceable(
    name="Repository Analysis",
    run_type="chain",
    tags=["react-agent", "repository-analyzer", "autonomous"]
)
def run_analysis(repo_input: str, llm: AzureChatOpenAI, tavily_api_key: str) -> str:
    """
    Run the autonomous repository analysis.
    
    Args:
        repo_input: Repository URL or local path
        llm: Azure OpenAI LLM instance
        tavily_api_key: API key for Tavily search
    
    Returns:
        The generated technical report
    """
    console.print(f"\n[bold blue]🚀 Starting Autonomous Analysis[/bold blue]")
    console.print(f"[blue]📍 Target: {repo_input}[/blue]\n")
    
    # Create the agent
    agent = create_repository_analysis_agent(llm, tavily_api_key)
    
    # Create initial message
    initial_message = f"""Analyze this repository: {repo_input}

Your task is to:
1. Clone/load the repository
2. Explore its structure and contents
3. Analyze dependencies, frameworks, and technologies
4. Read 2-3 key files MAXIMUM (README + main config + one source file)
5. Generate the report immediately after step 4

CRITICAL: After you have dependencies, frameworks, structure info, and read README, 
call generate_final_report IMMEDIATELY. Do NOT read more than 3 files.
The analysis tools (analyze_dependencies, detect_frameworks, analyze_structure) 
provide all the information you need - you don't need to read every source file!

Remember: Be efficient. Gather essential info, then GENERATE THE REPORT.
"""
    
    # Run the agent with increased recursion limit
    config = {
        "configurable": {"thread_id": "repo-analysis-001"},
        "recursion_limit": 100  # Increased from default 25
    }
    
    try:
        console.print("[yellow]🤔 Agent is thinking...[/yellow]\n")
        
        # Stream the agent's execution
        final_state = None
        step_count = 0
        
        for event in agent.stream(
            {"messages": [HumanMessage(content=initial_message)]},
            config=config,
            stream_mode="values"
        ):
            step_count += 1
            messages = event.get("messages", [])
            
            if messages:
                last_message = messages[-1]
                
                # Show agent's reasoning and actions
                if hasattr(last_message, 'content') and last_message.content:
                    console.print(f"[dim]Step {step_count}:[/dim] {last_message.content[:200]}...")
                
                # Check if tool was called
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    for tool_call in last_message.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        console.print(f"[cyan]  🔧 Calling tool: {tool_name}[/cyan]")
            
            final_state = event
        
        console.print(f"\n[green]✅ Agent completed in {step_count} steps[/green]\n")
        
        # Extract the final report from messages
        if final_state and "messages" in final_state:
            messages = final_state["messages"]
            
            # Look for the report in the messages
            for message in reversed(messages):
                if hasattr(message, 'content') and message.content:
                    content = message.content
                    # Check if this looks like a report (contains markdown headers)
                    if "# Technical Analysis Report" in content or "## Project Overview" in content:
                        return content
            
            # If no formatted report found, return the last assistant message
            for message in reversed(messages):
                if hasattr(message, 'content') and message.content and message.type == 'ai':
                    return message.content
        
        return "Error: No report generated. The agent may not have completed the analysis."
    
    except Exception as e:
        console.print(f"[red]❌ Error during analysis: {str(e)}[/red]")
        raise


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    from config import get_config
    
    console.print("[bold blue]Testing ReAct Agent[/bold blue]\n")
    
    # Load config
    config = get_config()
    
    # Test with a small repository
    test_repo = "pallets/flask"
    
    console.print(f"[yellow]Testing with: {test_repo}[/yellow]\n")
    
    try:
        report = run_analysis(
            repo_input=test_repo,
            llm=config['llm'],
            tavily_api_key=config.get('tavily_api_key', '')
        )
        
        console.print("\n[bold green]Generated Report:[/bold green]")
        console.print(report[:1000] + "..." if len(report) > 1000 else report)
    
    except Exception as e:
        console.print(f"[red]Test failed: {str(e)}[/red]")
