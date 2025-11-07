"""Orchestrator tool that runs full analysis for a CVE: decomposition, semantic search, file reads and report generation."""
import os
import logging
from typing import Dict, Any, List, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_tools.base_tool import BaseTool, ToolDefinition, ToolParameter
from query_processor import QueryProcessor
from config import CODEBASE_CONFIG
from agent_tools.report_writer import write_report, consolidate_matches
from agent_tools.pdf_report_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class AnalysisOrchestratorTool(BaseTool):
    """Tool to orchestrate full analysis flow for a CVE or markdown input."""

    def __init__(self):
        super().__init__()
        self.query_processor = QueryProcessor()
        self.pdf_generator = PDFReportGenerator()

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="analysis_orchestrator",
            description="Run full automated analysis for a CVE or report: decompose query, search codebase, read files, consolidate, and generate report.",
            category="orchestration",
            parameters=[
                ToolParameter(name="action", type="string", description="Action", required=True, enum=["run_full", "generate_report"]),
                ToolParameter(name="cve_id", type="string", description="CVE id to analyze", required=False),
                ToolParameter(name="markdown_report", type="string", description="Markdown report to analyze", required=False),
                ToolParameter(name="db_path", type="string", description="FAISS DB path", required=False),
                ToolParameter(name="top_k", type="integer", description="Top files per subquery", required=False, default=10),
                ToolParameter(name="max_files_to_read", type="integer", description="Max files to read and consolidate", required=False, default=50),
                ToolParameter(name="generate_pdf", type="boolean", description="Generate PDF report in addition to JSON", required=False, default=True),
            ],
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        validated = self.validate_parameters(kwargs)
        action = validated.get("action")

        if action == "run_full":
            return self._run_full(validated)
        elif action == "generate_report":
            # expect 'matches' list in params
            matches = validated.get("matches")
            if not matches:
                return {"error": "matches parameter required for generate_report"}
            report_path = write_report({"matches": matches}, filename=validated.get("filename"))
            return {"success": True, "report_path": report_path}
        else:
            return {"error": f"Unknown action: {action}"}

    def _run_full(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete analysis pipeline:
        1. Get CVE from id or markdown
        2. Decompose query using Hype (hypothetical answer generation)
        3. Semantic search for each decomposed query
        4. Read matched files
        5. Consolidate results
        6. Generate report
        """
        # Step 0: determine CVE or query
        cve_id = params.get("cve_id")
        markdown = params.get("markdown_report")
        db_path = params.get("db_path") or CODEBASE_CONFIG.get("faiss_db_path")
        top_k = params.get("top_k", 10)
        max_files_to_read = params.get("max_files_to_read", 50)

        # Import here to avoid circular dependency
        from agent_tools.tool_registry import execute_tool

        # Decide which CVE/payload to analyze
        cve_record = None
        if cve_id:
            logger.info(f"Orchestrator: fetching CVE by id: {cve_id}")
            res = execute_tool("cve_retrieval", action="get_by_id", cve_id=cve_id)
            if "error" in res:
                return {"success": False, "error": res["error"]}
            cve_record = res.get("data")
        elif markdown:
            logger.info("Orchestrator: analyzing markdown to find CVEs")
            res = execute_tool("cve_retrieval", action="analyze_markdown", markdown_report=markdown, top_k=5)
            
            # Handle different response formats
            if isinstance(res, dict):
                if "error" in res:
                    return {"success": False, "error": res["error"]}
                
                # Try to get vulnerabilities from different possible locations
                vulns = res.get("vulnerabilities")
                if not vulns:
                    result_data = res.get("result", {})
                    vulns = result_data.get("vulnerabilities")
                if not vulns:
                    data = res.get("data", {})
                    vulns = data.get("vulnerabilities")
                    
                if not vulns or len(vulns) == 0:
                    return {"success": False, "error": "No vulnerabilities found in markdown"}
                
                cve_record = vulns[0]
                cve_id = cve_record.get("cve_id")
        else:
            return {"error": "Either cve_id or markdown_report must be provided"}

        # Step 1: Create decomposition / Hype queries (Hypothetical Answer Generation)
        logger.info(f"Step 1: Performing Hype (hypothetical answer generation) for CVE: {cve_id}")
        title = cve_record.get("summary", "") if isinstance(cve_record, dict) else ""
        base_query = title or cve_id or ""
        
        # Expand query to generate multiple search angles (Hype)
        queries = self.query_processor.expand_query(base_query)
        if not queries or len(queries) == 0:
            queries = [base_query]

        logger.info(f"Decomposed into {len(queries)} queries: {queries[:3]}...")  # Show first 3

        # Step 2: For each query, run semantic search against codebase
        logger.info(f"Step 2: Running semantic search for {len(queries)} decomposed queries")
        all_matches: List[Dict[str, Any]] = []
        seen_files = set()
        
        for idx, q in enumerate(queries, 1):
            logger.info(f"  Search {idx}/{len(queries)}: '{q[:60]}...'")
            search_res = execute_tool(
                "codebase_indexing",
                action="search",
                query=q,
                db_path=db_path,
                top_k=top_k,
            )

            if "error" in search_res:
                logger.warning(f"  Search error for query '{q}': {search_res['error']}")
                continue

            # Extract results from different response formats
            results = []
            if isinstance(search_res, dict):
                results = search_res.get("data", {}).get("results") or search_res.get("results") or []
            
            logger.info(f"  Found {len(results)} results")

            for r in results:
                fp = r.get("file_path")
                score = r.get("similarity_score") or r.get("score") or 0.0
                
                if fp in seen_files:
                    continue
                seen_files.add(fp)

                # Step 3: Read file content using best-effort approach
                content = None
                content_preview = None
                actual_path = None
                
                try:
                    codebase_path = CODEBASE_CONFIG.get("codebase_path", "")
                    logger.info(f"  Reading file: {fp}")
                    logger.info(f"  Codebase path: {codebase_path}")
                    
                    # Try absolute path first
                    if os.path.isabs(fp):
                        if os.path.exists(fp):
                            actual_path = fp
                            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                                content = fh.read()
                            logger.info(f"  ✓ Read using absolute path")
                    
                    if not content:
                        # Try relative to codebase path
                        candidate = os.path.join(codebase_path, fp)
                        logger.info(f"  Trying: {candidate}")
                        if os.path.exists(candidate):
                            actual_path = candidate
                            with open(candidate, "r", encoding="utf-8", errors="replace") as fh:
                                content = fh.read()
                            logger.info(f"  ✓ Read using codebase_path + file_path")
                    
                    if not content:
                        # Try without leading path separators
                        clean_fp = fp.lstrip("/\\")
                        candidate2 = os.path.join(codebase_path, clean_fp)
                        logger.info(f"  Trying: {candidate2}")
                        if os.path.exists(candidate2):
                            actual_path = candidate2
                            with open(candidate2, "r", encoding="utf-8", errors="replace") as fh:
                                content = fh.read()
                            logger.info(f"  ✓ Read using cleaned path")
                    
                    if content:
                        content_preview = content[:500] + ("..." if len(content) > 500 else "")
                        logger.info(f"  ✓ Successfully read file: {fp} ({len(content)} chars)")
                    else:
                        logger.warning(f"  ✗ Could not read file: {fp} (all paths failed)")
                        
                except Exception as e:
                    logger.warning(f"  ✗ Error reading {fp}: {str(e)}")
                    content = None
                    actual_path = None

                match = {
                    "file_path": fp,
                    "actual_path": actual_path,
                    "score": score,
                    "query": q,
                    "content": content,
                    "content_preview": content_preview,
                    "content_length": len(content) if content else 0
                }
                all_matches.append(match)

                if len(all_matches) >= max_files_to_read:
                    break

            if len(all_matches) >= max_files_to_read:
                break

        logger.info(f"Step 3: Collected {len(all_matches)} unique file matches")

        # Step 4: Consolidate and write report
        logger.info(f"Step 4: Consolidating results and generating report")
        
        consolidated = consolidate_matches(all_matches)
        
        report = {
            "cve_id": cve_id,
            "cve_summary": title,
            "base_query": base_query,
            "decomposed_queries": queries,
            "total_queries": len(queries),
            "total_matches": len(all_matches),
            "unique_files": len(seen_files),
            "consolidated": consolidated,
            "detailed_matches": all_matches,
        }

        filename = f"analysis_{cve_id or 'manual'}_report.json".replace("/", "_")
        report_path = write_report(report, filename=filename)

        logger.info(f"✓ JSON Report generated: {report_path}")
        
        # Generate PDF report if requested
        pdf_path = None
        generate_pdf = params.get("generate_pdf", True)
        if generate_pdf:
            try:
                logger.info(f"Step 5: Generating PDF report")
                pdf_path = self.pdf_generator.generate_report(report)
                logger.info(f"✓ PDF Report generated: {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to generate PDF: {str(e)}")
                pdf_path = None

        return {
            "success": True, 
            "report_path": report_path,
            "pdf_path": pdf_path,
            "total_matches": len(all_matches),
            "unique_files": len(seen_files),
            "queries_used": len(queries),
            "summary": f"Analyzed {cve_id} with {len(queries)} queries, found {len(all_matches)} matches in {len(seen_files)} files"
        }

    def cleanup(self):
        logger.info("Analysis Orchestrator cleaned up")
