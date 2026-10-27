# My Assignment 2 Requirements

## My scope and checklist conventions

I use this file as my single checklist for outstanding work on CSCI 599 Agentic AI Assignment 2, **Multi-Agent System with RAG and Orchestration**. I target every full-credit criterion in the supplied assignment; I do not treat this checklist as a guarantee of a grade. My assignment is individual work, represents 15% of the course grade, and has a base rubric of 100% with no bonus criteria. I obtain my actual deadline from Brightspace and my late/regrade rules from the syllabus. [PDF pp. 1, 14, 16]

I mark an item `[x]` only after I review its implementation or deliverable and have evidence that it satisfies the requirement. An unchecked item is not a claim of completion. I record completion evidence next to the relevant item as I progress. I keep conditional items unchecked until I either satisfy them or explicitly record why they are not applicable to my selected architecture; I do not represent an unused alternative as implemented.

- [ ] **WORK-01 — My folder boundary:** I keep all project work, generated files, dependencies, caches, test outputs, and deliverables inside `CSCI 599/Assignment 2/`; I do not inspect other assignment folders.
- [ ] **WORK-02 — My review discipline:** I review every implementation and documentation change and run the checks appropriate to that change before calling it complete.
- [ ] **WORK-03 — My documentation voice:** I write my original documentation in first person and describe my actual work, observations, and decisions accurately.
- [ ] **WORK-04 — My single backlog:** I keep unfinished steps, future implementation notes, and completion checklists only in this file. My other deliverables describe implemented behavior and verified results.
- [ ] **WORK-05 — My clarification discipline:** I ask for clarification when a material requirement or decision is unknown instead of silently inventing an answer.
- [x] **WORK-06 — My standing instructions:** I maintain `agent_docs/agents.md` with my folder boundary, simple-code/no-unused-code rules, first-person documentation rule, strict testing gates, CI/CD policy, and live acceptance requirements. I reviewed its coverage against my instructions on 2026-10-26.
- [ ] **WORK-07 — My code hygiene:** I keep only used files, imports, dependencies, and code; I require linting plus manual simplicity review for every change.
- [ ] **WORK-08 — My strict acceptance gate:** I require zero failed, errored, skipped, xfailed, or unexpectedly passing tests and a nonempty suite. I do not weaken checks or bypass failures.
- [x] **WORK-09 — My documentation layout:** I use lowercase snake_case for project-owned directories. I keep my guidelines at `agent_docs/agents.md`, my architecture at `agent_docs/architecture.md`, and my supplied Markdown references unchanged under `agent_docs/reference_docs/`. Only `README.md` may be a root Markdown file. I preserve required tool/dependency directory names.
- [ ] **WORK-10 — My submission-path conflict:** I reconcile my requested Markdown layout with the PDF's explicit `docs/architecture.md`, `docs/evaluation.md`, and root `PROCESS_LOG.md` submission paths before submission, through instructor acceptance or an explicitly approved submission-layout exception. My working copies belong in `agent_docs/`; I do not silently claim the different paths meet the submission contract.

## My proposed architecture review

I describe my proposed design in [architecture.md](architecture.md). I distinguish these design choices from implemented or benchmarked behavior. I retain the original rubric paths elsewhere in this checklist as source requirements, subject to WORK-10.

- [x] **DESIGN-01:** I document my Supervisor topology, three specialist roles/tools, provider policy, state schema, ingestion/retrieval/synthesis flow, deployment boundaries, and design critique with four Mermaid diagrams. I reviewed the design against my requested book features and rubric.
- [ ] **DESIGN-02:** I review the proposed Supervisor topology, Pinecone/GCS/Firestore storage split, background ingestion job, durable checkpoint adapter, and NVIDIA/OpenAI/Anthropic task preferences against access, complexity, cost, and measured quality before fixing the implementation choices.
- [ ] **DESIGN-03:** I validate chapter chunking, retrieval k, ordered synthesis, evidence reconciliation, and major-point coverage for substantial fiction and nonfiction books; my initial 800-token/120-overlap/top-k-6 values are tunable hypotheses.
- [ ] **DESIGN-04:** I finalize upload format/size/token limits, curated titles, identity/session isolation, cancellation behavior, and spoiler rules, including treatment of external web results.
- [ ] **DESIGN-05:** I implement and test idempotent ingestion, consistency/readiness publication across stores, job retry/progress recovery, and same-version web/job deployments; my existing workflow does not yet deploy the ingestion job.
- [ ] **DESIGN-06:** I verify the chosen Firestore-backed checkpoint adapter, scoped fact queries, large-evidence references, and instance-replacement recovery rather than assuming an in-memory graph provides durability.
- [ ] **DESIGN-07:** I benchmark provider selection and bounded fallback on normal queries, demonstrate multiple active providers and two-agent Tavily sharing, and compare UX latency/cost before accepting optimization claims.
- [x] **DESIGN-08:** I define my minimal visual system, responsive layout, reusable components, content views, streaming behavior, trace/citation surfaces, accessibility targets, and failure states in [design.md](design.md). On 2026-10-26 I verified its local links, source anchor, five SSE event types, four trace badge types, and absence of a duplicate implementation checklist. My 16 proposed text/background combinations exceed 4.5:1 contrast (minimum 5.63:1); functional control borders exceed 3:1 on both backgrounds. These are specification checks, not implemented-UI evidence.
- [ ] **DESIGN-09:** I implement and verify the design's layout at desktop/tablet/mobile sizes, 200% zoom, keyboard/focus behavior, assistive-technology announcements, reduced motion, actual rendered contrast, and safe dynamic-content rendering.
- [ ] **DESIGN-10:** I test the design's submit locking, per-turn context/evidence, incremental rendering, Stop/Reset cancellation, interrupted streams, upload states, spoiler boundaries, and source/purchase-link behavior in a real browser against the deployed backend.

## My source inventory and interpretation

I reviewed all eight supplied documents. I retain the PDF in `docs/` and preserve the seven Markdown references under `agent_docs/reference_docs/`. I preserve the supplied source documents as reference material. My PDF page references below use the PDF's 16 physical pages.

| My source | My use of the source |
| --- | --- |
| [Assignment_2_Description (1).pdf](../docs/Assignment_2_Description%20%281%29.pdf) | I treat the assignment description, submission contract, and full-credit rubric as my primary requirements. |
| [alternative_a2a_pattern.md](reference_docs/alternative_a2a_pattern.md) | I use its additional protocol evidence requirements if I choose A2A. |
| [alternative_deepeval_pattern.md](reference_docs/alternative_deepeval_pattern.md) | I treat DeepEval as an optional addition, never as a replacement for RAGAS without an explicit instructor change. |
| [alternative_gcs_persistence.md](reference_docs/alternative_gcs_persistence.md) | I use its mount, configuration, and durability requirements if I choose GCS/GCSFuse. |
| [alternative_pinecone_pattern.md](reference_docs/alternative_pinecone_pattern.md) | I use its SDK, integration, configuration, and deployment guidance if I choose Pinecone. |
| [alternative_vertex_ai_search.md](reference_docs/alternative_vertex_ai_search.md) | I use its qualifying live-source and deployment conditions if I choose Vertex AI Search. |
| [cost_analysis.md](reference_docs/cost_analysis.md) | I use its usage-measurement method; I verify model availability and prices before treating its examples as deployable. |
| [frontend_vibecode_prompt.md](reference_docs/frontend_vibecode_prompt.md) | I use its reference UI/API contract as implementation guidance, distinguished below from rubric requirements. |

I distinguish **required** assignment outcomes, **conditional** requirements for a selected alternative, **reference guidance**, and **my additional quality requirements**. I do not turn example model families, reference timings, example `top-k=5`, example deployment sizing, or optional provider counts into grading thresholds. I use `.env.example`, as explicitly required by the PDF, even where supporting files abbreviate the filename as `env.example`.

## My rubric coverage map

| My full-credit area | Weight | My primary checklist sections |
| --- | ---: | --- |
| Multi-agent orchestration correctness | 25% | ARCH, AGENT |
| RAG implementation quality | 20% | RAG, EVAL |
| LLM routing logic | 15% | ROUTE |
| Frontend usability | 15% | UI |
| Deployment and scalability | 15% | DEPLOY, STATE, SUBMIT |
| A2A integration or MCP tool sharing | 10% | SHARE |
| **My total coverage** | **100%** | I also satisfy the cross-cutting submission, configuration, evaluation, and integrity requirements. |

## My assignment decisions and clarification gates

- [ ] **DEC-01:** I confirm my Brightspace deadline and applicable syllabus grace-day, late-submission, and Piazza regrade-window rules. [PDF pp. 1, 16]
- [ ] **DEC-02:** I establish what my Assignment 1 implemented from information supplied within this folder or conversation, and demonstrate equal or greater complexity with a distinct multi-agent retrieval architecture rather than the Assignment 1 single-agent MCP loop. [PDF p. 1]
- [ ] **DEC-03:** I select my project domain and a substantial, genuinely structured corpus; I document why it supports meaningful retrieval. [PDF pp. 1, 3]
- [ ] **DEC-04:** I select Supervisor or Hierarchical LangGraph orchestration, or explicitly select the permitted Codex worktree alternative with equivalent evidence. [PDF pp. 2, 14]
- [ ] **DEC-05:** I select at least three eligible specialized agents, at least two accessible generation providers, my embedding model, and Pinecone or Chroma. [PDF pp. 1–8]
- [ ] **DEC-06:** I select Tavily Remote MCP or the qualifying externally updated domain-retrieval alternative, and independently choose MCP sharing or A2A for the 10% protocol criterion. [PDF pp. 3, 6–7, 16]
- [ ] **DEC-07:** I explicitly choose whether my system is stateless/single-turn or claims durable multi-turn state; I select a durable external store if I make that claim. [PDF pp. 4, 10–11]
- [ ] **DEC-08:** I confirm provider access, GCP project/billing/credits, and my spending constraints without placing real credentials in documentation. [PDF pp. 6, 9]

### My supplied baseline and preferred direction

My Assignment 1 was a simple course study planner using an NVIDIA Nemotron model, LangChain, Python, FastAPI, a simple frontend, and seven tools, including Tavily and a weather API. I use this supplied description as my baseline without accessing the Assignment 1 folder. DEC-02 remains open until I demonstrate the increased complexity in my actual Assignment 2 implementation.

My preferred Assignment 2 direction is a book summarizer/reading companion that can ingest a 500–600-page book and help me understand its story with strong detail coverage. I distinguish an achievable goal of traceable coverage of major events, characters, and chapter developments from an impossible guarantee that a much shorter summary loses no information. My exact corpus, accepted coverage criteria, provider pair, and implementation design remain decisions under DEC-03 through DEC-08.

### My confirmed product scope and available services

I have selected a book-reading companion for both fiction and nonfiction, with a curated library for rubric evidence and user uploads as part of my intended product. I can access OpenAI, Anthropic, and NVIDIA Nemotron, and I have Google Cloud credits. I have not verified working credentials, exact deployable model IDs, remaining credits, or a spending ceiling. My GitHub repository is `https://github.com/Arya-Wadhwani07/book_reader`; Assignment 2 is its intended root.

- [ ] **BOOK-01:** I support both fiction and nonfiction and adapt the analysis to the book: story/characters for fiction, and arguments, concepts, evidence, real people, or historical events when applicable to nonfiction. I do not invent a fictional plot for a nonfiction book.
- [ ] **BOOK-02:** I provide a substantial curated library with documented sources and a reproducible ingestion path for grading.
- [ ] **BOOK-03:** I support user uploads with validated formats and size limits, clear extraction/ingestion errors and progress, and isolation between uploaded books/users. I define supported formats before implementation.
- [ ] **BOOK-04:** I provide selectable summary depth, chapter-level expansion, and whole-book synthesis with source citations and measured coverage rather than a lossless-summary promise.
- [ ] **BOOK-05:** I provide character sketches and deep dives into relationships, motivations, and development, grounded in the text; I label interpretation and uncertainty.
- [ ] **BOOK-06:** I provide major-event deep dives, chronology, causes, and consequences, retaining references to supporting passages.
- [ ] **BOOK-07:** I include an about-the-author section with cited sources and a clear distinction between book content and externally researched biographical information.
- [ ] **BOOK-08:** I research related film/TV adaptations through live web search, distinguish actual adaptations from loosely related works, and avoid asserting a match without source evidence.
- [ ] **BOOK-09:** I find source-backed purchase links, including hardcover options when available, and distinguish editions/formats and current availability without inventing prices or links. I only link to vendors; I do not purchase anything.
- [ ] **BOOK-10:** I keep researched author, adaptation, and buying information separate from book-grounded summaries, preserve spoiler/depth choices consistently, and test both content types.

### My one-time deployment inspection record

On 2026-10-26, I used my explicit one-time exception to read Assignment 1's deployment script, Dockerfile, deployment-related README excerpts, placeholder environment example, build exclusions, and readiness evidence. I did not open its real `.env` or copy API keys. That inspection is complete; I do not access Assignment 1 again.

I recorded project ID `clean-mountain-511522-d0`, project number `252917810263` as present in its recorded URL, region `us-west1`, Artifact Registry repository `csci599`, and existing service `coursework-studio`. I use a separate `book-companion` service/image for Assignment 2. These are historical configuration facts, not a fresh verification of my cloud permissions or resource availability. Assignment 1's readiness evidence recorded `/readyz` success and a `/healthz` 404; I require an explicit readiness contract and live verification for Assignment 2.

## My CI/CD implementation and activation checklist

- [ ] **CICD-01:** I use Assignment 2 as the root of my `book_reader` Git repository, with `.github/workflows/ci-cd.yml` running CI on pushes/PRs and automatic deployment from `main` after successful gates.
- [ ] **CICD-02:** I configure GitHub repository variables `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SERVICE_ACCOUNT`, `GCP_RUNTIME_SERVICE_ACCOUNT`, `CLOUD_RUN_SECRETS`, `CLOUD_RUN_ENV_VARS`, and `SMOKE_QUERY`. My secrets variable contains Secret Manager references (`ENV_NAME=secret-name:version`), not credential values; my runtime variables contain only non-secret model/service configuration.
- [ ] **CICD-03:** I configure Workload Identity Federation restricted to `Arya-Wadhwani07/book_reader` and `refs/heads/main`, a deployment identity able to push images/deploy/manage service traffic and act as my runtime identity, and a runtime identity with access only to the required secrets/data. I enable required Google APIs and verify the existing registry before deployment.
- [ ] **CICD-04:** I implement the application, exact-pinned runtime requirements, runnable non-root Dockerfile, `tests/test_app.py`, and `tests/live/test_acceptance.py`; my workflow intentionally fails while these required artifacts are absent.
- [ ] **CICD-05:** I use the release-checker HTTP contract: `GET /readyz` returns HTTP 200 JSON with `ready: true`; `/` serves HTML; `POST /api/chat` accepts `query` and `session_id` and emits JSON SSE events. My token payload has `text`; citation has `source_id`/`chunk_id`; traces include `agent_route` with `agent`/`reason`, `llm_route` with `provider`/`model`/`reason`, and `rag_retrieval` with `chunk_ids`; successful `done` has `success: true`.
- [ ] **CICD-06:** I pass lint/format checks, the complete offline test suite and no-skips report gate, container build/non-root checks, candidate live smoke/full acceptance, traffic promotion, and public URL smoke/full acceptance. I configure my live suite to use `BASE_URL` and define `SMOKE_QUERY` against my actual curated corpus.
- [ ] **CICD-07:** I execute and verify a real GitHub Actions deployment and record the run URL, tested commit, deployed revision, and public Cloud Run URL. Local tests of my release-checking code alone do not satisfy this requirement.
- [ ] **CICD-08:** I test cold/warm behavior, streaming timing, all selected agents/providers, web-tool sharing, uploads, isolation, fiction/nonfiction features, citations, and failure handling through my complete live acceptance suite; I do not confuse the narrower release smoke check with this full suite.
- [ ] **CICD-09:** I verify first-deployment behavior for the candidate traffic policy and define/test recovery for failures after traffic promotion; the current workflow fails on a public check failure but does not automatically roll back.
- [ ] **CICD-10:** I add selected persistence/index provisioning and mounts to deployment if the chosen architecture needs them, confirm costs/limits, and keep required test evidence free of credentials.
- [x] **CICD-11 — My local pipeline-tooling verification:** On 2026-10-26 I passed all 37 release-checker tests with zero failures/errors/skips, including real pytest report rejection tests for failed, skipped, xfailed, and unexpectedly passing probes. I passed Ruff lint/format checks, parsed my workflow YAML, and syntax-checked all 14 shell blocks. My local evidence is `reports/tooling.xml`; I ran on local Python 3.9.6, not the workflow's Python 3.13 runner. I initialized my local `main` repository and configured the supplied GitHub origin; I have not pushed or run cloud deployment. This evidence verifies the tooling only, not CICD-06 through CICD-09 or the application.

My current activation blockers are the absent application/container/full acceptance suite, unconfigured GitHub-to-GCP identity and repository variables, unverified cloud permissions, and an undecided exact corpus/provider configuration. My local shell has no `gcloud` or `gh` executable available on PATH. I keep these outstanding steps here rather than in other documentation files.

## My orchestration and specialized agents — 25%

- [ ] **ARCH-01:** I build a working multi-agent system that accepts a user query, delegates work, coordinates results, and completes an answer end to end. [PDF pp. 1–2, 14–15]
- [ ] **ARCH-02:** I implement state/task-driven delegation with inspectable decisions, rather than cosmetic agents or fixed transitions pretending to be orchestration. [PDF pp. 2, 14]
- [ ] **ARCH-03:** I handle a worker failure without crashing the whole graph or collapsing the complete workflow, and expose understandable failure evidence. [PDF p. 14]
- [ ] **ARCH-04:** I document my nodes/agents, communication paths, relevant state schema, responsibilities, and tool access in `docs/architecture.md`. [PDF pp. 12, 14]
- [ ] **ARCH-05 — If I choose LangGraph:** I compile and execute a LangGraph state graph with a clean Supervisor or Hierarchical pattern; my supervisor routes workers based on inspectable state fields. [PDF pp. 2, 14]
- [ ] **ARCH-06 — If I choose Supervisor:** I implement a central supervisor that knows its workers, delegates to them, and receives their results. [PDF p. 2]
- [ ] **ARCH-07 — If I choose Hierarchical:** I implement a top-level supervisor coordinating team supervisors, with worker coordination inside teams and explicit cross-team escalation. [PDF p. 2]
- [ ] **ARCH-08 — If I choose Codex worktrees:** I execute at least three behaviorally specialized agents through distinct delegated tasks/worktrees; I make delegation, integration, task ownership, coordination, and failure handling inspectable and document the architecture. I keep all worktrees within my folder boundary. [PDF pp. 2, 14]
- [ ] **AGENT-01:** I implement at least three specialized agents from Research, Code, Data, and Summary; I do not count my Router/Supervisor toward the three. [PDF pp. 1–2]
- [ ] **AGENT-02:** I give every counted specialist a distinct system prompt and distinct tool access that produces genuinely different behavior. [PDF p. 2]
- [ ] **AGENT-03 — If I select Research:** I implement web search plus RAG retrieval and grounded answers with citations. [PDF p. 1]
- [ ] **AGENT-04 — If I select Code:** I implement code generation or code analysis over a supplied file or corpus. [PDF p. 1]
- [ ] **AGENT-05 — If I select Data:** I implement structured data queries over SQLite, CSV, or a JSON document store. [PDF p. 1]
- [ ] **AGENT-06 — If I select Summary:** I implement document summarization that preserves citations. [PDF p. 1]
- [ ] **AGENT-07:** I exercise at least one specialist using RAG and at least one using live/current knowledge retrieval in my deployed system. [PDF pp. 1, 3]
- [ ] **AGENT-08:** I document each agent's model/provider choice and demonstrate cooperation rather than merely exposing unrelated model calls. [PDF pp. 1, 13]

## My RAG implementation — 20%

- [ ] **RAG-01:** I select a corpus with genuine retrieval structure, such as research papers, course readings, technical documentation, or public organizational documentation; I avoid a five-file toy corpus. The PDF does not define an exact minimum document count. [PDF pp. 3, 15]
- [ ] **RAG-02:** I implement the RAG pipeline with LangChain LCEL and document the corpus source and pipeline shape. [PDF pp. 4, 12]
- [ ] **RAG-03:** I load source documents, chunk them using a documented strategy, and generate embeddings. [PDF pp. 3, 7–8]
- [ ] **RAG-04:** I store chunks and embeddings in Pinecone or Chroma and preserve stable source/chunk metadata for citations. [PDF pp. 3, 7–8, 15]
- [ ] **RAG-05:** I retrieve top-k chunks using vector similarity and document my chosen k; I do not substitute keyword search for embedding-based retrieval. [PDF pp. 3, 12, 15]
- [ ] **RAG-06:** I inject retrieved chunks into my generation prompt and document the augmentation prompt template. [PDF pp. 3, 12]
- [ ] **RAG-07:** I generate grounded answers whose citations link back to the actual retrieved source chunks and source document identifiers. [PDF pp. 3–4, 15]
- [ ] **RAG-08:** I implement ingestion error handling, configurable chunking, and re-indexing behavior rather than copying the PDF's illustrative pseudocode as complete code. [PDF pp. 7–8]
- [ ] **RAG-09:** I use a verified embedding configuration consistently for ingestion and query retrieval, accounting for vector dimensions if I choose local `sentence-transformers` embeddings. [PDF p. 6]
- [ ] **RAG-10 — If I choose Chroma:** I provide a usable deployed index, such as a baked read-only index, and configure its path; I do not confuse vector-index storage with durable conversation storage. [PDF pp. 9, 11]
- [ ] **RAG-11 — If I choose Pinecone:** I use the current Pinecone SDK and LangChain `PineconeVectorStore` integration, pin dependencies, configure the index and API-key placeholders, and verify current account terms. I keep conversation persistence separate from the externally stored index. [PDF pp. 7–9; alternative_pinecone_pattern.md]
- [ ] **RAG-12 — Pinecone reference layout:** If I use the suggested layout, I implement the adapter in `src/rag/ingest.py` and `src/rag/retriever.py` while preserving orchestration, streaming, and evaluation behavior. [alternative_pinecone_pattern.md; reference guidance]

## My provider routing — 15%

- [ ] **ROUTE-01:** I wire and actually exercise at least two different LLM generation providers. Two models from one provider, NVIDIA-only hosted models, and an embedding provider do not satisfy this floor. [PDF pp. 2–3, 5–6, 15]
- [ ] **ROUTE-02:** I route on cost, capability, or a documented hybrid of both using meaningful query/task characteristics. [PDF pp. 2–3]
- [ ] **ROUTE-03:** I show the selected agent, provider/model, and rationale per turn in the UI or trace, making it clear why that provider was selected instead of another. [PDF pp. 3–4, 15]
- [ ] **ROUTE-04:** I demonstrate normal queries/tasks that route to different providers; I avoid a router that always selects the same provider or leaves its second provider unexercised. [PDF pp. 3, 15]
- [ ] **ROUTE-05:** I include an LLM routing table in `docs/architecture.md` showing the dimension driving each decision and each agent's provider/model. [PDF pp. 12–13]
- [ ] **ROUTE-06:** I verify exact deployable model IDs before submission and pin them in my source/configuration and `.env.example`; I do not assume the planning examples remain available. [PDF pp. 5–6]
- [ ] **ROUTE-07:** I choose providers I can access and document their current cost/access tradeoffs; I treat three providers as recommended, not mandatory. [PDF pp. 5–6]

## My live/current knowledge channel

- [ ] **LIVE-01:** I retrieve current information through at least one agent using Tavily Remote MCP or the qualifying externally updated domain alternative, separate from static-corpus RAG. [PDF pp. 3, 6–7]
- [ ] **LIVE-02 — If I choose Tavily:** I connect to `https://mcp.tavily.com/mcp/?tavilyApiKey=<placeholder>` using Streamable HTTP, placing the key in the query parameter rather than the request body. I use the hosted Remote MCP pattern without a local MCP server process or OAuth flow. [PDF pp. 6–7]
- [ ] **LIVE-03 — If I choose Tavily:** I obtain my own key, verify current student/free-plan availability and quotas, and expose the relevant search/extract tools to my agents through an appropriate MCP adapter. [PDF p. 7]
- [ ] **LIVE-04 — If I choose Vertex AI Search:** I demonstrate an externally updated, domain-specific source supplying current knowledge; I do not reuse only the fixed RAG corpus and call it live retrieval. [PDF pp. 3, 7; alternative_vertex_ai_search.md]
- [ ] **LIVE-05 — If I choose Vertex AI Search:** I enable the current Search/Discovery Engine APIs, provision/populate the qualifying datastore, configure project/location/datastore/engine identifiers, grant the service account the needed roles, and expose equivalent retrieval trace evidence. I verify current commands, IAM roles, API names, and prices. [alternative_vertex_ai_search.md]
- [ ] **LIVE-06:** I verify a deployed current-information query whose answer is absent from my static corpus. [PDF p. 12]

## My A2A or MCP sharing evidence — 10%

I choose one qualifying path below. My live-retrieval choice does not automatically satisfy this separate rubric criterion. [PDF p. 16]

- [ ] **SHARE-01:** I exercise my selected sharing/protocol path in the deployed application, with at least two participating agents and inspectable evidence. [PDF p. 16]
- [ ] **SHARE-02 — If I choose MCP:** I expose one or more MCP servers as tools accessible to at least two agents. [PDF p. 16]
- [ ] **SHARE-03 — If I choose MCP:** I demonstrate the **same MCP tool invoked by different agents in different contexts**, not merely one active MCP user or two configured tool lists. [PDF p. 16]
- [ ] **SHARE-04 — If I choose MCP:** I document my tool-sharing rationale in `docs/architecture.md`. [PDF p. 16]
- [ ] **SHARE-05 — If I choose A2A:** I demonstrate at least two distinct agents communicating through Agent Card discovery, protocol message/task exchange (`message/send` as named in the PDF), task lifecycle/status evidence, and SSE streaming/progress behavior. I verify the current specification and SDK rather than copying stale method names. [PDF p. 16; alternative_a2a_pattern.md]
- [ ] **SHARE-06 — If I choose A2A:** I expose inspectable A2A traffic in the trace log and document the architecture rationale; I do not present a generic HTTP endpoint with agent-themed JSON as A2A. [PDF p. 16; alternative_a2a_pattern.md]

## My frontend and streaming — 15%

- [ ] **UI-01:** I serve my chat frontend and its static assets from FastAPI alongside the API routes. [PDF pp. 1, 3–5]
- [ ] **UI-02:** I provide a single-page HTML/CSS/vanilla JavaScript interface, or the explicitly permitted HTMX alternative, without a frontend framework build step or `node_modules` in the container. [PDF pp. 4–5]
- [ ] **UI-03:** I provide a query input and a response area that renders real incremental SSE/token output before generation finishes. [PDF pp. 3–4, 15]
- [ ] **UI-04:** I use a streaming consumption method compatible with my HTTP method: for POST, `fetch()` with a streaming reader; for GET, a standards-compatible alternative such as `EventSource`. [PDF pp. 4, 10]
- [ ] **UI-05:** I show each turn's invoked agent, selected LLM provider, and routing reason visibly. [PDF pp. 4, 15]
- [ ] **UI-06:** I expose an understandable, inspectable trace showing orchestration state transitions. [PDF pp. 4, 15]
- [ ] **UI-07:** I render RAG citations linked to source document identifiers and preserve traceability to chunks. [PDF pp. 3–4, 15]
- [ ] **UI-08:** I connect my frontend to the deployed backend and verify it through the public URL. [PDF p. 15]
- [ ] **UI-09 — If I choose HTMX:** I bundle `htmx.min.js` in the static-assets folder, satisfy the same streaming/trace/citation requirements, and explain my choice in the README. [PDF p. 4]
- [ ] **UI-10 — My reference UI contract:** If I adopt the supplied frontend prompt, I POST `{query, session_id}` to `/api/chat`, consume `text/event-stream`, and parse `token`, `trace`, `citation`, `error`, and `done` events. [frontend_vibecode_prompt.md; reference guidance]
- [ ] **UI-11 — My reference UI presentation:** If I adopt that prompt, I provide separate trace/citation panels, distinguish `agent_route`, `llm_route`, `rag_retrieval`, and `mcp_tool_call` badges, disable submission during an active stream, and implement Reset. I keep the frontend inspectable and easy to run from FastAPI static files. [frontend_vibecode_prompt.md; reference guidance]

## My configuration, container, and deployment — 15%

- [ ] **CONFIG-01:** I pin every framework/dependency listed in `requirements.txt` with exact versions; I do not use `>=` or `~=` ranges. [PDF p. 5]
- [ ] **CONFIG-02:** I configure only the providers/services I actually use through environment variables and supply `.env.example` with placeholders and verified model IDs. [PDF pp. 6, 8–9]
- [ ] **CONFIG-03:** I exclude `.env` and working credentials from source control and submission; I keep deployed credentials outside source code. [PDF pp. 8–9, 11–12, 15]
- [ ] **CONFIG-04:** I document/configure my selected provider API keys/models/base URL where applicable, embedding model, vector-store location/index, live-retrieval service, GCP project/region/service, and conditional state backend. [PDF pp. 8–9]
- [ ] **DEPLOY-01:** I deploy to a publicly accessible Google Cloud Run URL that responds to arbitrary reasonable queries, not only rehearsed examples; I do not submit a localhost-only application. [PDF pp. 4, 12, 15–16]
- [ ] **DEPLOY-02:** I provide an authenticated gcloud setup, a billing-enabled GCP project, and the APIs needed by my selected services, including the reference Cloud Run, Cloud Build, and Artifact Registry baseline. [PDF p. 9]
- [ ] **DEPLOY-03:** I create a complete multi-stage Dockerfile using Python `3.13-slim`, a non-root runtime user, and uvicorn/FastAPI bound to `0.0.0.0` and Cloud Run's injected `PORT`. I implement the stated behavior rather than copying the illustrative hard-coded port or inaccessible dependency paths blindly. [PDF p. 10]
- [ ] **DEPLOY-04:** I include my app, orchestration, provider SDKs, frontend assets, and usable RAG index or external index connection in the deployed image/configuration. [PDF p. 4]
- [ ] **DEPLOY-05:** I configure an appropriate request timeout for long-running SSE streams and verify streaming on Cloud Run. [PDF p. 10]
- [ ] **DEPLOY-06:** I adapt deployment commands to my project, region, image, environment, and selected persistence/volume configuration. [PDF p. 11]
- [ ] **DEPLOY-07:** I choose memory, CPU, concurrency, and instance limits with state isolation, provider limits, and cost in mind. I treat 1 GiB, 1 CPU, concurrency 10, timeout 300 s, min 0/max 3 as reference starting values, not fixed grading requirements. [PDF p. 11]
- [ ] **DEPLOY-08:** I verify the public app loads and answers after a cold start without visible request failure. [PDF pp. 12, 15]
- [ ] **DEPLOY-09:** I run a deployed corpus-answerable query, a live-information query, and inspect their agent/provider/rationale traces. [PDF p. 12]
- [ ] **DEPLOY-10:** I document reproducible deployment commands that a TA can use against a fresh GCP project. [PDF p. 15]

## My conditional durable-state requirements

- [ ] **STATE-01:** I document my actual state model and avoid claiming persistence guarantees that my implementation does not provide. [PDF pp. 4, 10–11]
- [ ] **STATE-02 — If I claim durable multi-turn state:** I implement and document Firestore, GCS/GCSFuse, Cloud SQL, or an equivalent external durable store. Process memory or local container storage alone does not satisfy this requirement. [PDF pp. 10–11, 15–16]
- [ ] **STATE-03 — If I claim durable multi-turn state:** I prove state survives actual instance replacement/restart, rather than just consecutive requests to the same process, and account for scaling. [PDF pp. 4, 12]
- [ ] **STATE-04 — If I choose GCS/GCSFuse:** I configure `GCS_STATE_BUCKET`, `GCS_STATE_MOUNT`, a native Cloud Run volume mount, and service-identity bucket access; my application actually reads/writes its claimed state through the mount. [alternative_gcs_persistence.md]
- [ ] **STATE-05:** I distinguish local development SQLite/in-memory checkpointers from deployment durability, and distinguish my vector index from conversation checkpoints. [PDF p. 11]
- [ ] **STATE-06 — If I choose stateless/single-turn:** I explicitly document that scope and confirm that neither my UI nor my reports claim durable memory. I record the durable-store items as not applicable with that rationale. [PDF pp. 4, 11]

## My evaluation, latency, and cost evidence

- [ ] **EVAL-01:** I define and retain a fixed test-question set and the inputs/reference answers needed to reproduce my selected RAGAS metrics. [PDF pp. 3, 12, 15]
- [ ] **EVAL-02:** I run RAGAS and report concrete **faithfulness, answer relevance, context precision, and context recall** values in `docs/evaluation.md`; I do not substitute qualitative claims or another evaluator. [PDF pp. 3, 12, 15]
- [ ] **EVAL-03:** I provide a reproducible evaluation entry point. If I follow the supporting layout, I retain `src/eval/ragas_eval.py` as my canonical RAGAS path. [alternative_deepeval_pattern.md]
- [ ] **EVAL-04:** I report per-query wall-clock latency broken down into retrieval, LLM call, and total, plus time to first token (TTFT). [PDF pp. 12–13]
- [ ] **EVAL-05:** I separately measure cold-start and warm latency, present warm steady-state numbers as representative, and state the cold-start result separately. I do not present the PDF's approximately 20–25 s cold / 1.5–2 s warm TTFT examples as my own results or required targets. [PDF pp. 12–13]
- [ ] **EVAL-06:** I report per-query costs measured from actual API bills or estimated from token counts, identifying my estimation method. [PDF p. 13]
- [ ] **EVAL-07:** I compare the providers I actually route to, covering cost, latency, and answer quality using inspectable measurements. [PDF pp. 5, 13]
- [ ] **EVAL-08:** I record provider and exact model ID, available input/output token usage, and the current provider price used for each verification query or evaluation batch. [cost_analysis.md]
- [ ] **EVAL-09:** I account for ingestion embedding tokens/cost, Tavily usage/plan terms, Cloud Run compute, and material persistence costs. [cost_analysis.md]
- [ ] **EVAL-10:** I verify official provider pricing and service/account terms when budgeting and before publishing estimates, date-stamp my estimates, and distinguish eligible GCP credits from separately billed LLM usage. [PDF p. 6; cost_analysis.md]
- [ ] **EVAL-11 — If I add DeepEval:** I keep it separate from my mandatory RAGAS results, pin its version, and document evaluator-model costs; I replace RAGAS only if I obtain an explicit instructor change to the assignment contract. [alternative_deepeval_pattern.md]

## My additional testing and review requirements

I add the checks below to satisfy my requested engineering standard. These are my quality gates, not extra instructor-assigned rubric weights. I choose meaningful cases across the listed test types, retain actual results, and do not claim coverage from tests I have not executed. I keep all test fixtures, caches, temporary outputs, and evidence within Assignment 2.

- [ ] **TEST-01 — My smoke tests:** I verify imports, configuration validation, graph compilation, app startup, static asset delivery, an API query, and an SSE stream locally and in the container.
- [ ] **TEST-02 — My unit tests:** I test routing branches, state transitions, specialist tool permissions, prompt differences, chunking/metadata, retrieval adapters, citation mapping, SSE framing, and cost/latency calculations.
- [ ] **TEST-03 — My integration tests:** I verify ingestion → vector retrieval → prompt augmentation → cited generation, supervisor → workers → integrated answer, live tool calls, provider routing, and my selected sharing protocol.
- [ ] **TEST-04 — My happy-path tests:** I exercise every selected specialist, both or more generation providers, static RAG, live retrieval, and a cooperative multi-agent query.
- [ ] **TEST-05 — My black-box tests:** I submit unseen reasonable queries through the public UI/API and verify useful output, visible incremental streaming, routing explanations, trace inspection, and resolvable citations without relying on internal implementation knowledge.
- [ ] **TEST-06 — My white-box tests:** I inspect graph/task transitions, routing predicates, state updates, unique prompts/tools, error paths, and trace events; I verify that apparently separate agents/providers are genuinely exercised.
- [ ] **TEST-07 — My sandbox tests:** I isolate fake credentials, temporary indexes, test state, and mocked provider/tool responses for deterministic failure tests; I distinguish these results from real external-service verification.
- [ ] **TEST-08 — My failure tests:** I exercise worker exceptions, provider timeouts/rate limits, tool failures, malformed input, empty/no-match retrieval, invalid configuration, and unavailable dependencies; I check that failures are visible and do not collapse the whole workflow.
- [ ] **TEST-09 — My streaming tests:** I verify partial frames, split/multiple SSE events, UTF-8 boundaries, disconnects, error/done behavior, and incremental browser rendering; if I use the reference controls, I verify Reset and submit locking.
- [ ] **TEST-10 — My retrieval tests:** I check stable source/chunk IDs, embedding compatibility, configurable top-k, re-ingestion behavior, citation preservation through summarization, and answers unsupported by the corpus.
- [ ] **TEST-11 — My sharing tests:** I retain evidence of the same MCP tool invoked by two agents in different contexts, or complete qualifying A2A discovery/message/lifecycle/streaming evidence.
- [ ] **TEST-12 — My deployment tests:** I test cold and warm starts, a nondefault injected `PORT`, non-root file/dependency access, concurrent requests, session isolation where relevant, stream timeout behavior, and reasonable unrehearsed queries.
- [ ] **TEST-13 — My conditional persistence tests:** If I claim durable state, I test replacement/restart recovery and multiple sessions/instances; I do not use a same-process test as proof of durability.
- [ ] **TEST-14 — My security and boundary checks:** I check that source/archive/logs/traces do not reveal credentials, including Tavily URL query keys, and that my project/test tooling writes only within Assignment 2.
- [ ] **TEST-15 — My regression review:** I review each change against affected requirements, rerun relevant tests, and resolve failures before marking the associated items complete.
- [ ] **TEST-16 — My reproducibility review:** I verify setup, ingestion, evaluation, container startup, and documented deployment instructions from a clean project environment within this folder; I record actual commands, outcomes, and limitations.
- [ ] **TEST-17 — My evidence integrity:** I report measured results honestly, separate mocked/offline tests from live verification, and avoid fabricating evaluation scores, costs, personal learning, or successful deployments.

## My submission artifacts and final audit

- [ ] **SUBMIT-01:** I submit my live, public Cloud Run URL to Brightspace and verify it still handles arbitrary reasonable queries at submission time. [PDF p. 12]
- [ ] **SUBMIT-02:** I prepare a source-code ZIP including exact-pinned `requirements.txt` and placeholder `.env.example`, excluding `.env`, secrets, and generated vector-index artifacts where appropriate. I ensure excluded artifacts remain reproducible or available through my documented deployment/index setup. [PDF p. 12]
- [ ] **SUBMIT-03:** I write `docs/architecture.md` with an orchestration diagram (Mermaid or embedded image), agents/nodes, communication paths, relevant state schema, responsibilities/tool access, per-agent provider/model choices, and routing dimensions. [PDF pp. 12–14]
- [ ] **SUBMIT-04:** I include corpus source, chunking strategy, retrieval k, augmentation prompt template, selected sharing/protocol rationale, and conditional durable-state design in `docs/architecture.md`. [PDF pp. 12, 16]
- [ ] **SUBMIT-05:** I write `docs/evaluation.md` with the fixed question set, all four concrete RAGAS metrics, retrieval/LLM/total latency, TTFT, separate cold/warm results, per-query cost, and provider comparison. [PDF pp. 12–13]
- [ ] **SUBMIT-06:** I write a **200–300 word** `PROCESS_LOG.md` with exactly the four requested sections: AI tools used (including versions where known), development narrative (successes, failures, and blockers encountered), verification narrative (testing beyond simply running code), and what I learned that AI tools could not do for me. I base personal claims on my actual experience. [PDF p. 13]
- [ ] **SUBMIT-07:** I write `README.md` covering setup, local run instructions, deploy instructions, provider requirements, and current implementation-specific cost/access information, plus my HTMX choice if applicable. [PDF pp. 4, 13, 15]
- [ ] **SUBMIT-08:** I review the ZIP and all written deliverables for completeness, valid links, consistency with deployed behavior, first-person prose, and absence of secrets or unfinished-step lists outside this file.
- [ ] **SUBMIT-09:** I reconcile every applicable requirement against evidence, account explicitly for unselected alternatives, and audit all six rubric categories before submission. [PDF pp. 14–16]

## My academic-integrity obligations

- [ ] **INTEGRITY-01:** I keep my source, deployment, and written deliverables my own individual work; I limit classmate discussion to general concepts, framework choices, and patterns. [PDF p. 13]
- [ ] **INTEGRITY-02:** I do not share source code between students or use other students' prior-semester deliverables or instructor-only reference implementations as my submission. [PDF p. 13]
- [ ] **INTEGRITY-03:** I document AI assistance accurately and understand the system I submit; I use AI to help write/debug/refactor rather than to replace my understanding. [PDF p. 13]
- [ ] **INTEGRITY-04:** I provide normal technical documentation for frameworks/libraries and per-agent model/provider choices. I acknowledge that USC academic-integrity rules and sanctions apply. [PDF pp. 13–14]

## My initial document review

I read all seven supplied Markdown files and extracted/read all 16 pages of the assignment PDF. I mapped the six rubric weights to checklist sections, preserved conditional alternatives, and included the submission and integrity obligations. I have not implemented or executed the assignment application at this stage, so I have not marked implementation, evaluation, or deployment requirements complete.

My unresolved project choices are recorded in DEC-01 through DEC-08. I have my Assignment 1 baseline, confirmed book-companion scope, GitHub destination, provider-access preferences, and historical GCP deployment identifiers. I still need my exact corpus, verified model/service configuration, state design, upload-format limits, deadline, and spending ceiling before I can finalize the implementation.
