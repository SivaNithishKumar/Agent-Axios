"""
Structure Mapper Tool for analyzing repository structure and identifying key components.
Maps directories, entry points, configuration files, and important project components.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter
from langchain.tools import tool
from rich.console import Console

console = Console()


class StructureMapper:
    """Class to map and analyze repository structure."""
    
    def __init__(self):
        """Initialize the structure mapper."""
        # Define important directory patterns
        self.important_dirs = {
            'source': ['src', 'source', 'lib', 'app', 'application'],
            'tests': ['test', 'tests', '__tests__', 'spec', 'specs'],
            'docs': ['docs', 'doc', 'documentation', 'README'],
            'config': ['config', 'conf', 'configuration', 'settings'],
            'build': ['build', 'dist', 'target', 'bin', 'output'],
            'assets': ['assets', 'static', 'public', 'resources', 'media'],
            'scripts': ['scripts', 'bin', 'tools', 'utils'],
            'examples': ['examples', 'samples', 'demo', 'demos'],
            'data': ['data', 'datasets', 'fixtures', 'seed']
        }
        
        # Entry point patterns for different languages
        self.entry_points = {
            'python': ['main.py', 'app.py', 'run.py', '__main__.py', 'server.py', 'manage.py'],
            'nodejs': ['index.js', 'app.js', 'server.js', 'main.js', 'start.js'],
            'java': ['Main.java', 'Application.java', '*.java'],
            'go': ['main.go', 'cmd/main.go'],
            'rust': ['src/main.rs', 'src/lib.rs'],
            'php': ['index.php', 'app.php', 'public/index.php'],
            'ruby': ['app.rb', 'main.rb', 'config.ru'],
            'csharp': ['Program.cs', 'Main.cs', 'App.cs']
        }
        
        # Important configuration files
        self.config_files = {
            'docker': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', '.dockerignore'],
            'ci_cd': ['.github/workflows', '.gitlab-ci.yml', 'Jenkinsfile', '.travis.yml', 'azure-pipelines.yml'],
            'version_control': ['.gitignore', '.gitattributes', '.gitmodules'],
            'ide': ['.vscode', '.idea', '*.code-workspace'],
            'linting': ['.eslintrc', '.pylintrc', '.flake8', 'tslint.json', '.editorconfig'],
            'env': ['.env', '.env.example', '.env.local', '.env.production'],
            'license': ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING'],
            'readme': ['README.md', 'README.txt', 'README.rst', 'README'],
            'security': ['.gitignore', 'SECURITY.md', '.snyk']
        }
    
    def scan_directory_structure(self, repo_path: str, max_depth: int = 5) -> Dict:
        """Scan and analyze the directory structure."""
        if not os.path.exists(repo_path):
            return {'error': f'Directory does not exist: {repo_path}'}
        
        structure = {
            'directories': {},
            'files_by_type': defaultdict(list),
            'total_files': 0,
            'total_directories': 0,
            'max_depth_reached': 0,
            'large_directories': []  # Directories with many files
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Calculate depth
                depth = root[len(repo_path):].count(os.sep)
                if depth > max_depth:
                    dirs.clear()  # Don't recurse deeper
                    continue
                
                structure['max_depth_reached'] = max(structure['max_depth_reached'], depth)
                
                # Skip hidden directories and common build directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build', 'dist', 'venv']]
                
                rel_root = os.path.relpath(root, repo_path)
                if rel_root == '.':
                    rel_root = ''
                
                # Count directories
                structure['total_directories'] += len(dirs)
                
                # Analyze files in current directory
                non_hidden_files = [f for f in files if not f.startswith('.')]
                file_count = len(non_hidden_files)
                
                # Track large directories
                if file_count > 50:
                    structure['large_directories'].append({
                        'path': rel_root or 'root',
                        'file_count': file_count
                    })
                
                # Categorize files by extension
                for file in non_hidden_files:
                    structure['total_files'] += 1
                    
                    ext = Path(file).suffix.lower()
                    if ext:
                        structure['files_by_type'][ext].append(os.path.join(rel_root, file))
                    else:
                        structure['files_by_type']['no_extension'].append(os.path.join(rel_root, file))
                
                # Store directory information
                if rel_root:
                    structure['directories'][rel_root] = {
                        'file_count': file_count,
                        'subdirs': dirs.copy(),
                        'depth': depth
                    }
        
        except Exception as e:
            return {'error': str(e)}
        
        return structure
    
    def identify_important_directories(self, structure: Dict, repo_path: str) -> Dict[str, List[str]]:
        """Identify important directories based on naming patterns."""
        identified = defaultdict(list)
        
        if 'error' in structure:
            return identified
        
        # Check directories against patterns
        for dir_path in structure['directories'].keys():
            dir_name = os.path.basename(dir_path).lower()
            
            for category, patterns in self.important_dirs.items():
                for pattern in patterns:
                    if pattern in dir_name or dir_name == pattern:
                        identified[category].append(dir_path)
                        break
        
        # Also check for directories that exist in the file system
        for category, patterns in self.important_dirs.items():
            for pattern in patterns:
                full_path = os.path.join(repo_path, pattern)
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    rel_path = pattern
                    if rel_path not in identified[category]:
                        identified[category].append(rel_path)
        
        return dict(identified)
    
    def find_entry_points(self, repo_path: str, project_type: str = None) -> Dict[str, List[str]]:
        """Find potential entry points for the application."""
        entry_points = defaultdict(list)
        
        # Determine which patterns to check
        patterns_to_check = {}
        if project_type and project_type in self.entry_points:
            patterns_to_check[project_type] = self.entry_points[project_type]
        else:
            patterns_to_check = self.entry_points
        
        for lang, patterns in patterns_to_check.items():
            for pattern in patterns:
                if '*' in pattern:
                    # Handle wildcard patterns
                    pattern_dir = os.path.dirname(pattern) if '/' in pattern else ''
                    pattern_file = os.path.basename(pattern)
                    search_dir = os.path.join(repo_path, pattern_dir) if pattern_dir else repo_path
                    
                    if os.path.exists(search_dir):
                        for file in os.listdir(search_dir):
                            if pattern_file.replace('*', '') in file:
                                rel_path = os.path.join(pattern_dir, file) if pattern_dir else file
                                entry_points[lang].append(rel_path)
                else:
                    full_path = os.path.join(repo_path, pattern)
                    if os.path.exists(full_path):
                        entry_points[lang].append(pattern)
        
        return dict(entry_points)
    
    def find_config_files(self, repo_path: str) -> Dict[str, List[str]]:
        """Find configuration files in the repository."""
        config_files = defaultdict(list)
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and build directories
                dirs[:] = [d for d in dirs if not d.startswith('.') or d in ['.github', '.vscode']]
                
                rel_root = os.path.relpath(root, repo_path)
                if rel_root == '.':
                    rel_root = ''
                
                for file in files:
                    file_path = os.path.join(rel_root, file) if rel_root else file
                    
                    # Check against config file patterns
                    for category, patterns in self.config_files.items():
                        for pattern in patterns:
                            if '/' in pattern:
                                # Directory pattern
                                if pattern in file_path:
                                    config_files[category].append(file_path)
                            elif '*' in pattern:
                                # Wildcard pattern
                                if pattern.replace('*', '') in file:
                                    config_files[category].append(file_path)
                            else:
                                # Exact match
                                if file == pattern:
                                    config_files[category].append(file_path)
        
        except Exception as e:
            console.print(f"[red]Error finding config files: {str(e)}[/red]")
        
        return dict(config_files)
    
    def analyze_file_distribution(self, structure: Dict) -> Dict:
        """Analyze the distribution of files across directories."""
        if 'error' in structure:
            return {'error': structure['error']}
        
        # Count files by extension
        extension_counts = {}
        for ext, files in structure['files_by_type'].items():
            extension_counts[ext] = len(files)
        
        # Sort by count
        sorted_extensions = dict(sorted(extension_counts.items(), key=lambda x: x[1], reverse=True))
        
        # Calculate directory depths
        depth_distribution = defaultdict(int)
        for dir_info in structure['directories'].values():
            depth_distribution[dir_info['depth']] += 1
        
        return {
            'extension_counts': sorted_extensions,
            'depth_distribution': dict(depth_distribution),
            'largest_directories': sorted(structure['large_directories'], key=lambda x: x['file_count'], reverse=True)[:10]
        }
    
    def create_structure_summary(self, repo_path: str, project_type: str = None) -> Dict:
        """Create a comprehensive structure summary."""
        console.print(f"[blue]🏗️ Analyzing repository structure: {repo_path}[/blue]")
        
        try:
            # Scan directory structure
            structure = self.scan_directory_structure(repo_path)
            
            if 'error' in structure:
                return {
                    'status': 'error',
                    'error': structure['error']
                }
            
            # Identify important directories
            important_dirs = self.identify_important_directories(structure, repo_path)
            
            # Find entry points
            entry_points = self.find_entry_points(repo_path, project_type)
            
            # Find configuration files
            config_files = self.find_config_files(repo_path)
            
            # Analyze file distribution
            file_analysis = self.analyze_file_distribution(structure)
            
            # Create directory tree (simplified)
            tree = self._create_directory_tree(repo_path, max_items=30)
            
            result = {
                'status': 'success',
                'summary': {
                    'total_files': structure['total_files'],
                    'total_directories': structure['total_directories'],
                    'max_depth': structure['max_depth_reached'],
                    'large_directories_count': len(structure['large_directories'])
                },
                'important_directories': important_dirs,
                'entry_points': entry_points,
                'config_files': config_files,
                'file_analysis': file_analysis,
                'directory_tree': tree
            }
            
            console.print(f"[green]✅ Structure analysis complete. Found {structure['total_files']} files in {structure['total_directories']} directories[/green]")
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing structure: {str(e)}[/red]")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _create_directory_tree(self, repo_path: str, max_items: int = 30) -> List[str]:
        """Create a simplified directory tree representation."""
        tree = []
        count = 0
        
        try:
            for root, dirs, files in os.walk(repo_path):
                if count >= max_items:
                    tree.append("... (truncated)")
                    break
                
                # Skip hidden and build directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'target', 'build']]
                
                level = root.replace(repo_path, '').count(os.sep)
                indent = '  ' * level
                dirname = os.path.basename(root)
                
                if level == 0:
                    tree.append('.')
                else:
                    tree.append(f"{indent}{dirname}/")
                    count += 1
                
                # Add some important files
                subindent = '  ' * (level + 1)
                important_files = [f for f in files if not f.startswith('.') and 
                                 any(f.endswith(ext) for ext in ['.py', '.js', '.java', '.go', '.rs', '.md', '.txt', '.yml', '.yaml', '.json'])][:3]
                
                for file in important_files:
                    if count >= max_items:
                        break
                    tree.append(f"{subindent}{file}")
                    count += 1
                
                if level >= 3:  # Limit depth for readability
                    dirs.clear()
        
        except Exception as e:
            tree.append(f"Error creating tree: {str(e)}")
        
        return tree


# Global mapper instance
structure_mapper = StructureMapper()


@tool
def analyze_repository_structure_tool(repo_path: Optional[str] = None, project_type: Optional[str] = None) -> str:
    """
    Analyze the repository structure to identify key directories, entry points, and configuration files.
    
    Args:
        repo_path: Optional path to repository. If not provided, uses current directory.
        project_type: Optional project type hint (python, nodejs, etc.) to help identify entry points.
    
    Returns:
        Comprehensive analysis of the repository structure including directories, files, and organization.
    """
    if repo_path is None:
        repo_path = os.getcwd()
    
    result = structure_mapper.create_structure_summary(repo_path, project_type)
    
    if result['status'] == 'error':
        return f"Error analyzing repository structure: {result['error']}"
    
    # Format the result for LangChain
    output = f"""Repository Structure Analysis:

SUMMARY:
  - Total files: {result['summary']['total_files']}
  - Total directories: {result['summary']['total_directories']}
  - Maximum depth: {result['summary']['max_depth']}
  - Large directories: {result['summary']['large_directories_count']}

"""
    
    # Important directories
    if result['important_directories']:
        output += "IMPORTANT DIRECTORIES:\n"
        for category, dirs in result['important_directories'].items():
            if dirs:
                output += f"  {category}: {', '.join(dirs)}\n"
        output += "\n"
    
    # Entry points
    if result['entry_points']:
        output += "ENTRY POINTS:\n"
        for lang, files in result['entry_points'].items():
            if files:
                output += f"  {lang}: {', '.join(files)}\n"
        output += "\n"
    
    # Configuration files
    if result['config_files']:
        output += "CONFIGURATION FILES:\n"
        for category, files in result['config_files'].items():
            if files:
                output += f"  {category}: {', '.join(files[:3])}"
                if len(files) > 3:
                    output += f" (and {len(files) - 3} more)"
                output += "\n"
        output += "\n"
    
    # File distribution
    if result['file_analysis']['extension_counts']:
        output += "FILE TYPES (top 10):\n"
        for ext, count in list(result['file_analysis']['extension_counts'].items())[:10]:
            output += f"  {ext}: {count} files\n"
        output += "\n"
    
    # Directory tree
    if result['directory_tree']:
        output += "DIRECTORY TREE (sample):\n"
        for item in result['directory_tree'][:20]:
            output += f"  {item}\n"
    
    return output


if __name__ == "__main__":
    # Test the tool
    console.print("[bold blue]Testing Repository Structure Mapper Tool[/bold blue]")
    
    # Test with current directory
    test_path = "/home/ubuntu/sem"
    console.print(f"\n[yellow]Testing with path: {test_path}[/yellow]")
    result = analyze_repository_structure_tool(test_path, "python")
    console.print(result)
