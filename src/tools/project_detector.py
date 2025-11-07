"""
Project Type Detector Tool for identifying programming languages and project types.
Analyzes files and directory structure to determine the primary technology stack.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import Counter
from langchain.tools import tool
from rich.console import Console

console = Console()

# Import function to get loaded repo path
def get_loaded_repo_path() -> Optional[str]:
    """Get the path of the currently loaded repository. Placeholder for now."""
    return None


class ProjectTypeDetector:
    """Class to detect project type and programming languages."""
    
    def __init__(self):
        """Initialize the project type detector."""
        # Define file patterns for different project types
        self.project_indicators = {
            'python': {
                'files': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock', 'setup.cfg'],
                'extensions': ['.py', '.pyx', '.pyi'],
                'directories': ['__pycache__', '.pytest_cache', 'site-packages'],
                'config_files': ['tox.ini', 'pytest.ini', '.flake8', 'mypy.ini']
            },
            'nodejs': {
                'files': ['package.json', 'package-lock.json', 'yarn.lock', 'node_modules'],
                'extensions': ['.js', '.ts', '.jsx', '.tsx'],
                'directories': ['node_modules', 'dist', 'build'],
                'config_files': ['.babelrc', 'webpack.config.js', 'tsconfig.json', '.eslintrc']
            },
            'java': {
                'files': ['pom.xml', 'build.gradle', 'gradlew', 'maven-wrapper.properties'],
                'extensions': ['.java', '.class', '.jar'],
                'directories': ['src/main/java', 'target', 'build'],
                'config_files': ['application.properties', 'application.yml']
            },
            'csharp': {
                'files': ['*.csproj', '*.sln', '*.vbproj', 'packages.config'],
                'extensions': ['.cs', '.vb', '.dll'],
                'directories': ['bin', 'obj', 'packages'],
                'config_files': ['app.config', 'web.config']
            },
            'go': {
                'files': ['go.mod', 'go.sum', 'Gopkg.toml', 'Gopkg.lock'],
                'extensions': ['.go'],
                'directories': ['vendor'],
                'config_files': ['go.mod', 'go.sum']
            },
            'rust': {
                'files': ['Cargo.toml', 'Cargo.lock'],
                'extensions': ['.rs'],
                'directories': ['target', 'src'],
                'config_files': ['Cargo.toml']
            },
            'php': {
                'files': ['composer.json', 'composer.lock'],
                'extensions': ['.php', '.phtml'],
                'directories': ['vendor'],
                'config_files': ['.htaccess', 'php.ini']
            },
            'ruby': {
                'files': ['Gemfile', 'Gemfile.lock', '*.gemspec'],
                'extensions': ['.rb', '.erb'],
                'directories': ['vendor/bundle'],
                'config_files': ['config.ru', '.ruby-version']
            },
            'cpp': {
                'files': ['CMakeLists.txt', 'Makefile', 'configure.ac'],
                'extensions': ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'],
                'directories': ['build', 'cmake'],
                'config_files': ['CMakeLists.txt', 'Makefile']
            },
            'swift': {
                'files': ['Package.swift', '*.xcodeproj', '*.xcworkspace'],
                'extensions': ['.swift'],
                'directories': ['.build', 'DerivedData'],
                'config_files': ['Package.swift']
            },
            'kotlin': {
                'files': ['build.gradle.kts', 'settings.gradle.kts'],
                'extensions': ['.kt', '.kts'],
                'directories': ['build', 'gradle'],
                'config_files': ['gradle.properties']
            }
        }
        
        # Web framework indicators
        self.framework_indicators = {
            'react': ['package.json', 'src/App.js', 'src/App.tsx', 'public/index.html'],
            'vue': ['vue.config.js', 'src/main.js', 'src/App.vue'],
            'angular': ['angular.json', 'src/app', 'package.json'],
            'django': ['manage.py', 'settings.py', 'urls.py', 'requirements.txt'],
            'flask': ['app.py', 'requirements.txt', 'templates'],
            'express': ['package.json', 'server.js', 'app.js'],
            'spring': ['pom.xml', 'src/main/java', 'application.properties'],
            'laravel': ['artisan', 'composer.json', 'config/app.php'],
            'rails': ['Gemfile', 'config/routes.rb', 'app/controllers']
        }
    
    def scan_directory(self, repo_path: str) -> Dict:
        """Scan directory and collect file information."""
        if not os.path.exists(repo_path):
            return {'error': f'Directory does not exist: {repo_path}'}
        
        file_extensions = Counter()
        total_files = 0
        found_files = set()
        found_directories = set()
        directory_structure = []
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and common build/cache directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'target', 'build', 'dist']]
                
                rel_root = os.path.relpath(root, repo_path)
                if rel_root != '.':
                    directory_structure.append(rel_root)
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    total_files += 1
                    found_files.add(file.lower())
                    
                    # Count file extensions
                    ext = Path(file).suffix.lower()
                    if ext:
                        file_extensions[ext] += 1
                
                # Check for directories
                for dir_name in dirs:
                    found_directories.add(dir_name.lower())
            
            return {
                'file_extensions': dict(file_extensions),
                'total_files': total_files,
                'found_files': found_files,
                'found_directories': found_directories,
                'directory_structure': directory_structure[:50]  # Limit to avoid too much data
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_project_scores(self, scan_data: Dict) -> Dict[str, float]:
        """Calculate confidence scores for each project type."""
        if 'error' in scan_data:
            return {}
        
        scores = {}
        
        for project_type, indicators in self.project_indicators.items():
            score = 0.0
            
            # Check for indicator files
            for file_pattern in indicators['files']:
                if '*' in file_pattern:
                    # Handle wildcard patterns
                    pattern = file_pattern.replace('*', '')
                    matches = [f for f in scan_data['found_files'] if pattern in f]
                    if matches:
                        score += 3.0
                else:
                    if file_pattern.lower() in scan_data['found_files']:
                        score += 3.0
            
            # Check for file extensions
            for ext in indicators['extensions']:
                if ext in scan_data['file_extensions']:
                    count = scan_data['file_extensions'][ext]
                    # More files = higher confidence
                    score += min(count * 0.1, 2.0)
            
            # Check for directories
            for directory in indicators['directories']:
                if directory.lower() in scan_data['found_directories']:
                    score += 1.0
            
            # Check for config files
            for config_file in indicators['config_files']:
                if config_file.lower() in scan_data['found_files']:
                    score += 1.5
            
            scores[project_type] = score
        
        return scores
    
    def detect_frameworks(self, repo_path: str, scan_data: Dict) -> List[str]:
        """Detect specific frameworks based on file patterns."""
        detected_frameworks = []
        
        for framework, indicators in self.framework_indicators.items():
            matches = 0
            for indicator in indicators:
                file_path = os.path.join(repo_path, indicator)
                if os.path.exists(file_path):
                    matches += 1
                elif indicator.lower() in scan_data.get('found_files', set()):
                    matches += 1
                elif any(indicator in d for d in scan_data.get('directory_structure', [])):
                    matches += 1
            
            # If at least 30% of indicators match, consider framework detected
            if matches >= len(indicators) * 0.3:
                detected_frameworks.append(framework)
        
        return detected_frameworks
    
    def analyze_project_type(self, repo_path: Optional[str] = None) -> Dict:
        """Analyze project type for the given repository path."""
        if repo_path is None:
            repo_path = get_loaded_repo_path()
        
        if repo_path is None:
            return {
                'error': 'No repository loaded. Please load a repository first.',
                'status': 'error'
            }
        
        console.print(f"[blue]🔍 Analyzing project type for: {repo_path}[/blue]")
        
        try:
            # Scan the directory
            scan_data = self.scan_directory(repo_path)
            
            if 'error' in scan_data:
                return {
                    'error': scan_data['error'],
                    'status': 'error'
                }
            
            # Calculate project type scores
            scores = self.calculate_project_scores(scan_data)
            
            # Determine primary language/type
            if scores:
                primary_type = max(scores.items(), key=lambda x: x[1])
                sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
            else:
                primary_type = ('unknown', 0.0)
                sorted_scores = {}
            
            # Detect frameworks
            frameworks = self.detect_frameworks(repo_path, scan_data)
            
            # Get top file extensions
            top_extensions = dict(sorted(
                scan_data['file_extensions'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10])
            
            result = {
                'status': 'success',
                'primary_type': primary_type[0] if primary_type[1] > 1.0 else 'unknown',
                'confidence': primary_type[1],
                'all_scores': sorted_scores,
                'detected_frameworks': frameworks,
                'file_statistics': {
                    'total_files': scan_data['total_files'],
                    'top_extensions': top_extensions,
                    'directory_count': len(scan_data['directory_structure'])
                },
                'key_files': list(scan_data['found_files'])[:20],  # Limit output
                'directory_structure': scan_data['directory_structure'][:20]  # Limit output
            }
            
            console.print(f"[green]✅ Project analysis complete. Primary type: {result['primary_type']}[/green]")
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing project: {str(e)}[/red]")
            return {
                'error': str(e),
                'status': 'error'
            }


# Global detector instance
project_detector = ProjectTypeDetector()


@tool
def detect_project_type_tool(repo_path: Optional[str] = None) -> str:
    """
    Detect the programming language and project type of a repository.
    
    Args:
        repo_path: Optional path to repository. If not provided, uses the currently loaded repository.
    
    Returns:
        Detailed analysis of the project type, languages, frameworks, and file statistics.
    """
    result = project_detector.analyze_project_type(repo_path)
    
    if result['status'] == 'error':
        return f"Error analyzing project: {result['error']}"
    
    # Format the result for LangChain
    output = f"""Project Type Analysis Results:

Primary Type: {result['primary_type']} (confidence: {result['confidence']:.1f})

Language Scores:
"""
    
    for lang, score in list(result['all_scores'].items())[:5]:
        output += f"  - {lang}: {score:.1f}\n"
    
    if result['detected_frameworks']:
        output += f"\nDetected Frameworks: {', '.join(result['detected_frameworks'])}\n"
    
    output += f"""
File Statistics:
  - Total files: {result['file_statistics']['total_files']}
  - Top extensions: {result['file_statistics']['top_extensions']}
  - Directory count: {result['file_statistics']['directory_count']}

Key files found: {', '.join(result['key_files'][:10])}
"""
    
    return output


if __name__ == "__main__":
    # Test the tool
    console.print("[bold blue]Testing Project Type Detector Tool[/bold blue]")
    
    # Test with current directory
    test_path = "/home/ubuntu/sem"
    console.print(f"\n[yellow]Testing with path: {test_path}[/yellow]")
    result = detect_project_type_tool(test_path)
    console.print(result)
