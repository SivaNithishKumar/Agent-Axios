"""
Dependency Extractor Tool for parsing and analyzing project dependencies.
Supports multiple dependency formats: requirements.txt, package.json, Pipfile, pom.xml, etc.
"""

import os
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any
from langchain.tools import tool
from rich.console import Console
import toml
import yaml

console = Console()


class DependencyExtractor:
    """Class to extract and analyze project dependencies."""
    
    def __init__(self):
        """Initialize the dependency extractor."""
        self.supported_files = {
            'python': ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py', 'environment.yml'],
            'nodejs': ['package.json', 'yarn.lock', 'package-lock.json'],
            'java': ['pom.xml', 'build.gradle', 'gradle.properties'],
            'php': ['composer.json', 'composer.lock'],
            'ruby': ['Gemfile', 'Gemfile.lock', '*.gemspec'],
            'go': ['go.mod', 'go.sum'],
            'rust': ['Cargo.toml', 'Cargo.lock'],
            'csharp': ['packages.config', '*.csproj', '*.sln']
        }
    
    def find_dependency_files(self, repo_path: str) -> Dict[str, List[str]]:
        """Find all dependency files in the repository."""
        found_files = {}
        
        if not os.path.exists(repo_path):
            return found_files
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and common build directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # Check against known dependency files
                    for lang, patterns in self.supported_files.items():
                        for pattern in patterns:
                            if '*' in pattern:
                                # Handle wildcard patterns
                                pattern_regex = pattern.replace('*', '.*')
                                if re.match(pattern_regex, file):
                                    if lang not in found_files:
                                        found_files[lang] = []
                                    found_files[lang].append(rel_path)
                            else:
                                if file == pattern:
                                    if lang not in found_files:
                                        found_files[lang] = []
                                    found_files[lang].append(rel_path)
        
        except Exception as e:
            console.print(f"[red]Error scanning for dependency files: {str(e)}[/red]")
        
        return found_files
    
    def parse_requirements_txt(self, file_path: str) -> Dict:
        """Parse Python requirements.txt file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip -r includes and other pip options
                    if line.startswith('-'):
                        continue
                    
                    # Parse package specification
                    # Handle various formats: package, package==1.0, package>=1.0, etc.
                    match = re.match(r'^([a-zA-Z0-9_.-]+)([<>=!]+.*)?', line)
                    if match:
                        package_name = match.group(1)
                        version_spec = match.group(2) or ''
                        
                        dependencies.append({
                            'name': package_name,
                            'version': version_spec,
                            'line': line_num,
                            'raw': line
                        })
        
        except Exception as e:
            return {'error': str(e)}
        
        return {
            'type': 'requirements.txt',
            'dependencies': dependencies,
            'count': len(dependencies)
        }
    
    def parse_package_json(self, file_path: str) -> Dict:
        """Parse Node.js package.json file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dependencies = []
            dev_dependencies = []
            
            # Parse dependencies
            if 'dependencies' in data:
                for name, version in data['dependencies'].items():
                    dependencies.append({
                        'name': name,
                        'version': version,
                        'type': 'production'
                    })
            
            # Parse devDependencies
            if 'devDependencies' in data:
                for name, version in data['devDependencies'].items():
                    dev_dependencies.append({
                        'name': name,
                        'version': version,
                        'type': 'development'
                    })
            
            # Extract other useful information
            scripts = data.get('scripts', {})
            engines = data.get('engines', {})
            
            return {
                'type': 'package.json',
                'name': data.get('name', 'unknown'),
                'version': data.get('version', 'unknown'),
                'description': data.get('description', ''),
                'dependencies': dependencies,
                'dev_dependencies': dev_dependencies,
                'scripts': scripts,
                'engines': engines,
                'count': len(dependencies) + len(dev_dependencies)
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def parse_pipfile(self, file_path: str) -> Dict:
        """Parse Python Pipfile."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            dependencies = []
            dev_dependencies = []
            
            # Parse packages
            if 'packages' in data:
                for name, version in data['packages'].items():
                    if isinstance(version, dict):
                        version_str = version.get('version', '*')
                    else:
                        version_str = str(version)
                    
                    dependencies.append({
                        'name': name,
                        'version': version_str,
                        'type': 'production'
                    })
            
            # Parse dev-packages
            if 'dev-packages' in data:
                for name, version in data['dev-packages'].items():
                    if isinstance(version, dict):
                        version_str = version.get('version', '*')
                    else:
                        version_str = str(version)
                    
                    dev_dependencies.append({
                        'name': name,
                        'version': version_str,
                        'type': 'development'
                    })
            
            return {
                'type': 'Pipfile',
                'dependencies': dependencies,
                'dev_dependencies': dev_dependencies,
                'python_version': data.get('requires', {}).get('python_version', 'unknown'),
                'count': len(dependencies) + len(dev_dependencies)
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def parse_pyproject_toml(self, file_path: str) -> Dict:
        """Parse Python pyproject.toml file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            dependencies = []
            dev_dependencies = []
            
            # Check for different sections where dependencies might be
            # Poetry format
            if 'tool' in data and 'poetry' in data['tool']:
                poetry_data = data['tool']['poetry']
                
                if 'dependencies' in poetry_data:
                    for name, version in poetry_data['dependencies'].items():
                        if name == 'python':
                            continue
                        
                        if isinstance(version, dict):
                            version_str = version.get('version', '*')
                        else:
                            version_str = str(version)
                        
                        dependencies.append({
                            'name': name,
                            'version': version_str,
                            'type': 'production'
                        })
                
                if 'dev-dependencies' in poetry_data:
                    for name, version in poetry_data['dev-dependencies'].items():
                        if isinstance(version, dict):
                            version_str = version.get('version', '*')
                        else:
                            version_str = str(version)
                        
                        dev_dependencies.append({
                            'name': name,
                            'version': version_str,
                            'type': 'development'
                        })
            
            # PEP 621 format
            if 'project' in data:
                project_data = data['project']
                
                if 'dependencies' in project_data:
                    for dep in project_data['dependencies']:
                        # Parse dependency specification
                        match = re.match(r'^([a-zA-Z0-9_.-]+)([<>=!]+.*)?', dep)
                        if match:
                            name = match.group(1)
                            version = match.group(2) or ''
                            
                            dependencies.append({
                                'name': name,
                                'version': version,
                                'type': 'production'
                            })
            
            return {
                'type': 'pyproject.toml',
                'dependencies': dependencies,
                'dev_dependencies': dev_dependencies,
                'count': len(dependencies) + len(dev_dependencies)
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def parse_pom_xml(self, file_path: str) -> Dict:
        """Parse Java pom.xml file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle namespace
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            if root.tag.startswith('{'):
                ns = root.tag[1:].split('}')[0]
                namespace['maven'] = ns
            
            dependencies = []
            
            # Find dependencies
            deps = root.findall('.//maven:dependency', namespace) or root.findall('.//dependency')
            
            for dep in deps:
                group_id = dep.find('maven:groupId', namespace) or dep.find('groupId')
                artifact_id = dep.find('maven:artifactId', namespace) or dep.find('artifactId')
                version = dep.find('maven:version', namespace) or dep.find('version')
                scope = dep.find('maven:scope', namespace) or dep.find('scope')
                
                if group_id is not None and artifact_id is not None:
                    dependencies.append({
                        'groupId': group_id.text if group_id.text else '',
                        'artifactId': artifact_id.text if artifact_id.text else '',
                        'version': version.text if version is not None and version.text else 'unknown',
                        'scope': scope.text if scope is not None and scope.text else 'compile',
                        'name': f"{group_id.text}:{artifact_id.text}" if group_id.text and artifact_id.text else 'unknown'
                    })
            
            return {
                'type': 'pom.xml',
                'dependencies': dependencies,
                'count': len(dependencies)
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_dependencies(self, repo_path: str) -> Dict:
        """Analyze all dependencies in the repository."""
        console.print(f"[blue]🔍 Analyzing dependencies in: {repo_path}[/blue]")
        
        # Find all dependency files
        found_files = self.find_dependency_files(repo_path)
        
        if not found_files:
            return {
                'status': 'success',
                'message': 'No dependency files found',
                'languages': [],
                'total_dependencies': 0,
                'files_analyzed': {}
            }
        
        results = {}
        total_dependencies = 0
        
        for language, files in found_files.items():
            results[language] = {}
            
            for file_path in files:
                full_path = os.path.join(repo_path, file_path)
                file_name = os.path.basename(file_path)
                
                try:
                    if file_name == 'requirements.txt':
                        result = self.parse_requirements_txt(full_path)
                    elif file_name == 'package.json':
                        result = self.parse_package_json(full_path)
                    elif file_name == 'Pipfile':
                        result = self.parse_pipfile(full_path)
                    elif file_name == 'pyproject.toml':
                        result = self.parse_pyproject_toml(full_path)
                    elif file_name == 'pom.xml':
                        result = self.parse_pom_xml(full_path)
                    else:
                        result = {'type': file_name, 'message': 'Parser not implemented'}
                    
                    results[language][file_path] = result
                    
                    if 'count' in result:
                        total_dependencies += result['count']
                
                except Exception as e:
                    results[language][file_path] = {'error': str(e)}
        
        console.print(f"[green]✅ Dependency analysis complete. Found {total_dependencies} dependencies[/green]")
        
        return {
            'status': 'success',
            'languages': list(found_files.keys()),
            'total_dependencies': total_dependencies,
            'files_analyzed': results,
            'summary': self._create_summary(results)
        }
    
    def _create_summary(self, results: Dict) -> Dict:
        """Create a summary of the dependency analysis."""
        summary = {
            'by_language': {},
            'most_common_packages': {},
            'dependency_counts': {}
        }
        
        for language, files in results.items():
            lang_deps = 0
            packages = []
            
            for file_path, data in files.items():
                if 'dependencies' in data:
                    lang_deps += len(data['dependencies'])
                    packages.extend([dep['name'] for dep in data['dependencies']])
                
                if 'dev_dependencies' in data:
                    lang_deps += len(data['dev_dependencies'])
                    packages.extend([dep['name'] for dep in data['dev_dependencies']])
                
                if 'count' in data:
                    lang_deps += data['count']
            
            summary['by_language'][language] = lang_deps
            summary['dependency_counts'][language] = lang_deps
            
            # Count package frequency
            from collections import Counter
            if packages:
                summary['most_common_packages'][language] = dict(Counter(packages).most_common(10))
        
        return summary


# Global extractor instance
dependency_extractor = DependencyExtractor()


@tool
def extract_dependencies_tool(repo_path: Optional[str] = None) -> str:
    """
    Extract and analyze dependencies from various dependency files in a repository.
    
    Args:
        repo_path: Optional path to repository. If not provided, uses the currently loaded repository.
    
    Returns:
        Detailed analysis of all dependencies found in the repository.
    """
    # For now, use provided path or current directory
    if repo_path is None:
        repo_path = os.getcwd()
    
    result = dependency_extractor.analyze_dependencies(repo_path)
    
    if result['status'] != 'success':
        return f"Error analyzing dependencies: {result.get('error', 'Unknown error')}"
    
    # Format the result for LangChain
    output = f"""Dependency Analysis Results:

Languages detected: {', '.join(result['languages']) if result['languages'] else 'None'}
Total dependencies: {result['total_dependencies']}

"""
    
    if result['languages']:
        output += "Dependencies by language:\n"
        for lang, count in result['summary']['dependency_counts'].items():
            output += f"  - {lang}: {count} dependencies\n"
        
        output += "\nFiles analyzed:\n"
        for lang, files in result['files_analyzed'].items():
            output += f"\n{lang.upper()}:\n"
            for file_path, data in files.items():
                if 'error' in data:
                    output += f"  - {file_path}: Error - {data['error']}\n"
                else:
                    count = data.get('count', 0)
                    output += f"  - {file_path}: {count} dependencies\n"
        
        # Show most common packages
        if result['summary']['most_common_packages']:
            output += "\nMost common packages:\n"
            for lang, packages in result['summary']['most_common_packages'].items():
                if packages:
                    output += f"  {lang}: {', '.join(list(packages.keys())[:5])}\n"
    
    return output


if __name__ == "__main__":
    # Test the tool
    console.print("[bold blue]Testing Dependency Extractor Tool[/bold blue]")
    
    # Test with current directory
    test_path = "/home/ubuntu/sem"
    console.print(f"\n[yellow]Testing with path: {test_path}[/yellow]")
    result = extract_dependencies_tool(test_path)
    console.print(result)
