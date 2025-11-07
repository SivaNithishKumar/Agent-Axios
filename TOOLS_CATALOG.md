# Agent Axios - Complete Tools Catalog

## Overview
Agent Axios is a comprehensive security analysis and vulnerability detection system that combines autonomous repository analysis with CVE (Common Vulnerabilities and Exposures) retrieval and codebase indexing capabilities.

---

## 🎯 System Architecture

The system consists of two main components:
1. **Repository Analysis System** (`/src`) - ReAct Agent for autonomous repository analysis
2. **Retrieval System** (`/retrieval`) - CVE vulnerability search and codebase semantic indexing

---

# 📦 REPOSITORY ANALYSIS TOOLS (`/src/tools`)

## 1. Repository Loader (`repo_loader.py`)

### Tool: `clone_repository`
**Purpose:** Clone Git repositories or load local directories for analysis

**Use Cases:**
- Clone remote repositories from GitHub, GitLab, BitBucket
- Handle GitHub shorthand notation (username/repo)
- Load and validate local project directories
- Extract repository metadata (commits, authors, branches)

**Input Formats:**
- Git URLs: `https://github.com/user/repo.git`
- SSH URLs: `git@github.com:user/repo.git`
- GitHub shorthand: `user/repo`
- Local paths: `/path/to/project`

**Outputs:**
- Repository path (local)
- Git metadata (branch, commit hash, author, date)
- File statistics (total files, extensions)
- Source type (git/local)

---

## 2. Project Type Detector (`project_detector.py`)

### Tool: `detect_project_type`
**Purpose:** Identify programming languages and project types through file analysis

**Use Cases:**
- Detect primary programming language (Python, JavaScript, Java, Go, Rust, etc.)
- Calculate confidence scores for each detected language
- Identify web frameworks and project categories
- Analyze file extension distribution

**Detection Methods:**
- File extension analysis (`.py`, `.js`, `.java`, etc.)
- Presence of language-specific files (package.json, requirements.txt, pom.xml)
- Configuration file patterns
- Directory structure patterns

**Supported Languages:**
- Python, Node.js/JavaScript, Java, C#, Go, Rust, PHP, Ruby, C++, Swift, Kotlin

**Outputs:**
- Primary project type with confidence score
- All detected languages with scores
- Framework indicators (React, Django, Flask, Spring, etc.)
- File statistics by extension

---

## 3. Dependency Extractor (`dependency_extractor.py`)

### Tool: `analyze_dependencies`
**Purpose:** Extract and parse project dependencies from various package managers

**Use Cases:**
- Parse Python dependencies (requirements.txt, Pipfile, pyproject.toml, setup.py)
- Extract Node.js packages (package.json, yarn.lock, package-lock.json)
- Analyze Java dependencies (pom.xml, build.gradle)
- Parse PHP, Ruby, Go, Rust, C# dependencies
- Version extraction and analysis
- Separate production vs development dependencies

**Supported Dependency Files:**
- **Python:** requirements.txt, Pipfile, pyproject.toml, setup.py, environment.yml
- **Node.js:** package.json, yarn.lock, package-lock.json
- **Java:** pom.xml, build.gradle, gradle.properties
- **PHP:** composer.json, composer.lock
- **Ruby:** Gemfile, Gemfile.lock, *.gemspec
- **Go:** go.mod, go.sum
- **Rust:** Cargo.toml, Cargo.lock
- **C#:** packages.config, *.csproj, *.sln

**Outputs:**
- Complete dependency list with versions
- Dependency categorization (production/development)
- Package metadata (descriptions, scripts, engines)
- Dependency count per language
- Security-relevant package identification

---

## 4. Framework Detector (`framework_detector.py`)

### Tool: `detect_frameworks`
**Purpose:** Identify frameworks, libraries, and technology stacks used in projects

**Use Cases:**
- Detect web frameworks (Django, Flask, FastAPI, React, Vue, Angular, Express)
- Identify backend frameworks (Spring Boot, Laravel, Rails, etc.)
- Analyze import statements and dependencies
- Confidence scoring for each framework
- Language-specific framework patterns

**Detected Frameworks:**

**Python:**
- Django, Flask, FastAPI, Streamlit

**JavaScript/TypeScript:**
- React, Vue, Angular, Express, Next.js

**Java:**
- Spring, Spring Boot

**Go:**
- Gin, Echo

**PHP:**
- Laravel, Symfony

**Ruby:**
- Rails

**Rust:**
- Actix, Rocket

**Detection Methods:**
- Import statement analysis
- Configuration file presence
- Directory structure patterns
- Dependency declarations

**Outputs:**
- Framework list with confidence levels (high/medium/low)
- Primary frameworks identification
- Language-specific framework categorization
- Framework usage patterns

---

## 5. Structure Mapper (`structure_mapper.py`)

### Tool: `analyze_structure`
**Purpose:** Analyze and map repository directory structure and architecture

**Use Cases:**
- Map directory hierarchy
- Identify important directories (source, tests, docs, config, build, assets)
- Locate entry points (main.py, index.js, Main.java, etc.)
- Find configuration files (Docker, CI/CD, environment, linting)
- Analyze project organization patterns
- Calculate project complexity

**Important Directory Categories:**
- **Source:** src, source, lib, app, application
- **Tests:** test, tests, __tests__, spec, specs
- **Documentation:** docs, doc, documentation, README
- **Configuration:** config, conf, configuration, settings
- **Build:** build, dist, target, bin, output
- **Assets:** assets, static, public, resources, media
- **Scripts:** scripts, bin, tools, utils
- **Examples:** examples, samples, demo, demos
- **Data:** data, datasets, fixtures, seed

**Entry Point Detection:**
- Python: main.py, app.py, run.py, __main__.py, server.py
- Node.js: index.js, app.js, server.js, main.js
- Java: Main.java, Application.java
- Go: main.go, cmd/main.go
- Rust: src/main.rs, src/lib.rs

**Configuration Files:**
- Docker: Dockerfile, docker-compose.yml
- CI/CD: .github/workflows, .gitlab-ci.yml, Jenkinsfile
- Version Control: .gitignore, .gitattributes
- IDE: .vscode, .idea
- Linting: .eslintrc, .pylintrc, .flake8
- Environment: .env, .env.example
- Security: SECURITY.md, .snyk

**Outputs:**
- Complete directory tree
- File count per directory
- Important directory categorization
- Entry point locations
- Configuration file inventory
- Project complexity assessment
- Large directory identification (50+ files)

---

## 6. Summary Context Generator (`summary_context.py`)

### Tool: `create_summary_context`
**Purpose:** Aggregate all analysis results into a unified summary for LLM consumption

**Use Cases:**
- Consolidate results from all analysis tools
- Calculate summary statistics
- Generate recommendations
- Prepare structured data for report generation
- Assess project characteristics (complexity, completeness)

**Aggregated Data:**
- Repository metadata
- Project type and confidence scores
- Complete dependency inventory
- Framework detection results
- Directory structure analysis
- Summary statistics

**Calculated Metrics:**
- Total files and directories
- Total dependencies
- Primary language
- Project complexity (simple/medium/complex/large)
- Feature flags (has tests, has docs, has CI/CD, has Docker)

**Outputs:**
- Comprehensive JSON summary
- Analysis timestamp
- Cross-tool insights
- Recommendations for improvements
- Security-relevant metadata

---

## 7. Report Generator (`create_report.py`)

### Tool: `generate_final_report`
**Purpose:** Generate comprehensive technical reports using Azure OpenAI GPT-4.1

**Use Cases:**
- Create security-focused technical reports
- CVE vulnerability matching optimization
- Detailed technology inventory with versions
- Security surface analysis
- CWE (Common Weakness Enumeration) mapping
- Attack vector classification

**Report Structure:**
1. Executive Summary
2. Technology Inventory & Versions
3. Security Surface Analysis
4. Component-Level Security Assessment
5. Potential Vulnerability Categories (CWE-Mapped)
6. Attack Vector Analysis
7. Structured Metadata for CVE Matching
8. Detailed Security Observations
9. Recommendations
10. Conclusion

**Security Focus:**
- Identify security-relevant components (authentication, authorization, input validation)
- Map to CWE categories (SQL Injection, XSS, CSRF, Buffer Overflow, etc.)
- Classify attack vectors (Network, Adjacent, Local, Physical)
- Generate machine-readable metadata tags
- Use CVE-matching terminology

**Structured Metadata:**
- TECHNOLOGIES: Framework and library names
- VERSIONS: Specific version numbers
- SECURITY_COMPONENTS: Auth, validation, etc.
- VULNERABILITY_KEYWORDS: sql, injection, xss, etc.
- ATTACK_SURFACES: web_api, database, file_system, etc.
- CWE_RELEVANT: CWE identifiers
- LANGUAGES: Programming languages used

**Outputs:**
- Markdown formatted technical report
- Security-focused analysis
- CVE-matchable descriptions
- Actionable recommendations

---

# 🔍 RETRIEVAL SYSTEM TOOLS (`/retrieval/agent_tools`)

## 8. CVE Retrieval Tool (`cve_retrieval_tool.py`)

### Tool: `cve_retrieval`
**Purpose:** Search and retrieve vulnerability data from CVE database using semantic similarity

**Actions:**

### Action: `search_by_text`
**Purpose:** Search CVEs using natural language queries

**Use Cases:**
- Find vulnerabilities by description (e.g., "SQL injection in web applications")
- Semantic similarity matching
- Query expansion with related terms
- CVSS score filtering

**Parameters:**
- query: Text description of vulnerability
- limit: Max results (default: 10)
- similarity_threshold: Min score (default: 0.7)
- expand_query: Enable query expansion

### Action: `search_similar`
**Purpose:** Find CVEs similar to a reference CVE

**Use Cases:**
- Discover related vulnerabilities
- Pattern matching across CVEs
- Vulnerability clustering

**Parameters:**
- cve_id: Reference CVE identifier (e.g., CVE-2021-1234)
- limit: Max results

### Action: `get_by_id`
**Purpose:** Retrieve specific CVE by identifier

**Use Cases:**
- Get detailed CVE information
- Fetch CVSS scores and vectors
- Retrieve vulnerability summaries

**Parameters:**
- cve_id: CVE identifier

### Action: `search_by_filters`
**Purpose:** Filter CVEs by attributes

**Use Cases:**
- CVSS score range filtering
- Severity-based search
- Attribute-based filtering

**Parameters:**
- min_cvss_score: Minimum score (0.0-10.0)
- max_cvss_score: Maximum score (0.0-10.0)
- filters: Additional filter criteria

### Action: `get_high_severity`
**Purpose:** Retrieve high-severity vulnerabilities

**Use Cases:**
- Critical vulnerability monitoring
- Severity-based prioritization
- Quick high-risk assessment

**Parameters:**
- min_cvss: Minimum CVSS score (default: 7.0)
- limit: Max results

### Action: `analyze_report`
**Purpose:** Analyze technical reports for vulnerabilities

**Use Cases:**
- Automated vulnerability detection
- Report parsing and matching
- Technology-to-CVE mapping

**Parameters:**
- analysis_report: Technical report object

### Action: `analyze_markdown`
**Purpose:** Extract vulnerabilities from markdown security reports

**Use Cases:**
- Parse security analysis documents
- Find relevant CVEs from report text
- Automated vulnerability identification

**Parameters:**
- markdown_report: Markdown document text
- top_k: Number of top matches (default: 10)

**Outputs:**
- CVE identifiers
- Vulnerability summaries
- CVSS scores and vectors
- Similarity scores
- Match metadata

---

## 9. Codebase Indexing Tool (`codebase_indexing_tool.py`)

### Tool: `codebase_indexing`
**Purpose:** Index and search code repositories using semantic embeddings (FAISS)

**Actions:**

### Action: `index`
**Purpose:** Index entire codebase into searchable vector database

**Use Cases:**
- Create semantic code search database
- Index large codebases
- Enable natural language code queries
- Build code knowledge base

**Parameters:**
- codebase_path: Path to repository
- db_path: Database storage location
- index_type: FAISS index type (flat/ivf/hnsw)
- batch_size: Files per batch (default: 10)
- max_file_size_mb: Max file size (default: 5.0)
- overwrite: Replace existing database

**Supported File Types:**
- Programming languages: .py, .js, .ts, .java, .c, .cpp, .go, .rs, .php, .rb, .swift, .kt, .scala
- Markup/Config: .json, .xml, .yaml, .yml, .md, .txt
- Web: .html, .css, .scss, .jsx, .tsx, .vue
- Scripts: .sh, .bash, .ps1, .sql

### Action: `search`
**Purpose:** Search codebase using natural language queries

**Use Cases:**
- Find code by functionality description
- Locate security-critical code
- Discover implementation patterns
- Code navigation and exploration

**Parameters:**
- query: Natural language search query
- db_path: Database location
- top_k: Number of results (default: 10)

**Examples:**
- "user authentication and login logic"
- "database connection handling"
- "input validation functions"
- "SQL query construction"

### Action: `get_stats`
**Purpose:** Get database statistics and metadata

**Use Cases:**
- Database health check
- Index size monitoring
- File count verification

**Parameters:**
- db_path: Database location

### Action: `clear`
**Purpose:** Clear/delete FAISS database

**Use Cases:**
- Reset index
- Clean up storage
- Prepare for re-indexing

**Parameters:**
- db_path: Database location

### Action: `analyze_codebase`
**Purpose:** Analyze codebase without creating full index

**Use Cases:**
- Quick codebase overview
- File type distribution
- Size analysis

**Parameters:**
- codebase_path: Path to repository

### Action: `auto_index`
**Purpose:** Automatically index codebase from configuration

**Use Cases:**
- Use default settings from .env
- Simplified indexing
- Automated workflows

**Outputs:**
- Indexed file count
- Database statistics
- Search results with similarity scores
- File paths and content previews
- Metadata (file size, line count, extensions)

---

## 10. Analysis Orchestrator Tool (`analysis_orchestrator.py`)

### Tool: `analysis_orchestrator`
**Purpose:** Orchestrate complete vulnerability analysis pipeline

**Actions:**

### Action: `run_full`
**Purpose:** Execute end-to-end CVE analysis workflow

**Pipeline Steps:**
1. Fetch CVE data (by ID or from markdown)
2. Decompose query using Hype (Hypothetical Answer Generation)
3. Semantic search for each decomposed query
4. Read matched code files
5. Consolidate results
6. Generate reports (JSON and PDF)

**Use Cases:**
- Automated CVE impact analysis
- Vulnerability-to-codebase mapping
- Security assessment workflows
- Multi-stage analysis automation

**Parameters:**
- cve_id: CVE identifier to analyze
- markdown_report: Markdown report to analyze
- db_path: FAISS database path
- top_k: Results per subquery (default: 10)
- max_files_to_read: Max files to consolidate (default: 50)
- generate_pdf: Create PDF report (default: true)

**Workflow Details:**

**Step 1 - CVE Retrieval:**
- Fetch CVE by ID or extract from markdown
- Get vulnerability summary and metadata

**Step 2 - Query Decomposition (Hype):**
- Generate multiple search angles
- Create hypothetical answer variations
- Expand vulnerability description

**Step 3 - Semantic Search:**
- Search codebase for each decomposed query
- Collect matching code files
- Score relevance

**Step 4 - File Reading:**
- Read content of matched files
- Extract code context
- Build evidence

**Step 5 - Consolidation:**
- Deduplicate files
- Aggregate scores
- Group by file path
- Calculate average relevance

**Step 6 - Report Generation:**
- Create JSON analysis report
- Generate professional PDF report
- Save to logs/reports directory

### Action: `generate_report`
**Purpose:** Generate report from pre-collected matches

**Use Cases:**
- Report generation from cached results
- Custom report creation
- Batch reporting

**Parameters:**
- matches: List of matched files with scores
- filename: Output filename

**Outputs:**
- JSON analysis report with:
  - CVE identifier
  - Matched files with scores
  - Query decompositions
  - Content previews
- PDF report with professional formatting
- Consolidated file rankings
- Report file paths

---

## 11. Report Writer (`report_writer.py`)

### Purpose: Utility for writing and consolidating analysis reports

**Functions:**

### `write_report()`
**Purpose:** Save analysis report to JSON file

**Use Cases:**
- Persist analysis results
- Create timestamped reports
- Archive vulnerability assessments

**Outputs:**
- JSON file in logs/reports/
- Timestamp-based naming
- Structured report data

### `consolidate_matches()`
**Purpose:** Consolidate and deduplicate search matches

**Use Cases:**
- Merge results from multiple queries
- Calculate aggregate scores
- Group by file path
- Remove duplicates

**Processing:**
- Groups matches by file path
- Aggregates similarity scores
- Collects associated queries
- Calculates average scores
- Sorts by relevance

**Outputs:**
- Deduplicated file list
- Average relevance scores
- Associated query list
- Content snippets
- Total file count

---

## 12. PDF Report Generator (`pdf_report_generator.py`)

### Purpose: Generate professional security analysis PDF reports

**Features:**

**Document Styling:**
- Custom paragraph styles (title, subtitle, headers, code blocks)
- Color-coded sections
- Professional formatting
- Page headers and footers
- Branding and watermarks

**Report Sections:**
- Cover page with metadata
- Executive summary
- CVE details (ID, CVSS score, severity)
- Decomposed query analysis
- Matched files section with:
  - File paths
  - Relevance scores
  - Content previews
  - Syntax-highlighted code snippets
- Statistics and metrics
- Conclusions and recommendations

**Visual Elements:**
- Tables with colored headers
- Code blocks with syntax highlighting
- Info boxes and warning boxes
- Progress indicators
- Severity badges

**Use Cases:**
- Client-facing security reports
- Compliance documentation
- Audit trail generation
- Executive summaries
- Technical documentation

**Outputs:**
- Professional PDF document
- Formatted code listings
- Visual severity indicators
- Comprehensive metadata
- Timestamped reports

---

# 🔧 SUPPORTING COMPONENTS

## Query Processor (`query_processor.py`)

### Purpose: Process text queries and generate embeddings using Google Gemini

**Functions:**

### `generate_embedding()`
**Purpose:** Generate vector embeddings for text

**Use Cases:**
- Convert text to vector representation
- Enable semantic search
- Query processing

**Features:**
- Gemini API integration
- API key rotation
- Retry logic with exponential backoff
- Query preprocessing
- Context addition for security queries

### `expand_query()`
**Purpose:** Expand queries with related terms

**Use Cases:**
- Improve search recall
- Generate query variations
- Synonym expansion

**Security Term Expansions:**
- buffer overflow → buffer overrun, stack overflow, heap overflow
- sql injection → sqli, database injection, sql attack
- xss → cross-site scripting, script injection
- csrf → cross-site request forgery, session riding
- rce → remote code execution, code injection

### `validate_embedding()`
**Purpose:** Validate embedding format and dimensions

**Outputs:**
- 768-dimensional vectors (standard models)
- 3072-dimensional vectors (Gemini)
- Normalized embeddings

---

## Retrieval Service (`retrieval_service.py`)

### Purpose: Main service for CVE retrieval and similarity search

**Core Functions:**

### `search_by_text()`
- Text-based CVE search
- Query expansion
- Similarity scoring
- Result deduplication

### `search_by_filters()`
- Attribute-based filtering
- CVSS score ranges
- Metadata filtering

### `search_by_cve_id()`
- Direct CVE lookup
- Exact match retrieval

### `get_similar_cves()`
- Related vulnerability discovery
- Similarity-based matching

**Features:**
- Milvus vector database integration
- Configurable similarity thresholds
- Result limiting and pagination
- Score-based ranking

---

## Codebase Indexer (`codebase_indexer.py`)

### Purpose: Index codebases into FAISS vector database

**Functions:**

### `index_codebase()`
**Purpose:** Complete codebase indexing workflow

**Process:**
1. Scan directory for code files
2. Extract file content and metadata
3. Generate embeddings using Gemini
4. Create/update FAISS index
5. Store metadata alongside vectors
6. Save index to disk

**Features:**
- Batch processing
- Progress tracking
- Error handling
- Statistics collection
- Overwrite control

### `search_codebase()`
**Purpose:** Search indexed code

**Features:**
- Natural language queries
- Semantic similarity scoring
- Metadata retrieval
- Result ranking

---

## FAISS Manager (`faiss_manager.py`)

### Purpose: Manage FAISS vector database operations

**Index Types:**
- **Flat:** Exact search, no training needed
- **IVF:** Inverted file index, faster approximate search
- **HNSW:** Hierarchical Navigable Small World, balanced speed/accuracy

**Functions:**

### `create_index()`
- Initialize FAISS index
- Configure index type
- Set dimension

### `add_embeddings()`
- Insert vectors
- Attach metadata
- Train index (if needed)

### `search()`
- Query vector database
- Return top-k results
- Include distances/similarities

### `save()` / `load()`
- Persist index to disk
- Load index from disk
- Manage metadata files

---

## File Processor (`file_processor.py`)

### Purpose: Process and extract code files for indexing

**Features:**

**File Type Support:**
- 40+ file extensions
- Programming languages
- Configuration files
- Documentation files
- Web technologies

**Filtering:**
- Skip directories (node_modules, __pycache__, .git, etc.)
- File size limits
- Binary file detection
- Encoding handling

**Metadata Extraction:**
- File path and name
- Extension and language
- File size and line count
- Character count
- Content preview

**Functions:**

### `scan_directory()`
- Recursive directory traversal
- File filtering
- Metadata collection

### `_process_file()`
- Read file content
- Extract metadata
- Handle encoding errors

---

# 🤖 REACT AGENT (`src/react_agent.py`)

## Purpose: Autonomous repository analysis agent using LangGraph

**Architecture:**
- ReAct (Reasoning + Acting) methodology
- State-based workflow
- Tool selection autonomy
- Iterative exploration

**Agent Capabilities:**
1. **Autonomous Decision Making:**
   - Decides which tools to use
   - Plans analysis strategy
   - Adapts based on findings

2. **Iterative Workflow:**
   - Clone/load repository
   - Explore structure
   - Analyze components
   - Generate report

3. **Tool Integration:**
   - All 7 repository analysis tools
   - Web search (Tavily)
   - File operations
   - Report generation

4. **Observability:**
   - LangSmith tracking
   - Decision logging
   - Tool usage analytics
   - Performance monitoring

**Workflow:**
1. START: Clone repository
2. EXPLORE: Understand structure (3-5 steps)
3. ANALYZE: Run analysis tools (4 steps)
4. COMPLETE: Generate final report (1 step)

**Target:** 10-15 steps total for efficiency

---

# 📊 USE CASE SCENARIOS

## Scenario 1: Security Vulnerability Assessment

**Objective:** Assess if a codebase is vulnerable to a specific CVE

**Workflow:**
1. Index codebase using `codebase_indexing` (action: index)
2. Retrieve CVE details using `cve_retrieval` (action: get_by_id)
3. Run full analysis using `analysis_orchestrator` (action: run_full)
4. Review generated PDF and JSON reports

**Output:**
- List of potentially vulnerable files
- Relevance scores
- Code snippets for manual review
- Professional PDF report

---

## Scenario 2: Repository Security Audit

**Objective:** Generate comprehensive security report for a repository

**Workflow:**
1. Use ReAct Agent to analyze repository
2. Agent automatically:
   - Clones repository
   - Detects project type
   - Extracts dependencies
   - Identifies frameworks
   - Analyzes structure
3. Generates CVE-matchable technical report
4. Review security-focused findings

**Output:**
- Technology inventory with versions
- Security surface analysis
- CWE mappings
- Attack vector classifications
- Structured metadata for CVE matching

---

## Scenario 3: Dependency Vulnerability Scanning

**Objective:** Identify vulnerable dependencies in a project

**Workflow:**
1. Analyze dependencies using `analyze_dependencies`
2. Extract all package names and versions
3. For each critical package:
   - Search CVEs using `cve_retrieval` (action: search_by_text)
   - Filter by CVSS score
4. Compile vulnerability report

**Output:**
- List of dependencies
- Known CVEs for each package
- Severity assessments
- Update recommendations

---

## Scenario 4: Similar Vulnerability Discovery

**Objective:** Find similar vulnerabilities to a known CVE

**Workflow:**
1. Start with a reference CVE
2. Use `cve_retrieval` (action: search_similar)
3. Get top-k similar CVEs
4. Analyze patterns and commonalities

**Output:**
- Related CVE list
- Similarity scores
- Vulnerability patterns
- Mitigation strategies

---

## Scenario 5: Code Search for Security Patterns

**Objective:** Find specific security-relevant code patterns

**Workflow:**
1. Index codebase using `codebase_indexing`
2. Search for patterns:
   - "SQL query construction"
   - "password hashing"
   - "user input validation"
   - "authentication logic"
3. Review matched files

**Output:**
- Files containing patterns
- Code snippets
- Relevance scores
- Security assessment

---

# 🔐 SECURITY-FOCUSED FEATURES

## CVE Matching Optimization

**Technology Inventory:**
- Exact version numbers extraction
- Framework and library cataloging
- Language identification

**Security Surface Analysis:**
- Authentication mechanisms
- Authorization controls
- Input validation points
- Database access patterns
- File operations
- API endpoints

**CWE Mapping:**
- SQL Injection (CWE-89)
- Cross-Site Scripting (CWE-79)
- CSRF (CWE-352)
- Buffer Overflow (CWE-119)
- Authentication Issues (CWE-287)
- Path Traversal (CWE-22)
- Command Injection (CWE-78)

**Attack Vector Classification:**
- Network (AV:N) - Remotely exploitable
- Adjacent (AV:A) - Local network
- Local (AV:L) - Local system access
- Physical (AV:P) - Physical access

---

# 📈 TECHNICAL SPECIFICATIONS

## Vector Embeddings
- **Model:** Google Gemini (text-embedding-004)
- **Dimension:** 768 (standard) / 3072 (Gemini)
- **Task Type:** retrieval_query
- **Similarity Metric:** L2 distance / Cosine similarity

## Vector Databases
- **CVE Database:** Milvus
- **Codebase Database:** FAISS
- **Index Types:** Flat L2, IVF, HNSW

## LLM Integration
- **Primary Model:** Azure OpenAI GPT-4.1
- **API Version:** 2024-12-01-preview
- **Temperature:** Configurable
- **Max Tokens:** Configurable

## Supported Languages
- Python, JavaScript/TypeScript, Java, C#, Go, Rust, PHP, Ruby, C++, Swift, Kotlin, Scala, R, Objective-C

## File Processing
- **Max File Size:** 5 MB (configurable)
- **Batch Size:** 10 files (configurable)
- **Encoding:** UTF-8
- **40+ file extensions supported**

---

# 🎯 KEY DIFFERENTIATORS

1. **Autonomous Analysis:** ReAct agent makes intelligent decisions
2. **Multi-Stage Pipeline:** From repository to vulnerability assessment
3. **Semantic Search:** Natural language queries for code and CVEs
4. **Professional Reports:** PDF generation with formatting
5. **CVE Optimization:** Reports designed for vulnerability matching
6. **Comprehensive Coverage:** 12 specialized tools working together
7. **Observability:** Complete tracking with LangSmith
8. **Flexibility:** Support for multiple languages and frameworks

---

# 📝 SUMMARY

Agent Axios provides a complete solution for:
- ✅ Autonomous repository analysis
- ✅ Security vulnerability assessment  
- ✅ CVE database search and retrieval
- ✅ Semantic code search and indexing
- ✅ Professional report generation
- ✅ Multi-language support
- ✅ End-to-end automation

**Total Tools:** 12 core tools + 8 supporting components
**Languages Supported:** 15+
**File Types:** 40+
**Use Cases:** Security auditing, vulnerability assessment, code analysis, compliance reporting

---

*Generated for Agent Axios - Security Analysis and Vulnerability Detection System*
