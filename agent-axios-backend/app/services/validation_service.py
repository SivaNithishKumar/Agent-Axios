"""GPT-4 validation service - validates CVE findings using Azure OpenAI."""
import os
from typing import List, Callable, Optional
from openai import AzureOpenAI
from langsmith import traceable
from app.models import CodeChunk, CVEFinding, CVEDataset, db
import logging

logger = logging.getLogger(__name__)

class ValidationService:
    """Validates CVE findings using GPT-4.1."""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version='2023-12-01-preview',
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        self.model = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
    
    @traceable(name="validate_all_findings", run_type="tool")
    def validate_all_findings(
        self,
        findings: List[CVEFinding],
        chunks: List[CodeChunk],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        Validate all findings using GPT-4.1.
        
        Args:
            findings: List of CVEFinding objects
            chunks: List of CodeChunk objects (for context)
            progress_callback: Optional progress callback (current, total)
        """
        total = len(findings)
        logger.info(f"Validating {total} findings with GPT-4.1")
        
        # Create chunk lookup
        chunk_map = {chunk.chunk_id: chunk for chunk in chunks}
        
        for i, finding in enumerate(findings):
            try:
                chunk = chunk_map.get(finding.chunk_id)
                if not chunk:
                    logger.warning(f"Chunk {finding.chunk_id} not found for finding {finding.finding_id}")
                    continue
                
                # Get CVE data
                cve = db.session.query(CVEDataset).filter_by(cve_id=finding.cve_id).first()
                if not cve:
                    logger.warning(f"CVE {finding.cve_id} not found")
                    continue
                
                # Validate with GPT-4
                is_valid, severity, explanation = self._validate_finding(chunk, cve)
                
                # Update finding
                finding.validation_status = 'confirmed' if is_valid else 'false_positive'
                finding.severity = severity if is_valid else None
                finding.validation_explanation = explanation

                db.session.flush()
                
                if progress_callback:
                    progress_callback(i + 1, total)
                
                if (i + 1) % 5 == 0:
                    logger.info(f"Validated {i + 1}/{total} findings")
                    
            except Exception as e:
                logger.error(f"Failed to validate finding {finding.finding_id}: {str(e)}")
                finding.validation_status = 'needs_review'
                finding.validation_explanation = f"Validation error: {str(e)}"
                db.session.flush()
                continue
        
        confirmed = sum(1 for f in findings if f.validation_status == 'confirmed')
        logger.info(f"Validation complete: {confirmed}/{total} confirmed")
    db.session.commit()
    
    @traceable(name="validate_single_finding", run_type="llm")
    def _validate_finding(
        self,
        chunk: CodeChunk,
        cve: CVEDataset
    ) -> tuple[bool, str, str]:
        """
        Validate a single finding using GPT-4.1.
        
        Returns:
            (is_valid, severity, explanation)
        """
        prompt = f"""You are a security expert analyzing code for vulnerabilities.

CVE Information:
- ID: {cve.cve_id}
- Description: {cve.description}
- Severity: {cve.severity}
- CWE: {cve.cwe_id or 'N/A'}

Code to Analyze:
File: {chunk.file_path}
Lines {chunk.line_start}-{chunk.line_end}:
```
{chunk.chunk_text}
```

Task:
1. Determine if this code is vulnerable to the described CVE
2. If vulnerable, assess the severity (CRITICAL, HIGH, MEDIUM, LOW)
3. Provide a brief explanation

Response format:
VULNERABLE: YES/NO
SEVERITY: CRITICAL/HIGH/MEDIUM/LOW/NONE
EXPLANATION: <your explanation>

Be strict in your assessment. Only confirm if there's clear evidence of vulnerability."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security expert specializing in vulnerability analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response
            is_valid = 'VULNERABLE: YES' in content
            
            # Extract severity
            severity = 'MEDIUM'  # default
            for line in content.split('\n'):
                if line.startswith('SEVERITY:'):
                    severity_text = line.split(':')[1].strip()
                    if severity_text in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                        severity = severity_text
                    break
            
            # Extract explanation
            explanation = ''
            if 'EXPLANATION:' in content:
                explanation = content.split('EXPLANATION:')[1].strip()
            
            return is_valid, severity, explanation
            
        except Exception as e:
            logger.error(f"GPT-4 validation failed: {str(e)}")
            return False, 'UNKNOWN', f"Validation failed: {str(e)}"
    
    @traceable(name="validate_single_by_id", run_type="tool")
    def validate_finding_by_id(self, finding_id: int) -> bool:
        """
        Validate a specific finding by ID.
        
        Args:
            finding_id: Finding ID to validate
        
        Returns:
            bool: True if validation succeeded
        """
        try:
            finding = db.session.query(CVEFinding).filter_by(finding_id=finding_id).first()
            if not finding:
                logger.error(f"Finding {finding_id} not found")
                return False
            
            chunk = db.session.query(CodeChunk).filter_by(chunk_id=finding.chunk_id).first()
            cve = db.session.query(CVEDataset).filter_by(cve_id=finding.cve_id).first()
            
            if not chunk or not cve:
                logger.error(f"Missing chunk or CVE data for finding {finding_id}")
                return False
            
            is_valid, severity, explanation = self._validate_finding(chunk, cve)
            
            finding.validation_status = 'confirmed' if is_valid else 'false_positive'
            finding.severity = severity if is_valid else None
            finding.validation_explanation = explanation

            db.session.commit()
            
            logger.info(f"Validated finding {finding_id}: {finding.validation_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate finding {finding_id}: {str(e)}")
            return False
