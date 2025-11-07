"""
PDF Report Generator for Security Analysis

Creates professional PDF reports with neat UI and detailed information.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class PDFReportGenerator:
    """Generate professional security analysis PDF reports"""
    
    def __init__(self, output_dir: str = "logs/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#3f51b5'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#3f51b5'),
            borderPadding=5,
            backColor=colors.HexColor('#e8eaf6')
        ))
        
        # Code style
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Code'],
            fontSize=9,
            textColor=colors.HexColor('#212121'),
            backColor=colors.HexColor('#f5f5f5'),
            borderWidth=1,
            borderColor=colors.HexColor('#bdbdbd'),
            borderPadding=10,
            fontName='Courier',
            spaceAfter=10,
            spaceBefore=5,
            leftIndent=20,
            rightIndent=20
        ))
        
        # Info box style
        self.styles.add(ParagraphStyle(
            name='InfoBox',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#004d40'),
            backColor=colors.HexColor('#e0f2f1'),
            borderWidth=1,
            borderColor=colors.HexColor('#00897b'),
            borderPadding=10,
            spaceAfter=10,
            spaceBefore=5
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#e65100'),
            backColor=colors.HexColor('#fff3e0'),
            borderWidth=1,
            borderColor=colors.HexColor('#ff9800'),
            borderPadding=10,
            spaceAfter=10,
            spaceBefore=5
        ))
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(colors.HexColor('#1a237e'))
        canvas_obj.drawString(inch, doc.height + doc.topMargin + 0.3*inch, 
                             "Security Analysis Report")
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawRightString(doc.width + doc.leftMargin, 
                                   doc.height + doc.topMargin + 0.3*inch,
                                   datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        # Header line
        canvas_obj.setStrokeColor(colors.HexColor('#3f51b5'))
        canvas_obj.setLineWidth(2)
        canvas_obj.line(inch, doc.height + doc.topMargin + 0.2*inch,
                       doc.width + doc.leftMargin, doc.height + doc.topMargin + 0.2*inch)
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(inch, 0.5*inch, 
                             "Confidential - Security Analysis")
        canvas_obj.drawRightString(doc.width + doc.leftMargin, 0.5*inch,
                                   f"Page {doc.page}")
        
        # Footer line
        canvas_obj.setStrokeColor(colors.HexColor('#3f51b5'))
        canvas_obj.setLineWidth(1)
        canvas_obj.line(inch, 0.7*inch, doc.width + doc.leftMargin, 0.7*inch)
        
        canvas_obj.restoreState()
    
    def generate_report(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """
        Generate a professional PDF report from analysis data
        
        Args:
            report_data: Dictionary containing analysis results
            filename: Output filename (optional)
        
        Returns:
            Path to generated PDF file
        """
        if filename is None:
            cve_id = report_data.get("cve_id", "analysis").replace("/", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_analysis_{cve_id}_{timestamp}.pdf"
        
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        pdf_path = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        # Build story (content elements)
        story = []
        
        # Title page
        story.extend(self._create_title_page(report_data))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(report_data))
        story.append(PageBreak())
        
        # CVE details
        story.extend(self._create_cve_details(report_data))
        
        # Analysis methodology
        story.extend(self._create_methodology_section(report_data))
        story.append(PageBreak())
        
        # Findings
        story.extend(self._create_findings_section(report_data))
        
        # Detailed file analysis
        story.extend(self._create_detailed_analysis(report_data))
        
        # Appendix
        story.extend(self._create_appendix(report_data))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, 
                 onLaterPages=self._add_header_footer)
        
        return pdf_path
    
    def _create_title_page(self, data: Dict[str, Any]) -> List:
        """Create title page"""
        elements = []
        
        # Add spacer to center content
        elements.append(Spacer(1, 2*inch))
        
        # Title
        title = Paragraph("SECURITY ANALYSIS REPORT", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # CVE info box
        cve_id = data.get("cve_id", "N/A")
        cve_summary = data.get("cve_summary", "No summary available")
        
        info_text = f"""
        <b>CVE ID:</b> {cve_id}<br/>
        <b>Analysis Date:</b> {datetime.now().strftime("%B %d, %Y")}<br/>
        <b>Total Files Analyzed:</b> {data.get("unique_files", 0)}<br/>
        <b>Total Matches:</b> {data.get("total_matches", 0)}<br/>
        """
        
        info_box = Paragraph(info_text, self.styles['InfoBox'])
        elements.append(info_box)
        elements.append(Spacer(1, 0.3*inch))
        
        # CVE summary
        summary_para = Paragraph(f"<b>Vulnerability Summary:</b><br/>{cve_summary}", 
                                self.styles['Normal'])
        elements.append(summary_para)
        
        return elements
    
    def _create_executive_summary(self, data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary statistics
        total_queries = data.get("total_queries", 0)
        total_matches = data.get("total_matches", 0)
        unique_files = data.get("unique_files", 0)
        
        summary_text = f"""
        This report presents the results of an automated security analysis performed to identify 
        potential vulnerabilities related to <b>{data.get('cve_id', 'N/A')}</b> in the target codebase.
        <br/><br/>
        The analysis utilized advanced query decomposition and semantic search techniques to scan 
        <b>{unique_files}</b> unique files, generating <b>{total_queries}</b> specialized search queries 
        that resulted in <b>{total_matches}</b> potential matches.
        <br/><br/>
        Each identified file has been analyzed for patterns and code structures that may be related 
        to the vulnerability, providing actionable insights for security remediation.
        """
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Key findings table
        elements.append(Paragraph("Key Metrics", self.styles['SectionHeader']))
        
        metrics_data = [
            ['Metric', 'Value'],
            ['CVE ID', data.get('cve_id', 'N/A')],
            ['Total Queries Generated', str(total_queries)],
            ['Files Scanned', str(unique_files)],
            ['Total Matches Found', str(total_matches)],
            ['Analysis Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdbdbd')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        
        elements.append(metrics_table)
        
        return elements
    
    def _create_cve_details(self, data: Dict[str, Any]) -> List:
        """Create CVE details section"""
        elements = []
        
        elements.append(Paragraph("Vulnerability Details", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # CVE information
        cve_id = data.get('cve_id', 'N/A')
        cve_summary = data.get('cve_summary', 'No summary available')
        
        elements.append(Paragraph(f"<b>CVE Identifier:</b> {cve_id}", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph(f"<b>Description:</b>", self.styles['Normal']))
        elements.append(Paragraph(cve_summary, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_methodology_section(self, data: Dict[str, Any]) -> List:
        """Create methodology section"""
        elements = []
        
        elements.append(Paragraph("Analysis Methodology", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        methodology_text = """
        The analysis employed a multi-stage approach:
        <br/><br/>
        <b>1. Query Decomposition (Hype):</b> The CVE description was decomposed into multiple 
        specialized search queries using hypothetical answer generation techniques.
        <br/><br/>
        <b>2. Semantic Search:</b> Each query was executed against a FAISS vector database 
        containing embedded representations of the codebase files.
        <br/><br/>
        <b>3. File Retrieval:</b> Matched files were retrieved and their full contents analyzed.
        <br/><br/>
        <b>4. Consolidation:</b> Results were aggregated and ranked by relevance score.
        """
        
        elements.append(Paragraph(methodology_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Decomposed queries
        queries = data.get('decomposed_queries', [])
        if queries:
            elements.append(Paragraph("Generated Search Queries", self.styles['SectionHeader']))
            
            for idx, query in enumerate(queries, 1):
                query_text = f"<b>Query {idx}:</b> {query}"
                elements.append(Paragraph(query_text, self.styles['Normal']))
                elements.append(Spacer(1, 0.05*inch))
        
        return elements
    
    def _create_findings_section(self, data: Dict[str, Any]) -> List:
        """Create findings overview section"""
        elements = []
        
        elements.append(Paragraph("Findings Overview", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        consolidated = data.get('consolidated', {})
        files = consolidated.get('files', [])
        
        if not files:
            elements.append(Paragraph("No matches found in the codebase.", 
                                    self.styles['Normal']))
            return elements
        
        # Create findings table
        findings_data = [['Rank', 'File Path', 'Relevance', 'Size']]
        
        for idx, file_info in enumerate(files[:20], 1):  # Top 20 files
            file_path = file_info.get('file_path', 'N/A')
            avg_score = file_info.get('avg_score', 0.0)
            
            # Truncate path if too long
            if len(file_path) > 50:
                file_path = "..." + file_path[-47:]
            
            # Format score as percentage
            score_pct = f"{avg_score * 100:.1f}%" if avg_score > 0 else "N/A"
            
            content_len = len(file_info.get('content_snippet', ''))
            size_str = f"{content_len} chars"
            
            findings_data.append([
                str(idx),
                file_path,
                score_pct,
                size_str
            ])
        
        findings_table = Table(findings_data, colWidths=[0.5*inch, 3.5*inch, 1*inch, 1*inch])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(findings_table)
        elements.append(PageBreak())
        
        return elements
    
    def _create_detailed_analysis(self, data: Dict[str, Any]) -> List:
        """Create detailed file analysis section"""
        elements = []
        
        elements.append(Paragraph("Detailed File Analysis", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        detailed_matches = data.get('detailed_matches', [])
        
        if not detailed_matches:
            elements.append(Paragraph("No detailed matches available.", 
                                    self.styles['Normal']))
            return elements
        
        for idx, match in enumerate(detailed_matches[:10], 1):  # Top 10 detailed
            file_path = match.get('file_path', 'N/A')
            score = match.get('score', 0.0)
            query = match.get('query', 'N/A')
            content = match.get('content', '')
            content_length = match.get('content_length', 0)
            
            # File header
            file_header = f"<b>File {idx}:</b> {file_path}"
            elements.append(Paragraph(file_header, self.styles['SectionHeader']))
            
            # Match info
            info_text = f"""
            <b>Matched Query:</b> {query[:100]}{'...' if len(query) > 100 else ''}<br/>
            <b>Relevance Score:</b> {score:.4f}<br/>
            <b>File Size:</b> {content_length} characters
            """
            elements.append(Paragraph(info_text, self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Content preview
            if content:
                elements.append(Paragraph("<b>Content Preview:</b>", self.styles['Normal']))
                
                # Truncate and escape content
                preview = content[:1000] if len(content) > 1000 else content
                preview = preview.replace('<', '&lt;').replace('>', '&gt;')
                preview = preview.replace('\n', '<br/>')
                
                code_para = Paragraph(f"<font name='Courier' size='8'>{preview}</font>", 
                                    self.styles['CodeBlock'])
                elements.append(code_para)
                
                if len(content) > 1000:
                    elements.append(Paragraph(
                        f"<i>... truncated ({len(content) - 1000} more characters)</i>", 
                        self.styles['Normal']
                    ))
            else:
                elements.append(Paragraph("<i>Content not available</i>", 
                                        self.styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_appendix(self, data: Dict[str, Any]) -> List:
        """Create appendix section"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Appendix", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Configuration details
        elements.append(Paragraph("A. Analysis Configuration", self.styles['SectionHeader']))
        
        config_text = f"""
        <b>Base Query:</b> {data.get('base_query', 'N/A')}<br/>
        <b>Total Queries:</b> {data.get('total_queries', 0)}<br/>
        <b>Total Matches:</b> {data.get('total_matches', 0)}<br/>
        <b>Unique Files:</b> {data.get('unique_files', 0)}<br/>
        <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        elements.append(Paragraph(config_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Disclaimer
        elements.append(Paragraph("B. Disclaimer", self.styles['SectionHeader']))
        
        disclaimer_text = """
        This report is generated by an automated security analysis tool and should be reviewed 
        by qualified security professionals. The matches identified may include false positives 
        and require manual verification. The analysis is based on semantic similarity and does 
        not constitute a comprehensive security audit.
        """
        
        elements.append(Paragraph(disclaimer_text, self.styles['Warning']))
        
        return elements


def generate_pdf_from_json(json_path: str, output_dir: str = "logs/reports") -> str:
    """
    Generate PDF report from JSON report file
    
    Args:
        json_path: Path to JSON report file
        output_dir: Output directory for PDF
    
    Returns:
        Path to generated PDF file
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    generator = PDFReportGenerator(output_dir)
    pdf_path = generator.generate_report(report_data)
    
    return pdf_path
