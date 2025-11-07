"""
ReAct Agent Tools for Repository Analysis
Provides autonomous tools for LLM-driven repository exploration and analysis.
"""

import os
import json
import glob
from pathlib import Path
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from langsmith import traceable
from rich.console import Console

# Import existing components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.repo_loader import repo_loader
from tools.project_detector import ProjectTypeDetector
from tools.dependency_extractor import DependencyExtractor
from tools.structure_mapper import StructureMapper
from tools.framework_detector import FrameworkDetector
from tools.create_report import ReportGenerator

console = Console()


# ============================================================================
# REPOSITORY OPERATIONS
# ============================================================================

@tool
def clone_repository(repo_input: str) -> str:
    """
    Clone or load a repository from a Git URL or local path.
    
    Args:
        repo_input: Git URL (e.g., 'https://github.com/user/repo.git' or 'user/repo') or local directory path
    
    Returns:
        JSON string with repository path and basic information
    
    Examples:
        - clone_repository("pallets/flask")
        - clone_repository("https://github.com/django/django.git")
        - clone_repository("/home/user/my-project")
    """
    try:
        console.print(f"[blue]📥 Cloning/loading repository: {repo_input}[/blue]")
        result = repo_loader.load_repository(repo_input)
        
        if result['status'] == 'success':
            return json.dumps({
                "success": True,
                "repo_path": result['repo_path'],
                "source_type": result['source_type'],
                "total_files": result['file_stats'].get('total_files', 0),
                "total_size_mb": result['file_stats'].get('total_size_mb', 0),
                "message": f"Repository loaded successfully at {result['repo_path']}"
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "message": "Failed to load repository"
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"Exception occurred: {str(e)}"
        }, indent=2)


@tool
def list_directory(path: str, show_hidden: bool = False, max_items: int = 50) -> str:
    """
    List files and directories in a given path.
    
    Args:
        path: Directory path to list
        show_hidden: Whether to show hidden files (starting with .)
        max_items: Maximum number of items to return
    
    Returns:
        JSON string with directory contents
    
    Examples:
        - list_directory("/tmp/repo_xyz")
        - list_directory("/tmp/repo_xyz/src", show_hidden=True)
    """
    try:
        console.print(f"[blue]📁 Listing directory: {path}[/blue]")
        
        if not os.path.exists(path):
            return json.dumps({
                "success": False,
                "error": f"Path does not exist: {path}"
            }, indent=2)
        
        if not os.path.isdir(path):
            return json.dumps({
                "success": False,
                "error": f"Path is not a directory: {path}"
            }, indent=2)
        
        items = []
        try:
            for item_name in sorted(os.listdir(path)):
                if not show_hidden and item_name.startswith('.'):
                    continue
                
                item_path = os.path.join(path, item_name)
                is_dir = os.path.isdir(item_path)
                
                item_info = {
                    "name": item_name,
                    "type": "directory" if is_dir else "file",
                    "path": item_path
                }
                
                if not is_dir:
                    try:
                        item_info["size"] = os.path.getsize(item_path)
                    except:
                        item_info["size"] = 0
                
                items.append(item_info)
                
                if len(items) >= max_items:
                    break
        
        except PermissionError:
            return json.dumps({
                "success": False,
                "error": f"Permission denied: {path}"
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "path": path,
            "items": items,
            "total_items": len(items),
            "truncated": len(items) >= max_items,
            "message": f"Listed {len(items)} items in {path}"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool
def read_file(file_path: str, max_lines: int = 200) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        max_lines: Maximum number of lines to return (default: 200)
    
    Returns:
        JSON string with file contents
    
    Examples:
        - read_file("/tmp/repo_xyz/README.md")
        - read_file("/tmp/repo_xyz/package.json", max_lines=50)
    """
    try:
        console.print(f"[blue]📄 Reading file: {file_path}[/blue]")
        
        if not os.path.exists(file_path):
            return json.dumps({
                "success": False,
                "error": f"File does not exist: {file_path}"
            }, indent=2)
        
        if not os.path.isfile(file_path):
            return json.dumps({
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }, indent=2)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:  # 1MB
            return json.dumps({
                "success": False,
                "error": f"File too large: {file_size} bytes (max 1MB)",
                "suggestion": "This file is too large. Consider using search_files to find specific content."
            }, indent=2)
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            truncated = total_lines > max_lines
            
            if truncated:
                content = ''.join(lines[:max_lines])
            else:
                content = ''.join(lines)
            
            return json.dumps({
                "success": True,
                "file_path": file_path,
                "content": content,
                "total_lines": total_lines,
                "lines_returned": min(total_lines, max_lines),
                "truncated": truncated,
                "message": f"Read {min(total_lines, max_lines)} lines from {os.path.basename(file_path)}"
            }, indent=2)
        
        except UnicodeDecodeError:
            return json.dumps({
                "success": False,
                "error": "File contains binary data or unsupported encoding",
                "suggestion": "This appears to be a binary file"
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool
def search_files(pattern: str, base_path: str, max_results: int = 20) -> str:
    """
    Search for files matching a pattern in a directory tree.
    
    Args:
        pattern: File pattern to search for (e.g., "*.py", "package.json", "*test*")
        base_path: Base directory to search in
        max_results: Maximum number of results to return
    
    Returns:
        JSON string with matching file paths
    
    Examples:
        - search_files("*.py", "/tmp/repo_xyz")
        - search_files("package.json", "/tmp/repo_xyz")
        - search_files("*config*", "/tmp/repo_xyz")
    """
    try:
        console.print(f"[blue]🔍 Searching for files: {pattern} in {base_path}[/blue]")
        
        if not os.path.exists(base_path):
            return json.dumps({
                "success": False,
                "error": f"Path does not exist: {base_path}"
            }, indent=2)
        
        # Use glob to search
        search_pattern = os.path.join(base_path, "**", pattern)
        matches = []
        
        for file_path in glob.glob(search_pattern, recursive=True):
            # Skip hidden directories and files
            if '/.git/' in file_path or '/.venv/' in file_path or '/node_modules/' in file_path:
                continue
            
            if os.path.isfile(file_path):
                matches.append({
                    "path": file_path,
                    "relative_path": os.path.relpath(file_path, base_path),
                    "name": os.path.basename(file_path),
                    "size": os.path.getsize(file_path)
                })
                
                if len(matches) >= max_results:
                    break
        
        return json.dumps({
            "success": True,
            "pattern": pattern,
            "base_path": base_path,
            "matches": matches,
            "total_matches": len(matches),
            "truncated": len(matches) >= max_results,
            "message": f"Found {len(matches)} files matching '{pattern}'"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool
def get_file_info(file_path: str) -> str:
    """
    Get metadata about a file without reading its contents.
    
    Args:
        file_path: Path to the file
    
    Returns:
        JSON string with file metadata
    
    Examples:
        - get_file_info("/tmp/repo_xyz/README.md")
    """
    try:
        if not os.path.exists(file_path):
            return json.dumps({
                "success": False,
                "error": f"File does not exist: {file_path}"
            }, indent=2)
        
        stat = os.stat(file_path)
        
        return json.dumps({
            "success": True,
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "is_file": os.path.isfile(file_path),
            "is_directory": os.path.isdir(file_path),
            "extension": Path(file_path).suffix,
            "modified": stat.st_mtime
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# ANALYSIS OPERATIONS
# ============================================================================

@tool
def analyze_dependencies(repo_path: str) -> str:
    """
    Extract and analyze dependencies from the repository.
    
    Args:
        repo_path: Path to the repository
    
    Returns:
        JSON string with dependency information
    
    Examples:
        - analyze_dependencies("/tmp/repo_xyz")
    """
    try:
        console.print(f"[blue]📦 Analyzing dependencies in: {repo_path}[/blue]")
        extractor = DependencyExtractor()
        result = extractor.analyze_dependencies(repo_path)
        
        return json.dumps({
            "success": True,
            "dependencies": result.get("dependencies", {}),
            "summary": result.get("summary", {}),
            "dependency_files": result.get("dependency_files", {}),
            "message": f"Found {result.get('summary', {}).get('total_dependencies', 0)} dependencies"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool
def detect_project_type(repo_path: str) -> str:
    """
    Detect the programming language and project type.
    
    Args:
        repo_path: Path to the repository
    
    Returns:
        JSON string with project type information
    
    Examples:
        - detect_project_type("/tmp/repo_xyz")
    """
    try:
        console.print(f"[blue]🔍 Detecting project type for: {repo_path}[/blue]")
        detector = ProjectTypeDetector()
        result = detector.analyze_project_type(repo_path)
        
        return json.dumps({
            "success": True,
            "primary_language": result.get("primary_language", "unknown"),
            "project_types": result.get("project_types", []),
            "confidence_scores": result.get("scores", {}),
            "detected_frameworks": result.get("frameworks", []),
            "message": f"Detected as {result.get('primary_language', 'unknown')} project"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool
def analyze_structure(repo_path: str) -> str:
    """
    Analyze the repository structure and organization.
    
    Args:
        repo_path: Path to the repository
    
    Returns:
        JSON string with structure information
    
    Examples:
        - analyze_structure("/tmp/repo_xyz")
    """
    try:
        console.print(f"[blue]📁 Analyzing structure of: {repo_path}[/blue]")
        mapper = StructureMapper()
        result = mapper.create_structure_summary(repo_path)
        
        return json.dumps({
            "success": True,
            "statistics": result.get("statistics", {}),
            "important_directories": result.get("important_directories", {}),
            "entry_points": result.get("entry_points", {}),
            "config_files": result.get("config_files", {}),
            "file_distribution": result.get("file_distribution", {}),
            "message": f"Analyzed {result.get('statistics', {}).get('total_files', 0)} files"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool
def detect_frameworks(repo_path: str) -> str:
    """
    Detect frameworks and libraries used in the project.
    
    Args:
        repo_path: Path to the repository
    
    Returns:
        JSON string with framework information
    
    Examples:
        - detect_frameworks("/tmp/repo_xyz")
    """
    try:
        console.print(f"[blue]🔧 Detecting frameworks in: {repo_path}[/blue]")
        detector = FrameworkDetector()
        result = detector.analyze_frameworks(repo_path)
        
        return json.dumps({
            "success": True,
            "frameworks": result.get("frameworks", []),
            "categories": result.get("categories", {}),
            "import_analysis": result.get("import_analysis", {}),
            "message": f"Detected {len(result.get('frameworks', []))} frameworks"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# COMPLETION TOOL
# ============================================================================

@tool
def generate_final_report(analysis_summary: str, repo_path: str, repo_name: str = "Repository") -> str:
    """
    Generate the final technical report. Call this when you have gathered sufficient information.
    This tool signals that the analysis is complete.
    
    Args:
        analysis_summary: Comprehensive summary of all gathered information (JSON format recommended)
        repo_path: Path to the analyzed repository
        repo_name: Name of the repository for the report
    
    Returns:
        The generated technical report in Markdown format
    
    IMPORTANT: This is the final step. Only call this when you have:
    - Cloned/loaded the repository
    - Explored its structure
    - Analyzed dependencies and frameworks
    - Read key files (README, config files, etc.)
    - Gathered sufficient information for a comprehensive report
    
    Examples:
        - generate_final_report(json.dumps({...}), "/tmp/repo_xyz", "flask")
    """
    try:
        console.print(f"[blue]🤖 Generating final report for: {repo_name}[/blue]")
        
        # Initialize report generator
        generator = ReportGenerator()
        generator.initialize_llm()
        
        # Generate the report
        report = generator.generate_report(
            analysis_context=analysis_summary,
            repo_path=repo_path
        )
        
        console.print("[green]✅ Technical report generated successfully[/green]")
        
        return report
    
    except Exception as e:
        console.print(f"[red]❌ Failed to generate report: {str(e)}[/red]")
        return f"ERROR: Failed to generate report - {str(e)}"


# ============================================================================
# TOOL LISTS
# ============================================================================

# All tools for the agent
ALL_TOOLS = [
    clone_repository,
    list_directory,
    read_file,
    search_files,
    get_file_info,
    analyze_dependencies,
    detect_project_type,
    analyze_structure,
    detect_frameworks,
    generate_final_report
]


if __name__ == "__main__":
    # Test tools
    console.print("[bold blue]Testing ReAct Agent Tools[/bold blue]\n")
    
    # Test list_directory
    console.print("[yellow]Testing list_directory on current directory[/yellow]")
    result = list_directory.invoke({"path": ".", "max_items": 10})
    print(result)
