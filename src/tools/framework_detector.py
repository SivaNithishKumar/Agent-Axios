"""
Framework Detector Tool for identifying frameworks and libraries used in a project.
Analyzes imports, configuration files, and patterns to detect popular frameworks.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict, Counter
from langchain.tools import tool
from rich.console import Console

console = Console()


class FrameworkDetector:
    """Class to detect frameworks and libraries used in a project."""
    
    def __init__(self):
        """Initialize the framework detector."""
        # Framework detection patterns
        self.framework_patterns = {
            # Python frameworks
            'django': {
                'imports': ['django', 'from django'],
                'files': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
                'directories': ['migrations', 'templates'],
                'configs': ['settings/', 'django.conf']
            },
            'flask': {
                'imports': ['flask', 'from flask'],
                'files': ['app.py', 'application.py'],
                'directories': ['templates', 'static'],
                'configs': ['config.py', 'instance/']
            },
            'fastapi': {
                'imports': ['fastapi', 'from fastapi'],
                'files': ['main.py', 'app.py'],
                'directories': ['routers', 'schemas'],
                'configs': ['uvicorn', 'gunicorn']
            },
            'streamlit': {
                'imports': ['streamlit', 'import streamlit as st'],
                'files': ['streamlit_app.py', 'app.py'],
                'directories': ['.streamlit'],
                'configs': ['config.toml']
            },
            
            # JavaScript/TypeScript frameworks
            'react': {
                'imports': ['react', 'from react', '@types/react'],
                'files': ['package.json'],
                'directories': ['src', 'public', 'components'],
                'configs': ['react-scripts', 'create-react-app']
            },
            'vue': {
                'imports': ['vue', '@vue'],
                'files': ['vue.config.js', 'package.json'],
                'directories': ['src', 'components'],
                'configs': ['@vue/cli', 'vite']
            },
            'angular': {
                'imports': ['@angular', 'angular'],
                'files': ['angular.json', 'package.json'],
                'directories': ['src/app', 'e2e'],
                'configs': ['ng', '@angular/cli']
            },
            'express': {
                'imports': ['express', 'require(\'express\')'],
                'files': ['server.js', 'app.js', 'index.js'],
                'directories': ['routes', 'middleware'],
                'configs': ['express']
            },
            'nextjs': {
                'imports': ['next', 'next/'],
                'files': ['next.config.js', 'package.json'],
                'directories': ['pages', 'components', 'public'],
                'configs': ['next']
            },
            
            # Java frameworks
            'spring': {
                'imports': ['org.springframework', 'springframework'],
                'files': ['pom.xml', 'application.properties'],
                'directories': ['src/main/java', 'src/main/resources'],
                'configs': ['spring-boot', '@SpringBootApplication']
            },
            'spring_boot': {
                'imports': ['org.springframework.boot', 'SpringBootApplication'],
                'files': ['application.yml', 'application.properties'],
                'directories': ['src/main/java'],
                'configs': ['spring-boot-starter']
            },
            
            # Go frameworks
            'gin': {
                'imports': ['gin-gonic/gin', 'github.com/gin-gonic/gin'],
                'files': ['go.mod', 'main.go'],
                'directories': ['handlers', 'middleware'],
                'configs': ['gin']
            },
            'echo': {
                'imports': ['labstack/echo', 'github.com/labstack/echo'],
                'files': ['go.mod', 'main.go'],
                'directories': ['handlers'],
                'configs': ['echo']
            },
            
            # PHP frameworks
            'laravel': {
                'imports': ['Illuminate\\', 'Laravel\\'],
                'files': ['artisan', 'composer.json'],
                'directories': ['app', 'resources', 'routes'],
                'configs': ['laravel/framework']
            },
            'symfony': {
                'imports': ['Symfony\\', 'symfony/'],
                'files': ['composer.json', 'symfony.lock'],
                'directories': ['src', 'config', 'templates'],
                'configs': ['symfony/framework-bundle']
            },
            
            # Ruby frameworks
            'rails': {
                'imports': ['Rails', 'rails'],
                'files': ['Gemfile', 'config.ru'],
                'directories': ['app', 'config', 'db'],
                'configs': ['rails']
            },
            
            # Rust frameworks
            'actix': {
                'imports': ['actix-web', 'actix_web'],
                'files': ['Cargo.toml'],
                'directories': ['src'],
                'configs': ['actix-web']
            },
            'rocket': {
                'imports': ['rocket', '#[macro_use] extern crate rocket'],
                'files': ['Cargo.toml'],
                'directories': ['src'],
                'configs': ['rocket']
            }
        }
        
        # File extension to language mapping
        self.language_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c'
        }
    
    def scan_imports_in_file(self, file_path: str, language: str) -> List[str]:
        """Scan imports in a source code file."""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if language == 'python':
                    # Python imports
                    import_patterns = [
                        r'import\s+([a-zA-Z0-9_\.]+)',
                        r'from\s+([a-zA-Z0-9_\.]+)\s+import',
                        r'import\s+([a-zA-Z0-9_\.]+)\s+as'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        imports.extend(matches)
                
                elif language in ['javascript', 'typescript']:
                    # JavaScript/TypeScript imports
                    import_patterns = [
                        r'import.*from\s+[\'"]([^\'\"]+)[\'"]',
                        r'require\([\'"]([^\'\"]+)[\'"]\)',
                        r'import\([\'"]([^\'\"]+)[\'"]\)'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        imports.extend(matches)
                
                elif language == 'java':
                    # Java imports
                    import_pattern = r'import\s+([a-zA-Z0-9_\.]+);'
                    matches = re.findall(import_pattern, content)
                    imports.extend(matches)
                
                elif language == 'go':
                    # Go imports
                    import_patterns = [
                        r'import\s+"([^"]+)"',
                        r'import\s+\(\s*"([^"]+)"',
                        r'"([^"]+)"\s*\n'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        imports.extend(matches)
                
                elif language == 'php':
                    # PHP use statements
                    import_patterns = [
                        r'use\s+([a-zA-Z0-9_\\]+);',
                        r'require_once\s+[\'"]([^\'\"]+)[\'"]',
                        r'include_once\s+[\'"]([^\'\"]+)[\'"]'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        imports.extend(matches)
        
        except Exception:
            pass  # Ignore files that can't be read
        
        return imports
    
    def analyze_package_files(self, repo_path: str) -> Dict[str, List[str]]:
        """Analyze package/dependency files for framework indicators."""
        dependencies = []
        
        # Check package.json
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    
                    dependencies.extend(deps.keys())
                    dependencies.extend(dev_deps.keys())
            except Exception:
                pass
        
        # Check requirements.txt
        requirements_path = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('-'):
                            # Extract package name
                            match = re.match(r'^([a-zA-Z0-9_.-]+)', line)
                            if match:
                                dependencies.append(match.group(1))
            except Exception:
                pass
        
        # Check Cargo.toml
        cargo_path = os.path.join(repo_path, 'Cargo.toml')
        if os.path.exists(cargo_path):
            try:
                with open(cargo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple extraction of dependencies
                    in_deps_section = False
                    for line in content.split('\n'):
                        line = line.strip()
                        if line == '[dependencies]':
                            in_deps_section = True
                        elif line.startswith('[') and line != '[dependencies]':
                            in_deps_section = False
                        elif in_deps_section and '=' in line:
                            dep_name = line.split('=')[0].strip().strip('"')
                            dependencies.append(dep_name)
            except Exception:
                pass
        
        return {'dependencies': dependencies}
    
    def detect_frameworks_from_patterns(self, repo_path: str) -> Dict[str, Dict]:
        """Detect frameworks based on file patterns and content analysis."""
        detected_frameworks = {}
        
        # Collect all imports from source files
        all_imports = []
        all_files = []
        all_directories = set()
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden and build directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'target', 'build']]
                
                # Collect directory names
                for dir_name in dirs:
                    all_directories.add(dir_name)
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_file_path = os.path.relpath(file_path, repo_path)
                    all_files.append(rel_file_path)
                    
                    # Analyze source files for imports
                    ext = Path(file).suffix.lower()
                    if ext in self.language_extensions:
                        language = self.language_extensions[ext]
                        imports = self.scan_imports_in_file(file_path, language)
                        all_imports.extend(imports)
        
        except Exception as e:
            console.print(f"[red]Error scanning repository: {str(e)}[/red]")
        
        # Analyze package files
        package_analysis = self.analyze_package_files(repo_path)
        all_dependencies = package_analysis.get('dependencies', [])
        
        # Check each framework against patterns
        for framework, patterns in self.framework_patterns.items():
            score = 0
            evidence = []
            
            # Check import patterns
            for import_pattern in patterns.get('imports', []):
                matching_imports = [imp for imp in all_imports if import_pattern.lower() in imp.lower()]
                if matching_imports:
                    score += len(matching_imports) * 2
                    evidence.append(f"Imports: {', '.join(matching_imports[:3])}")
            
            # Check file patterns
            for file_pattern in patterns.get('files', []):
                matching_files = [f for f in all_files if file_pattern in f]
                if matching_files:
                    score += len(matching_files) * 3
                    evidence.append(f"Files: {', '.join(matching_files[:3])}")
            
            # Check directory patterns
            for dir_pattern in patterns.get('directories', []):
                if dir_pattern in all_directories:
                    score += 2
                    evidence.append(f"Directory: {dir_pattern}")
            
            # Check configuration/dependency patterns
            for config_pattern in patterns.get('configs', []):
                matching_deps = [dep for dep in all_dependencies if config_pattern.lower() in dep.lower()]
                if matching_deps:
                    score += len(matching_deps) * 2
                    evidence.append(f"Dependencies: {', '.join(matching_deps[:3])}")
            
            # If score is high enough, consider framework detected
            if score >= 2:
                detected_frameworks[framework] = {
                    'score': score,
                    'confidence': min(score / 10.0, 1.0),
                    'evidence': evidence
                }
        
        return detected_frameworks
    
    def analyze_frameworks(self, repo_path: str) -> Dict:
        """Analyze frameworks used in the repository."""
        console.print(f"[blue]🔍 Detecting frameworks in: {repo_path}[/blue]")
        
        try:
            # Detect frameworks
            detected_frameworks = self.detect_frameworks_from_patterns(repo_path)
            
            # Sort by confidence score
            sorted_frameworks = dict(sorted(
                detected_frameworks.items(), 
                key=lambda x: x[1]['score'], 
                reverse=True
            ))
            
            # Categorize by confidence level
            high_confidence = {k: v for k, v in sorted_frameworks.items() if v['confidence'] >= 0.7}
            medium_confidence = {k: v for k, v in sorted_frameworks.items() if 0.3 <= v['confidence'] < 0.7}
            low_confidence = {k: v for k, v in sorted_frameworks.items() if v['confidence'] < 0.3}
            
            result = {
                'status': 'success',
                'total_detected': len(detected_frameworks),
                'frameworks': {
                    'high_confidence': high_confidence,
                    'medium_confidence': medium_confidence,
                    'low_confidence': low_confidence
                },
                'all_frameworks': sorted_frameworks,
                'primary_frameworks': list(high_confidence.keys())[:3]
            }
            
            console.print(f"[green]✅ Framework detection complete. Found {len(detected_frameworks)} frameworks[/green]")
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Error detecting frameworks: {str(e)}[/red]")
            return {
                'status': 'error',
                'error': str(e)
            }


# Global detector instance
framework_detector = FrameworkDetector()


@tool
def detect_frameworks_tool(repo_path: Optional[str] = None) -> str:
    """
    Detect frameworks and libraries used in a repository by analyzing imports, files, and configurations.
    
    Args:
        repo_path: Optional path to repository. If not provided, uses current directory.
    
    Returns:
        Detailed analysis of detected frameworks with confidence scores and evidence.
    """
    if repo_path is None:
        repo_path = os.getcwd()
    
    result = framework_detector.analyze_frameworks(repo_path)
    
    if result['status'] == 'error':
        return f"Error detecting frameworks: {result['error']}"
    
    # Format the result for LangChain
    output = f"""Framework Detection Results:

Total frameworks detected: {result['total_detected']}
Primary frameworks: {', '.join(result['primary_frameworks']) if result['primary_frameworks'] else 'None detected'}

"""
    
    # High confidence frameworks
    if result['frameworks']['high_confidence']:
        output += "HIGH CONFIDENCE FRAMEWORKS:\n"
        for name, info in result['frameworks']['high_confidence'].items():
            output += f"  {name} (confidence: {info['confidence']:.2f})\n"
            for evidence in info['evidence']:
                output += f"    - {evidence}\n"
        output += "\n"
    
    # Medium confidence frameworks
    if result['frameworks']['medium_confidence']:
        output += "MEDIUM CONFIDENCE FRAMEWORKS:\n"
        for name, info in result['frameworks']['medium_confidence'].items():
            output += f"  {name} (confidence: {info['confidence']:.2f})\n"
        output += "\n"
    
    # Low confidence frameworks
    if result['frameworks']['low_confidence']:
        output += "LOW CONFIDENCE FRAMEWORKS:\n"
        framework_names = list(result['frameworks']['low_confidence'].keys())[:5]
        output += f"  {', '.join(framework_names)}\n"
        if len(result['frameworks']['low_confidence']) > 5:
            output += f"  (and {len(result['frameworks']['low_confidence']) - 5} more)\n"
    
    if not result['total_detected']:
        output += "No frameworks detected with sufficient confidence.\n"
    
    return output


if __name__ == "__main__":
    # Test the tool
    console.print("[bold blue]Testing Framework Detector Tool[/bold blue]")
    
    # Test with current directory
    test_path = "/home/ubuntu/sem"
    console.print(f"\n[yellow]Testing with path: {test_path}[/yellow]")
    result = framework_detector.analyze_frameworks(test_path)
    
    if result['status'] == 'success':
        print(f"Detected {result['total_detected']} frameworks")
        print(f"Primary: {result['primary_frameworks']}")
        print(f"High confidence: {list(result['frameworks']['high_confidence'].keys())}")
    else:
        print(f"Error: {result['error']}")
