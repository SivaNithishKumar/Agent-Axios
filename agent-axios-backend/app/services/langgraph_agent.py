"""LangGraph-based analysis agent orchestrating vulnerability scans."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

from app.models import Analysis, CodeChunk, CVEFinding, db
from app.services.chunking_service import ChunkingService
from app.services.cve_search_service import CVESearchService
from app.services.embedding_service import EmbeddingService
from app.services.repo_service import RepoService
from app.services.report_service import ReportService
from app.services.validation_service import ValidationService
from config.settings import Config

logger = logging.getLogger(__name__)


class AnalysisAgentState(TypedDict):
    """Shared LangGraph state for the analysis agent."""

    messages: Annotated[List[BaseMessage], add_messages]


class AnalysisTool(BaseTool):
    """Base tool carrying common context for the analysis."""

    def __init__(self, agent: "LangGraphAnalysisAgent") -> None:
        super().__init__()
        self.agent = agent

    @property
    def analysis(self) -> Analysis:
        return self.agent.analysis

    @property
    def context(self) -> Dict[str, Any]:
        return self.agent.context

    @property
    def emit_progress(self):
        return self.agent.emit_progress


class CloneRepositoryInput(BaseModel):
    branch: Optional[str] = Field(
        default=None,
        description="Optional branch name to checkout. Leave empty to use the default branch.",
    )


class CloneRepositoryTool(AnalysisTool):
    name = "clone_repository"
    description = (
        "Clone the target repository for the current analysis. "
        "Call this tool first to prepare local sources."
    )
    args_schema = CloneRepositoryInput

    def _run(self, branch: Optional[str] = None) -> str:
        if self.context.get("repo_path"):
            return "Repository already cloned; reusing existing working directory."

        repo_url = self.analysis.repo_url
        repo_path = self.agent.repo_service.clone(repo_url, branch=branch)
        self.context["repo_path"] = repo_path

        self.emit_progress(20, "cloning", "Repository cloned successfully")
        logger.info("Cloned repository %s to %s", repo_url, repo_path)
        return f"Repository cloned to {repo_path}"


class ChunkRepositoryInput(BaseModel):
    max_files: Optional[int] = Field(
        default=None,
        description="Optionally override the maximum number of files to process.",
    )


class ChunkRepositoryTool(AnalysisTool):
    name = "chunk_repository"
    description = (
        "Parse the cloned repository and create code chunks for embedding. "
        "Call after cloning and before generating embeddings."
    )
    args_schema = ChunkRepositoryInput

    def _run(self, max_files: Optional[int] = None) -> str:
        repo_path = self.context.get("repo_path")
        if not repo_path:
            raise ValueError("Repository has not been cloned yet. Please call clone_repository first.")

        config = self.agent.analysis_config
        effective_max_files = max_files or config.get("max_files")
        max_chunks_per_file = config.get("max_chunks_per_file")

        chunks = self.agent.chunking_service.process_directory(
            repo_path,
            self.analysis.analysis_id,
            max_files=effective_max_files,
            max_chunks_per_file=max_chunks_per_file,
            progress_callback=self.agent.chunk_progress_callback,
        )

        self.analysis.total_files = self.agent.chunking_service.files_processed
        self.analysis.total_chunks = len(chunks)
        db.session.commit()

        chunk_ids = [chunk.chunk_id for chunk in chunks]
        self.context["chunk_ids"] = chunk_ids

        self.emit_progress(35, "chunking", f"Chunked {len(chunks)} code segments")
        logger.info(
            "Chunked repository for analysis %s: %s files, %s chunks",
            self.analysis.analysis_id,
            self.analysis.total_files,
            self.analysis.total_chunks,
        )
        return f"Prepared {self.analysis.total_chunks} chunks from {self.analysis.total_files} files"


class GenerateEmbeddingsTool(AnalysisTool):
    name = "generate_embeddings"
    description = (
        "Generate embeddings for all stored code chunks. "
        "Invoke after chunk_repository and before search_vulnerabilities."
    )

    def _run(self) -> str:
        chunk_ids: List[int] = self.context.get("chunk_ids", [])
        if not chunk_ids:
            raise ValueError("No chunks available. Did you run chunk_repository?")

        chunks = (
            db.session.query(CodeChunk)
            .filter(CodeChunk.analysis_id == self.analysis.analysis_id)
            .order_by(CodeChunk.chunk_id)
            .all()
        )
        if not chunks:
            raise ValueError("No chunks persisted for this analysis. Cannot generate embeddings.")

        self.agent.embedding_service.embed_chunks(
            chunks,
            progress_callback=self.agent.embedding_progress_callback,
        )
        db.session.commit()

        self.emit_progress(55, "embedding", "Embeddings generated for all chunks")
        logger.info(
            "Generated embeddings for %s chunks (analysis %s)",
            len(chunks),
            self.analysis.analysis_id,
        )
        return f"Generated embeddings for {len(chunks)} chunks"


class SearchVulnerabilitiesTool(AnalysisTool):
    name = "search_vulnerabilities"
    description = (
        "Search for vulnerability candidates by comparing chunk embeddings against the CVE index."
    )

    def _run(self) -> str:
        chunks = (
            db.session.query(CodeChunk)
            .filter(CodeChunk.analysis_id == self.analysis.analysis_id)
            .order_by(CodeChunk.chunk_id)
            .all()
        )
        if not chunks:
            raise ValueError("No code chunks found. Ensure chunk_repository has been executed.")

        config = self.agent.analysis_config
        findings = self.agent.cve_search_service.search_all_chunks(
            chunks,
            faiss_top_k=config.get("faiss_top_k", 50),
            rerank_top_n=config.get("rerank_top_n", 10),
            progress_callback=self.agent.search_progress_callback,
        )
        db.session.commit()

        finding_ids = [finding.finding_id for finding in findings]
        self.context["finding_ids"] = finding_ids

        total_findings = (
            db.session.query(CVEFinding)
            .filter_by(analysis_id=self.analysis.analysis_id)
            .count()
        )
        self.analysis.total_findings = total_findings
        db.session.commit()

        self.emit_progress(75, "searching", f"Found {total_findings} potential vulnerabilities")
        logger.info(
            "Search completed for analysis %s: %s findings",
            self.analysis.analysis_id,
            total_findings,
        )
        return f"Identified {total_findings} potential vulnerabilities"


class ValidateFindingsTool(AnalysisTool):
    name = "validate_findings"
    description = (
        "Validate potential findings with GPT-4.1. Automatically skips when validation is disabled for the current analysis type."
    )

    def _run(self) -> str:
        if not self.agent.analysis_config.get("validation_enabled", False):
            self.emit_progress(90, "validating", "Validation skipped for this analysis type")
            return "Validation skipped because it is disabled for this analysis type."

        findings = (
            db.session.query(CVEFinding)
            .filter_by(analysis_id=self.analysis.analysis_id)
            .all()
        )
        if not findings:
            self.emit_progress(90, "validating", "No findings to validate")
            return "No findings available for validation."

        chunks = (
            db.session.query(CodeChunk)
            .filter(CodeChunk.analysis_id == self.analysis.analysis_id)
            .all()
        )

        self.agent.validation_service.validate_all_findings(
            findings,
            chunks,
            progress_callback=self.agent.validation_progress_callback,
        )
        db.session.commit()

        confirmed = sum(1 for f in findings if f.validation_status == "confirmed")
        self.emit_progress(90, "validating", f"Validation complete ({confirmed} confirmed)")
        logger.info(
            "Validation finished for analysis %s: %s confirmed",
            self.analysis.analysis_id,
            confirmed,
        )
        return f"Validated findings; {confirmed} confirmed vulnerabilities"


class GenerateReportTool(AnalysisTool):
    name = "generate_report"
    description = (
        "Generate JSON and PDF vulnerability reports. Call after analysis steps finish."
    )

    def _run(self) -> str:
        report_paths = self.agent.report_service.generate_reports(self.analysis.analysis_id)
        self.context["report_paths"] = report_paths

        config_snapshot = dict(self.analysis.config_json or {})
        config_snapshot.setdefault("reports", report_paths)
        self.analysis.config_json = config_snapshot
        db.session.commit()

        self.emit_progress(98, "finalizing", "Reports generated successfully")
        logger.info(
            "Generated reports for analysis %s: %s",
            self.analysis.analysis_id,
            report_paths,
        )
        return f"Reports generated at {report_paths}"


class LangGraphAnalysisAgent:
    """LangGraph agent responsible for orchestrating vulnerability analysis."""

    def __init__(self, analysis: Analysis, emit_progress_callback) -> None:
        self.analysis = analysis
        self.emit_progress = emit_progress_callback
        self.context: Dict[str, Any] = {
            "analysis_id": analysis.analysis_id,
            "analysis_type": analysis.analysis_type,
        }

        self.repo_service = RepoService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.cve_search_service = CVESearchService()
        self.validation_service = ValidationService()
        self.report_service = ReportService()

        self.analysis_config = Config.ANALYSIS_CONFIGS.get(
            analysis.analysis_type,
            Config.ANALYSIS_CONFIGS["MEDIUM"],
        )

        self.llm = AzureChatOpenAI(
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            deployment_name=Config.AZURE_OPENAI_MODEL,
            temperature=0.1,
        )

        self.tools: List[BaseTool] = [
            CloneRepositoryTool(self),
            ChunkRepositoryTool(self),
            GenerateEmbeddingsTool(self),
            SearchVulnerabilitiesTool(self),
            ValidateFindingsTool(self),
            GenerateReportTool(self),
        ]

        self._graph = self._build_graph()
        self._final_messages: List[BaseMessage] = []

    def _build_graph(self):
        builder = StateGraph(AnalysisAgentState)
        builder.add_node("call_model", self._call_model)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", self._should_continue)
        builder.add_edge("tools", "call_model")
        memory = MemorySaver()
        return builder.compile(checkpointer=memory)

    def _call_model(self, state: AnalysisAgentState) -> Dict[str, List[BaseMessage]]:
        response = self.llm.invoke(state["messages"])
        return {"messages": [response]}

    @staticmethod
    def _should_continue(state: AnalysisAgentState) -> str:
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return END

    def run(self) -> List[BaseMessage]:
        """Execute the LangGraph agent until completion."""
        system_prompt = (
            "You are Agent Axios, a security analysis orchestrator. "
            "Your mission is to analyze the repository provided in the analysis record and identify potential vulnerabilities. "
            "Always operate safely and deterministically, following this plan: "
            "1) clone_repository; 2) chunk_repository; 3) generate_embeddings; "
            "4) search_vulnerabilities; 5) validate_findings (only if enabled); 6) generate_report. "
            "After calling generate_report, provide a concise natural language summary of the results and finish. "
            "Do not repeat steps unnecessarily."
        )

        user_prompt = (
            "Begin the vulnerability analysis. Use the available tools to progress through each stage "
            f"for analysis_id={self.analysis.analysis_id} targeting repo {self.analysis.repo_url}."
        )

        initial_state: AnalysisAgentState = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        }

        final_state = self._graph.invoke(initial_state)
        self._final_messages = final_state["messages"]
        return self._final_messages

    def get_repo_path(self) -> Optional[str]:
        return self.context.get("repo_path")

    def get_report_paths(self) -> Optional[Dict[str, str]]:
        return self.context.get("report_paths")

    # Progress callbacks used by tools
    def chunk_progress_callback(self, current: int, total: int) -> None:
        if total > 0:
            percentage = 20 + int((current / total) * 15)
            self.emit_progress(percentage, "chunking", f"Processing file {current}/{total}")

    def embedding_progress_callback(self, current: int, total: int) -> None:
        if total > 0:
            percentage = 35 + int((current / total) * 20)
            self.emit_progress(percentage, "embedding", f"Embedded {current}/{total} chunks")

    def search_progress_callback(self, current: int, total: int) -> None:
        if total > 0:
            percentage = 55 + int((current / total) * 20)
            self.emit_progress(percentage, "searching", f"Searched {current}/{total} chunks")

    def validation_progress_callback(self, current: int, total: int) -> None:
        if total > 0:
            percentage = 75 + int((current / total) * 15)
            self.emit_progress(percentage, "validating", f"Validated {current}/{total} findings")