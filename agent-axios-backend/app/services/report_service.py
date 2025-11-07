"""Report generation service - creates JSON and PDF analysis reports."""
import json
import os
from datetime import datetime
from typing import Dict, Any
from langsmith import traceable
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app.models import Analysis, CVEFinding, CodeChunk, db
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """Generates analysis reports in multiple formats."""

    REPORT_ROOT = os.getenv('REPORT_OUTPUT_DIR', 'data/reports')

    def __init__(self):
        os.makedirs(self.REPORT_ROOT, exist_ok=True)

    @traceable(name="generate_reports", run_type="tool")
    def generate_reports(self, analysis_id: int) -> Dict[str, str]:
        """
        Generate JSON and PDF reports for an analysis.

        Args:
            analysis_id: ID of the analysis

        Returns:
            Mapping of report types to file paths
        """
        analysis = db.session.query(Analysis).filter_by(analysis_id=analysis_id).first()
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        findings = db.session.query(CVEFinding).filter_by(analysis_id=analysis_id).all()
        chunks = {
            chunk.chunk_id: chunk
            for chunk in db.session.query(CodeChunk).filter_by(analysis_id=analysis_id).all()
        }

        output_dir = os.path.join(self.REPORT_ROOT, f"analysis_{analysis_id}")
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Generating reports for analysis %s (%s findings)", analysis_id, len(findings))

        json_path = self._generate_json_report(analysis, findings, chunks, output_dir)
        pdf_path = self._generate_pdf_report(analysis, findings, chunks, output_dir)

        return {
            'json': json_path,
            'pdf': pdf_path
        }

    @traceable(name="generate_json_report", run_type="tool")
    def _generate_json_report(self, analysis: Analysis, findings, chunks, output_dir: str) -> str:
        """Create JSON report file."""
        summary = self._build_summary(analysis, findings)

        findings_data = []
        for finding in findings:
            chunk = chunks.get(finding.chunk_id)
            findings_data.append({
                'finding_id': finding.finding_id,
                'cve_id': finding.cve_id,
                'file_path': finding.file_path,
                'severity': finding.severity,
                'confidence_score': finding.confidence_score,
                'validation_status': finding.validation_status,
                'validation_explanation': finding.validation_explanation,
                'cve_description': finding.cve_description,
                'chunk_lines': {
                    'start': chunk.line_start if chunk else None,
                    'end': chunk.line_end if chunk else None,
                    'language': chunk.language if chunk else None,
                }
            })

        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'analysis': analysis.to_dict(),
            'summary': summary,
            'findings': findings_data
        }

        json_path = os.path.join(output_dir, f"analysis_{analysis.analysis_id}.json")
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(report, json_file, indent=2)

        logger.info("JSON report written to %s", json_path)
        return json_path

    @traceable(name="generate_pdf_report", run_type="tool")
    def _generate_pdf_report(self, analysis: Analysis, findings, chunks, output_dir: str) -> str:
        """Create PDF report file."""
        pdf_path = os.path.join(output_dir, f"analysis_{analysis.analysis_id}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        def write_line(text: str, y_pos: int, font_size: int = 10):
            c.setFont("Helvetica", font_size)
            c.drawString(40, y_pos, text)
            return y_pos - (font_size + 4)

        y = height - 40
        y = write_line("Agent Axios Vulnerability Report", y, 14)
        y = write_line(f"Analysis ID: {analysis.analysis_id}", y)
        y = write_line(f"Repository: {analysis.repo_url}", y)
        if analysis.start_time and analysis.end_time:
            duration = (analysis.end_time - analysis.start_time).total_seconds()
            y = write_line(f"Duration: {duration:.1f} seconds", y)
        y = write_line(f"Findings: {len(findings)}", y)
        y = write_line("", y)

        summary = self._build_summary(analysis, findings)
        for key, value in summary.items():
            y = write_line(f"{key.replace('_', ' ').title()}: {value}", y)

        y = write_line("", y)
        y = write_line("Top Findings:", y, 12)

        for finding in findings[:5]:
            if y < 120:
                c.showPage()
                y = height - 40

            chunk = chunks.get(finding.chunk_id)
            y = write_line(f"CVE: {finding.cve_id} (Severity: {finding.severity or 'N/A'})", y)
            y = write_line(f"Confidence: {finding.confidence_score:.2f}", y)
            y = write_line(f"File: {finding.file_path}", y)
            if chunk:
                y = write_line(
                    f"Lines: {chunk.line_start}-{chunk.line_end} ({chunk.language or 'unknown'})",
                    y
                )
            if finding.validation_explanation:
                explanation = finding.validation_explanation[:200].replace('\n', ' ')
                y = write_line(f"Explanation: {explanation}", y)
            y = write_line("", y)

        c.save()
        logger.info("PDF report written to %s", pdf_path)
        return pdf_path

    def _build_summary(self, analysis: Analysis, findings) -> Dict[str, Any]:
        """Build summary statistics for reports."""
        summary = {
            'total_files_analyzed': analysis.total_files or 0,
            'total_chunks_analyzed': analysis.total_chunks or 0,
            'total_findings': len(findings),
            'confirmed_vulnerabilities': len([
                f for f in findings if f.validation_status == 'confirmed'
            ])
        }

        severity_counts: Dict[str, int] = {}
        for finding in findings:
            severity = finding.severity or 'unknown'
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        summary['severity_breakdown'] = severity_counts
        return summary
