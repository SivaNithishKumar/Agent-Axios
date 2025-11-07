"""
Repository Loader Tool for cloning Git repositories and loading local folders.
Handles different input formats and provides error handling.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse
import git
from langchain.tools import tool
from rich.console import Console

console = Console()


class RepoLoader:
    """Class to handle repository loading operations."""
    
    def __init__(self):
        """Initialize the repository loader."""
        self.temp_dirs: List[str] = []
        self.loaded_repo_path: Optional[str] = None
        self.repo_info: Dict = {}
    
    def is_git_url(self, input_path: str) -> bool:
        """Check if the input is a Git URL."""
        # Direct Git URL patterns
        if any(input_path.startswith(prefix) for prefix in ['http://', 'https://', 'git@', 'ssh://']):
            return True
        
        # Git hosting service patterns
        git_patterns = [
            'github.com',
            'gitlab.com',
            'bitbucket.org',
        ]
        
        if any(pattern in input_path.lower() for pattern in git_patterns):
            return True
        
        # GitHub shorthand pattern (username/repo)
        if '/' in input_path and len(input_path.split('/')) == 2 and not os.path.exists(input_path):
            # Check if it looks like username/repo format
            parts = input_path.split('/')
            if all(part.strip() and not part.startswith('.') for part in parts):
                return True
        
        return False
    
    def normalize_git_url(self, git_url: str) -> str:
        """Normalize Git URL to ensure it's in the correct format."""
        # Handle SSH URLs
        if git_url.startswith('git@'):
            return git_url
        
        # Handle HTTPS URLs
        if git_url.startswith(('http://', 'https://')):
            if not git_url.endswith('.git'):
                git_url += '.git'
            return git_url
        
        # Handle GitHub shorthand (username/repo)
        if '/' in git_url and not git_url.startswith(('http', 'git@')):
            return f"https://github.com/{git_url}.git"
        
        return git_url
    
    def clone_repository(self, git_url: str, target_dir: Optional[str] = None) -> str:
        """Clone a Git repository to a local directory."""
        try:
            # Normalize the Git URL
            normalized_url = self.normalize_git_url(git_url)
            
            # Create temporary directory if no target specified
            if target_dir is None:
                target_dir = tempfile.mkdtemp(prefix="repo_analyzer_")
                self.temp_dirs.append(target_dir)
            
            console.print(f"[blue]🔄 Cloning repository from {normalized_url}...[/blue]")
            
            # Clone the repository
            repo = git.Repo.clone_from(normalized_url, target_dir)
            
            # Extract repository information
            self.repo_info = {
                'url': normalized_url,
                'local_path': target_dir,
                'branch': repo.active_branch.name,
                'commit_hash': repo.head.commit.hexsha,
                'commit_message': repo.head.commit.message.strip(),
                'author': str(repo.head.commit.author),
                'commit_date': repo.head.commit.committed_datetime.isoformat(),
            }
            
            console.print(f"[green]✅ Repository cloned successfully to {target_dir}[/green]")
            return target_dir
            
        except git.exc.GitError as e:
            console.print(f"[red]❌ Git error: {str(e)}[/red]")
            raise
        except Exception as e:
            console.print(f"[red]❌ Error cloning repository: {str(e)}[/red]")
            raise
    
    def validate_local_path(self, local_path: str) -> str:
        """Validate and return absolute path for local directory."""
        path = Path(local_path).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if not path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")
        
        console.print(f"[green]✅ Local directory validated: {path}[/green]")
        return str(path)
    
    def load_repository(self, input_path: str) -> Dict:
        """Load repository from Git URL or local path."""
        try:
            if self.is_git_url(input_path):
                # Handle Git repository
                repo_path = self.clone_repository(input_path)
                source_type = "git"
            else:
                # Handle local directory
                repo_path = self.validate_local_path(input_path)
                source_type = "local"
                
                # Set basic info for local repos
                self.repo_info = {
                    'url': None,
                    'local_path': repo_path,
                    'source_type': source_type
                }
            
            self.loaded_repo_path = repo_path
            
            # Get basic file statistics
            file_stats = self._get_file_statistics(repo_path)
            
            result = {
                'status': 'success',
                'repo_path': repo_path,
                'source_type': source_type,
                'repo_info': self.repo_info,
                'file_stats': file_stats,
                'message': f"Repository loaded successfully from {source_type}"
            }
            
            console.print(f"[green]✅ Repository loaded: {repo_path}[/green]")
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load repository: {str(e)}[/red]")
            return {
                'status': 'error',
                'error': str(e),
                'repo_path': None,
                'message': f"Failed to load repository: {str(e)}"
            }
    
    def _get_file_statistics(self, repo_path: str) -> Dict:
        """Get basic file statistics for the repository."""
        try:
            total_files = 0
            total_size = 0
            file_types = {}
            
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories like .git
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        total_files += 1
                        total_size += file_size
                        
                        # Count file extensions
                        ext = Path(file).suffix.lower()
                        if ext:
                            file_types[ext] = file_types.get(ext, 0) + 1
                        else:
                            file_types['no_extension'] = file_types.get('no_extension', 0) + 1
                    except (OSError, IOError):
                        continue
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': file_types,
                'common_extensions': dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    console.print(f"[yellow]🧹 Cleaned up temporary directory: {temp_dir}[/yellow]")
            except Exception as e:
                console.print(f"[red]❌ Failed to cleanup {temp_dir}: {str(e)}[/red]")
        
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            # Only cleanup if not already shutting down
            import sys
            if hasattr(sys, 'meta_path') and sys.meta_path is not None:
                self.cleanup()
        except:
            # Ignore errors during shutdown
            pass


# Global loader instance
repo_loader = RepoLoader()


@tool
def load_repository_tool(input_path: str) -> str:
    """
    Load a repository from a Git URL or local directory path.
    
    Args:
        input_path: Git URL (e.g., https://github.com/user/repo.git) or local directory path
    
    Returns:
        JSON string with repository loading results including path, statistics, and metadata
    """
    result = repo_loader.load_repository(input_path)
    
    # Format the result for LangChain
    if result['status'] == 'success':
        return f"""Repository loaded successfully!
        
Path: {result['repo_path']}
Source: {result['source_type']}
Files: {result['file_stats'].get('total_files', 'N/A')}
Size: {result['file_stats'].get('total_size_mb', 'N/A')} MB
Common file types: {result['file_stats'].get('common_extensions', {})}

Repository info: {result['repo_info']}
"""
    else:
        return f"Error loading repository: {result['error']}"


def get_loaded_repo_path() -> Optional[str]:
    """Get the path of the currently loaded repository."""
    return repo_loader.loaded_repo_path


if __name__ == "__main__":
    # Test the tool
    console.print("[bold blue]Testing Repository Loader Tool[/bold blue]")
    
    # Test with current directory
    test_path = "."
    console.print(f"\n[yellow]Testing with local path: {test_path}[/yellow]")
    result = load_repository_tool(test_path)
    console.print(result)
    
    # Test with a sample GitHub repository
    test_repo = "octocat/Hello-World"
    console.print(f"\n[yellow]Testing with GitHub repo: {test_repo}[/yellow]")
    result = load_repository_tool(test_repo)
    console.print(result)
    
    # Cleanup
    repo_loader.cleanup()
