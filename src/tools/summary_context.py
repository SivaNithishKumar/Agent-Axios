"""
Summary Context Tool for aggregating all repository analysis results.
Combines results from all other tools into a structured format for LLM consumption.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from langchain.tools import tool
from rich.console import Console

console = Console()


class SummaryContextGenerator:
    """Class to generate comprehensive repository analysis summaries."""
    
    def __init__(self):
        """Initialize the summary context generator."""
        pass
    
    def aggregate_analysis_results(self, repo_path: str) -> Dict[str, Any]:
        """Aggregate results from all analysis tools."""
        console.print(f"[blue]📊 Aggregating analysis results for: {repo_path}[/blue]")
        
        summary = {
            'metadata': {
                'repo_path': repo_path,
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.0.0'
            },
            'repository_info': {},
            'project_type': {},
            'dependencies': {},
            'structure': {},
            'frameworks': {},
            'config_files': {},
            'summary_stats': {},
            'recommendations': []
        }
        
        try:
            # Import and run each analysis tool
            from .repo_loader import repo_loader
            from .project_detector import project_detector
            from .dependency_extractor import dependency_extractor
            from .structure_mapper import structure_mapper
            from .framework_detector import framework_detector
            
            # Repository Info
            if hasattr(repo_loader, 'repo_info') and repo_loader.repo_info:
                summary['repository_info'] = repo_loader.repo_info
            
            # Project Type Analysis
            project_analysis = project_detector.analyze_project_type(repo_path)
            if project_analysis['status'] == 'success':
                summary['project_type'] = {
                    'primary_type': project_analysis['primary_type'],
                    'confidence': project_analysis['confidence'],
                    'all_scores': project_analysis['all_scores'],
                    'detected_frameworks': project_analysis['detected_frameworks'],
                    'file_statistics': project_analysis['file_statistics']
                }
            
            # Dependency Analysis
            dependency_analysis = dependency_extractor.analyze_dependencies(repo_path)
            if dependency_analysis['status'] == 'success':
                summary['dependencies'] = {
                    'languages': dependency_analysis['languages'],
                    'total_dependencies': dependency_analysis['total_dependencies'],
                    'summary': dependency_analysis['summary'],
                    'files_count': len(dependency_analysis['files_analyzed'])
                }
            
            # Structure Analysis
            structure_analysis = structure_mapper.create_structure_summary(repo_path)
            if structure_analysis['status'] == 'success':
                summary['structure'] = {
                    'summary': structure_analysis['summary'],
                    'important_directories': structure_analysis['important_directories'],
                    'entry_points': structure_analysis['entry_points'],
                    'config_files': structure_analysis['config_files'],
                    'file_analysis': structure_analysis['file_analysis']
                }
            
            # Framework Analysis
            framework_analysis = framework_detector.analyze_frameworks(repo_path)
            if framework_analysis['status'] == 'success':
                summary['frameworks'] = {
                    'total_detected': framework_analysis['total_detected'],
                    'primary_frameworks': framework_analysis['primary_frameworks'],
                    'high_confidence': list(framework_analysis['frameworks']['high_confidence'].keys()),
                    'medium_confidence': list(framework_analysis['frameworks']['medium_confidence'].keys()),
                    'all_frameworks': framework_analysis['all_frameworks']
                }
            
            # Calculate summary statistics
            summary['summary_stats'] = self._calculate_summary_stats(summary)
            
            # Generate recommendations
            summary['recommendations'] = self._generate_recommendations(summary)
            
            console.print("[green]✅ Analysis aggregation complete[/green]")
            return summary
            
        except Exception as e:
            console.print(f"[red]❌ Error aggregating analysis: {str(e)}[/red]")
            return {
                'metadata': summary['metadata'],
                'error': str(e),
                'status': 'error'
            }
    
    def _calculate_summary_stats(self, summary: Dict) -> Dict:
        """Calculate high-level summary statistics."""
        stats = {
            'total_files': 0,
            'total_directories': 0,
            'total_dependencies': 0,
            'primary_language': 'unknown',
            'project_complexity': 'unknown',
            'has_tests': False,
            'has_documentation': False,
            'has_ci_cd': False,
            'has_docker': False
        }
        
        try:
            # File and directory counts
            if 'structure' in summary and 'summary' in summary['structure']:
                stats['total_files'] = summary['structure']['summary'].get('total_files', 0)
                stats['total_directories'] = summary['structure']['summary'].get('total_directories', 0)
            
            # Dependencies
            if 'dependencies' in summary:
                stats['total_dependencies'] = summary['dependencies'].get('total_dependencies', 0)
            
            # Primary language
            if 'project_type' in summary:
                stats['primary_language'] = summary['project_type'].get('primary_type', 'unknown')
            
            # Project complexity assessment
            file_count = stats['total_files']
            dep_count = stats['total_dependencies']
            
            if file_count < 50 and dep_count < 10:
                stats['project_complexity'] = 'simple'
            elif file_count < 200 and dep_count < 50:
                stats['project_complexity'] = 'medium'
            else:
                stats['project_complexity'] = 'complex'
            
            # Feature detection
            if 'structure' in summary and 'important_directories' in summary['structure']:
                dirs = summary['structure']['important_directories']
                stats['has_tests'] = bool(dirs.get('tests', []))
                stats['has_documentation'] = bool(dirs.get('docs', []))
            
            if 'structure' in summary and 'config_files' in summary['structure']:
                configs = summary['structure']['config_files']
                stats['has_ci_cd'] = bool(configs.get('ci_cd', []))
                stats['has_docker'] = bool(configs.get('docker', []))
            
        except Exception as e:
            stats['calculation_error'] = str(e)
        
        return stats
    
    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        try:
            stats = summary.get('summary_stats', {})
            structure = summary.get('structure', {})
            
            # Testing recommendations
            if not stats.get('has_tests', False):
                recommendations.append("Consider adding unit tests to improve code quality and reliability")
            
            # Documentation recommendations
            if not stats.get('has_documentation', False):
                recommendations.append("Add documentation (README, API docs) to improve project maintainability")
            
            # CI/CD recommendations
            if not stats.get('has_ci_cd', False):
                recommendations.append("Set up CI/CD pipeline for automated testing and deployment")
            
            # Docker recommendations
            if not stats.get('has_docker', False) and stats.get('project_complexity') != 'simple':
                recommendations.append("Consider containerizing the application with Docker")
            
            # Security recommendations
            env_files = structure.get('config_files', {}).get('env', [])
            if env_files:
                recommendations.append("Ensure environment files are properly secured and not committed to version control")
            
            # Dependency recommendations
            dep_count = stats.get('total_dependencies', 0)
            if dep_count > 100:
                recommendations.append("Review dependencies to minimize security surface and improve build times")
            
            # Structure recommendations
            entry_points = structure.get('entry_points', {})
            if not entry_points:
                recommendations.append("Consider defining clear entry points for the application")
            
        except Exception as e:
            recommendations.append(f"Error generating recommendations: {str(e)}")
        
        return recommendations
    
    def format_for_llm(self, summary: Dict) -> str:
        """Format the summary for LLM consumption."""
        if 'error' in summary:
            return f"Error in analysis: {summary['error']}"
        
        formatted = f"""# Repository Analysis Summary

## Metadata
- Repository: {summary['metadata']['repo_path']}
- Analysis Date: {summary['metadata']['analysis_timestamp']}
- Analyzer Version: {summary['metadata']['analyzer_version']}

## Project Overview
- **Primary Language**: {summary['summary_stats'].get('primary_language', 'Unknown')}
- **Project Type**: {summary['project_type'].get('primary_type', 'Unknown')}
- **Complexity**: {summary['summary_stats'].get('project_complexity', 'Unknown')}
- **Total Files**: {summary['summary_stats'].get('total_files', 0)}
- **Total Dependencies**: {summary['summary_stats'].get('total_dependencies', 0)}

## Structure Analysis
"""
        
        # Important directories
        if summary.get('structure', {}).get('important_directories'):
            formatted += "### Important Directories\n"
            for category, dirs in summary['structure']['important_directories'].items():
                if dirs:
                    formatted += f"- **{category.title()}**: {', '.join(dirs)}\n"
        
        # Entry points
        if summary.get('structure', {}).get('entry_points'):
            formatted += "\n### Entry Points\n"
            for lang, files in summary['structure']['entry_points'].items():
                if files:
                    formatted += f"- **{lang}**: {', '.join(files)}\n"
        
        # Dependencies
        if summary.get('dependencies', {}).get('languages'):
            formatted += f"\n## Dependencies\n"
            formatted += f"- **Languages**: {', '.join(summary['dependencies']['languages'])}\n"
            formatted += f"- **Total Dependencies**: {summary['dependencies']['total_dependencies']}\n"
        
        # Frameworks
        if summary.get('frameworks', {}).get('primary_frameworks'):
            formatted += f"\n## Frameworks\n"
            formatted += f"- **Primary**: {', '.join(summary['frameworks']['primary_frameworks'])}\n"
            if summary['frameworks'].get('high_confidence'):
                formatted += f"- **High Confidence**: {', '.join(summary['frameworks']['high_confidence'])}\n"
        
        # Configuration
        if summary.get('structure', {}).get('config_files'):
            formatted += f"\n## Configuration\n"
            for config_type, files in summary['structure']['config_files'].items():
                if files:
                    formatted += f"- **{config_type.replace('_', ' ').title()}**: {len(files)} files\n"
        
        # Features
        formatted += f"\n## Project Features\n"
        formatted += f"- **Has Tests**: {'Yes' if summary['summary_stats'].get('has_tests') else 'No'}\n"
        formatted += f"- **Has Documentation**: {'Yes' if summary['summary_stats'].get('has_documentation') else 'No'}\n"
        formatted += f"- **Has CI/CD**: {'Yes' if summary['summary_stats'].get('has_ci_cd') else 'No'}\n"
        formatted += f"- **Has Docker**: {'Yes' if summary['summary_stats'].get('has_docker') else 'No'}\n"
        
        # Recommendations
        if summary.get('recommendations'):
            formatted += f"\n## Recommendations\n"
            for i, rec in enumerate(summary['recommendations'], 1):
                formatted += f"{i}. {rec}\n"
        
        return formatted
    
    def export_json(self, summary: Dict, output_path: str) -> bool:
        """Export summary to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)
            console.print(f"[green]✅ Summary exported to {output_path}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error exporting summary: {str(e)}[/red]")
            return False
    
    def export_markdown(self, summary: Dict, output_path: str) -> bool:
        """Export summary to Markdown file."""
        try:
            formatted_content = self.format_for_llm(summary)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            console.print(f"[green]✅ Summary exported to {output_path}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error exporting summary: {str(e)}[/red]")
            return False


# Global generator instance
summary_generator = SummaryContextGenerator()


@tool
def generate_summary_context_tool(repo_path: Optional[str] = None) -> str:
    """
    Generate a comprehensive summary of all repository analysis results.
    
    Args:
        repo_path: Optional path to repository. If not provided, uses current directory.
    
    Returns:
        Comprehensive formatted summary of all analysis results ready for LLM processing.
    """
    if repo_path is None:
        repo_path = os.getcwd()
    
    # Generate the summary
    summary = summary_generator.aggregate_analysis_results(repo_path)
    
    # Format for LLM
    formatted_summary = summary_generator.format_for_llm(summary)
    
    return formatted_summary


if __name__ == "__main__":
    # Test the tool
    console.print("[bold blue]Testing Summary Context Generator Tool[/bold blue]")
    
    # Test with current directory
    test_path = "/home/ubuntu/sem"
    console.print(f"\n[yellow]Testing with path: {test_path}[/yellow]")
    
    summary = summary_generator.aggregate_analysis_results(test_path)
    formatted = summary_generator.format_for_llm(summary)
    
    print("\n" + "="*50)
    print("FORMATTED SUMMARY:")
    print("="*50)
    print(formatted)
