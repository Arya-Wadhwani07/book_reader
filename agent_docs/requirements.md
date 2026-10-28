# Assignment 2 Requirements

This checklist records the applicable requirements for my CSCI 599 Assignment 2 project. A checked item has implementation or review evidence; it is not a guarantee of a grade. My operating rules are in [agents.md](agents.md), architecture in [docs/architecture.md](../docs/architecture.md), and measurements in [docs/evaluation.md](../docs/evaluation.md).

The entries below are acceptance criteria for my implementation. Checked items have supporting evidence; unfinished actions remain explicit.

## Scope and selected approach

- I follow the [assignment description](../docs/Assignment_2_Description%20%281%29.pdf) and the seven unchanged files in `reference_docs/`.
- I selected LangGraph Supervisor, Research/Summary/Data specialists, Pinecone, Tavily Remote MCP, vanilla JavaScript, Firestore, and GCS client storage.
- I do not need the unselected Hierarchical, Codex-worktree, Code Agent, Chroma, Vertex AI Search, A2A, HTMX, GCSFuse, stateless, or optional DeepEval alternatives.
- I keep all local work inside Assignment 2, use its Python virtual environment, and follow the professor's required submission paths.
- I confirmed my deadline as **October 27, 2026, 11:59 PM Los Angeles / Pacific Time**.
- I keep paid usage within **$5 OpenAI** and **$2.50 Anthropic**, with shared reservations across ingestion, generation, evaluation, retries, and CI. I monitor other service quotas and cloud credits separately.

| Rubric area | Weight | Evidence |
| --- | ---: | --- |
| Orchestration | 25% | I use three distinct specialists, state-driven hops, inspectable traces, and worker-failure recovery. |
| RAG | 20% | I use LCEL/Pinecone over eight complete books and 864 chunks, original-source citations, and four RAGAS metrics. |
| LLM routing | 15% | I route real calls across OpenAI, NVIDIA, and Anthropic, with visible reasons and measured comparisons. |
| Frontend | 15% | I stream actual tokens and expose per-turn sources, agents, providers, and routing traces. |
| Deployment | 15% | I deploy tested containers to Cloud Run and verify live queries, cold/warm timing, and durable recovery. |
| Tool sharing | 10% | I verified Research and Data calling the same Tavily MCP tool in different contexts. |

## Orchestration and specialized agents — 25%

- [x] **ARCH-01:** Build a working multi-agent system that accepts a user query, delegates work, coordinates results, and completes an answer end to end. [PDF pp. 1–2, 14–15]
- [x] **ARCH-02:** Implement state/task-driven delegation with inspectable decisions, rather than cosmetic agents or fixed transitions pretending to be orchestration. [PDF pp. 2, 14]
- [x] **ARCH-03:** Handle a worker failure without crashing the whole graph or collapsing the complete workflow, and expose understandable failure evidence. [PDF p. 14]
- [x] **ARCH-04:** Document my nodes/agents, communication paths, relevant state schema, responsibilities, and tool access in `docs/architecture.md`. [PDF pp. 12, 14]
- [x] **ARCH-05 — If I choose LangGraph:** Compile and execute a LangGraph state graph with a clean Supervisor or Hierarchical pattern; my supervisor routes workers based on inspectable state fields. [PDF pp. 2, 14]
- [x] **ARCH-06 — If I choose Supervisor:** Implement a central supervisor that knows its workers, delegates to them, and receives their results. [PDF p. 2]
- [x] **AGENT-01:** Implement at least three specialized agents from Research, Code, Data, and Summary; I do not count my Router/Supervisor toward the three. [PDF pp. 1–2]
- [x] **AGENT-02:** Give every counted specialist a distinct system prompt and distinct tool access that produces genuinely different behavior. [PDF p. 2]
- [x] **AGENT-03 — If I select Research:** Implement web search plus RAG retrieval and grounded answers with citations. [PDF p. 1]
- [x] **AGENT-05 — If I select Data:** Implement structured data queries over SQLite, CSV, or a JSON document store. [PDF p. 1]
- [x] **AGENT-06 — If I select Summary:** Implement document summarization that preserves citations. [PDF p. 1]
- [x] **AGENT-07:** Exercise at least one specialist using RAG and at least one using live/current knowledge retrieval in my deployed system. [PDF pp. 1, 3]
- [x] **AGENT-08:** Document each agent's model/provider choice and demonstrate cooperation rather than merely exposing unrelated model calls. [PDF pp. 1, 13]

## RAG implementation — 20%

- [x] **RAG-01:** Select a corpus with genuine retrieval structure, such as research papers, course readings, technical documentation, or public organizational documentation; I avoid a five-file toy corpus. The PDF does not define an exact minimum document count. [PDF pp. 3, 15]
- [x] **RAG-02:** Implement the RAG pipeline with LangChain LCEL and document the corpus source and pipeline shape. [PDF pp. 4, 12]
- [x] **RAG-03:** Load source documents, chunk them using a documented strategy, and generate embeddings. [PDF pp. 3, 7–8]
- [x] **RAG-04:** Store chunks and embeddings in Pinecone or Chroma and preserve stable source/chunk metadata for citations. [PDF pp. 3, 7–8, 15]
- [x] **RAG-05:** Retrieve top-k chunks using vector similarity and document my chosen k; I do not substitute keyword search for embedding-based retrieval. [PDF pp. 3, 12, 15]
- [x] **RAG-06:** Inject retrieved chunks into my generation prompt and document the augmentation prompt template. [PDF pp. 3, 12]
- [x] **RAG-07:** Generate grounded answers whose citations link back to the actual retrieved source chunks and source document identifiers. [PDF pp. 3–4, 15]
- [x] **RAG-08:** Implement extraction/indexing/map stages, explicit errors, stable vector upserts, resumed map reuse, and retry leases. Chunk size/overlap are validated chunk_book parameters; k is a retriever parameter. Corpus migration explicitly invalidates older pipeline maps/vectors.
- [x] **RAG-09:** Use a verified embedding configuration consistently for ingestion and query retrieval, accounting for vector dimensions if I choose local `sentence-transformers` embeddings. [PDF p. 6]
- [x] **RAG-11:** Use pinned Pinecone SDK and LangChain PineconeVectorStore with text-embedding-3-small, 1536-dimensional cosine, and a separate Firestore conversation store. I verified the ready deployed index has 864 public vectors, reviewed official Starter terms on October 27, and enabled no paid upgrade.

## Provider routing — 15%

- [x] **ROUTE-01:** Wire and actually exercise at least two different LLM generation providers. Two models from one provider, NVIDIA-only hosted models, and an embedding provider do not satisfy this floor. [PDF pp. 2–3, 5–6, 15]
- [x] **ROUTE-02:** Route on cost, capability, or a documented hybrid of both using meaningful query/task characteristics. [PDF pp. 2–3]
- [x] **ROUTE-03:** Show the selected agent, provider/model, and rationale per turn in the UI or trace, making it clear why that provider was selected instead of another. [PDF pp. 3–4, 15]
- [x] **ROUTE-04:** Demonstrate normal queries/tasks that route to different providers; I avoid a router that always selects the same provider or leaves its second provider unexercised. [PDF pp. 3, 15]
- [x] **ROUTE-05:** Include an LLM routing table in `docs/architecture.md` showing the dimension driving each decision and each agent's provider/model. [PDF pp. 12–13]
- [x] **ROUTE-06:** Verify exact deployable model IDs before submission and pin them in my source/configuration and `.env.example`; I do not assume the planning examples remain available. [PDF pp. 5–6]
- [x] **ROUTE-07:** Choose providers I can access and document their current cost/access tradeoffs; I treat three providers as recommended, not mandatory. [PDF pp. 5–6]

## Live/current knowledge channel

- [x] **LIVE-01:** Retrieve current information through at least one agent using Tavily Remote MCP or the qualifying externally updated domain alternative, separate from static-corpus RAG. [PDF pp. 3, 6–7]
- [x] **LIVE-02 — If I choose Tavily:** Connect to `https://mcp.tavily.com/mcp/?tavilyApiKey=<placeholder>` using Streamable HTTP, placing the key in the query parameter rather than the request body. I use the hosted Remote MCP pattern without a local MCP server process or OAuth flow. [PDF pp. 6–7]
- [x] **LIVE-03 — If I choose Tavily:** Obtain my own key, verify current student/free-plan availability and quotas, and expose the relevant search/extract tools to my agents through an appropriate MCP adapter. [PDF p. 7]
- [x] **LIVE-06:** Verify a deployed current-information query whose answer is absent from my static corpus. [PDF p. 12]

## A2A or MCP sharing evidence — 10%

I use shared Tavily MCP calls as my protocol evidence, separately from the live-information requirement. [PDF p. 16]

- [x] **SHARE-01:** Exercise my selected sharing/protocol path in the deployed application, with at least two participating agents and inspectable evidence. [PDF p. 16]
- [x] **SHARE-02 — If I choose MCP:** Expose one or more MCP servers as tools accessible to at least two agents. [PDF p. 16]
- [x] **SHARE-03 — If I choose MCP:** Demonstrate the **same MCP tool invoked by different agents in different contexts**, not merely one active MCP user or two configured tool lists. [PDF p. 16]
- [x] **SHARE-04 — If I choose MCP:** Document my tool-sharing rationale in `docs/architecture.md`. [PDF p. 16]

## Frontend and streaming — 15%

- [x] **UI-01:** Serve my chat frontend and its static assets from FastAPI alongside the API routes. [PDF pp. 1, 3–5]
- [x] **UI-02:** Provide a single-page HTML/CSS/vanilla JavaScript interface, or the explicitly permitted HTMX alternative, without a frontend framework build step or `node_modules` in the container. [PDF pp. 4–5]
- [x] **UI-03:** Provide a query input and a response area that renders real incremental SSE/token output before generation finishes. [PDF pp. 3–4, 15]
- [x] **UI-04:** Use a streaming consumption method compatible with my HTTP method: for POST, `fetch()` with a streaming reader; for GET, a standards-compatible alternative such as `EventSource`. [PDF pp. 4, 10]
- [x] **UI-05:** Show each turn's invoked agent, selected LLM provider, and routing reason visibly. [PDF pp. 4, 15]
- [x] **UI-06:** Expose an understandable, inspectable trace showing orchestration state transitions. [PDF pp. 4, 15]
- [x] **UI-07:** Render RAG citations linked to source document identifiers and preserve traceability to chunks. [PDF pp. 3–4, 15]
- [x] **UI-08:** Connect my frontend to the deployed backend and verify it through the public URL. [PDF p. 15]
- [x] **UI-10 — reference UI contract:** If I adopt the supplied frontend prompt, I POST `{query, session_id}` to `/api/chat`, consume `text/event-stream`, and parse `token`, `trace`, `citation`, `error`, and `done` events. [frontend_vibecode_prompt.md; reference guidance]
- [x] **UI-11 — reference UI presentation:** If I adopt that prompt, I provide separate trace/citation panels, distinguish `agent_route`, `llm_route`, `rag_retrieval`, and `mcp_tool_call` badges, disable submission during an active stream, and implement Reset. I keep the frontend inspectable and easy to run from FastAPI static files. [frontend_vibecode_prompt.md; reference guidance]

## Configuration, container, and deployment — 15%

- [x] **CONFIG-01:** Pin every framework/dependency listed in `requirements.txt` with exact versions; I do not use `>=` or `~=` ranges. [PDF p. 5]
- [x] **CONFIG-02:** Configure only the providers/services I actually use through environment variables and supply `.env.example` with placeholders and verified model IDs. [PDF pp. 6, 8–9]
- [x] **CONFIG-03:** Exclude `.env` and working credentials from source control and submission; I keep deployed credentials outside source code. [PDF pp. 8–9, 11–12, 15]
- [x] **CONFIG-04:** Document/configure my selected provider API keys/models/base URL where applicable, embedding model, vector-store location/index, live-retrieval service, GCP project/region/service, and conditional state backend. [PDF pp. 8–9]
- [x] **DEPLOY-01:** Deploy to a publicly accessible Google Cloud Run URL that responds to arbitrary reasonable queries, not only rehearsed examples; I do not submit a localhost-only application. [PDF pp. 4, 12, 15–16]
- [x] **DEPLOY-02:** Provide an authenticated gcloud setup, a billing-enabled GCP project, and the APIs needed by my selected services, including the reference Cloud Run, Cloud Build, and Artifact Registry baseline. [PDF p. 9]
- [x] **DEPLOY-03:** Create a complete multi-stage Dockerfile using Python `3.13-slim`, a non-root runtime user, and uvicorn/FastAPI bound to `0.0.0.0` and Cloud Run's injected `PORT`. I implement the stated behavior rather than copying the illustrative hard-coded port or inaccessible dependency paths blindly. [PDF p. 10]
- [x] **DEPLOY-04:** Include my app, orchestration, provider SDKs, frontend assets, and usable RAG index or external index connection in the deployed image/configuration. [PDF p. 4]
- [x] **DEPLOY-05:** Configure an appropriate request timeout for long-running SSE streams and verify streaming on Cloud Run. [PDF p. 10]
- [x] **DEPLOY-06:** Adapt deployment commands to my project, region, image, environment, and selected persistence/volume configuration. [PDF p. 11]
- [x] **DEPLOY-07:** Use web 1 CPU/1 GiB/concurrency 16/min 0/max 2 and ingestion 1 CPU/2 GiB/one-hour deadline. I selected concurrency 16 after reproducing and fixing 429s in the 120-read stress run.
- [x] **DEPLOY-08:** Measured idle first-hit bootstrap and a successful streamed answer, followed by a warm comparison; docs/evaluation.md distinguishes end-to-end latency from pure container-start time.
- [x] **DEPLOY-09:** Run a deployed corpus-answerable query, a live-information query, and inspect their agent/provider/rationale traces. [PDF p. 12]
- [x] **DEPLOY-10:** Document fresh-project prerequisites, local isolated setup, provisioning, image build, corpus migration, initial deployment, and OIDC CI configuration in README.md.

## Conditional durable-state requirements

- [x] **STATE-01:** Document my actual state model and avoid claiming persistence guarantees that my implementation does not provide. [PDF pp. 4, 10–11]
- [x] **STATE-02 — If I claim durable multi-turn state:** Implement and document Firestore, GCS/GCSFuse, Cloud SQL, or an equivalent external durable store. Process memory or local container storage alone does not satisfy this requirement. [PDF pp. 10–11, 15–16]
- [x] **STATE-03 — If I claim durable multi-turn state:** Prove state survives actual instance replacement/restart, rather than just consecutive requests to the same process, and account for scaling. [PDF pp. 4, 12]
- [x] **STATE-05:** Distinguish local development SQLite/in-memory checkpointers from deployment durability, and distinguish my vector index from conversation checkpoints. [PDF p. 11]

## Evaluation, latency, and cost evidence

- [x] **EVAL-01:** Define and retain a fixed test-question set and the inputs/reference answers needed to reproduce my selected RAGAS metrics. [PDF pp. 3, 12, 15]
- [x] **EVAL-02:** Run RAGAS and report concrete **faithfulness, answer relevance, context precision, and context recall** values in `docs/evaluation.md`; I do not substitute qualitative claims or another evaluator. [PDF pp. 3, 12, 15]
- [x] **EVAL-03:** Provide a reproducible evaluation entry point. If I follow the supporting layout, I retain `src/eval/ragas_eval.py` as my canonical RAGAS path. [alternative_deepeval_pattern.md]
- [x] **EVAL-04:** Report per-query wall-clock latency broken down into retrieval, LLM call, and total, plus time to first token (TTFT). [PDF pp. 12–13]
- [x] **EVAL-05:** Separately measure cold-start and warm latency, present warm steady-state numbers as representative, and state the cold-start result separately. I do not present the PDF's approximately 20–25 s cold / 1.5–2 s warm TTFT examples as my own results or required targets. [PDF pp. 12–13]
- [x] **EVAL-06:** Report per-query costs measured from actual API bills or estimated from token counts, identifying my estimation method. [PDF p. 13]
- [x] **EVAL-07:** Compare the providers I actually route to, covering cost, latency, and answer quality using inspectable measurements. [PDF pp. 5, 13]
- [x] **EVAL-08:** Record provider and exact model ID, available input/output token usage, and the current provider price used for each verification query or evaluation batch. [cost_analysis.md]
- [x] **EVAL-09:** Report token-based paid usage and separately account for Tavily credits, compute, storage, operations, builds, and transfer with dated official pricing references in docs/evaluation.md. I do not invent an infrastructure invoice or remaining credit balance.
- [x] **EVAL-10:** Retain verified model prices and October 27 official Cloud Run/Firestore/GCS/Pinecone/Tavily pricing references. I distinguish published plans, my confirmed access, measured token usage, and unobserved bills.

## Book companion features

- [x] **BOOK-01:** Support both fiction and nonfiction and adapt the analysis to the book: story/characters for fiction, and arguments, concepts, evidence, real people, or historical events when applicable to nonfiction. I do not invent a fictional plot for a nonfiction book.
- [x] **BOOK-02:** Provide a substantial curated library with documented sources and a reproducible ingestion path for grading.
- [x] **BOOK-03:** Support user uploads with validated formats and size limits, clear extraction/ingestion errors and progress, and isolation between uploaded books/users. I accept English PDF, EPUB, and TXT initially; I enforce the confirmed upload policy under SESSION-04, including a 500-page PDF cap, word-based EPUB/TXT cap, and displayed size/token limits.
- [x] **BOOK-04:** Provide selectable summary depth, chapter-level expansion, and whole-book synthesis with source citations and measured coverage rather than a lossless-summary promise.
- [x] **BOOK-05:** Provide character sketches and deep dives into relationships, motivations, and development, grounded in the text; I label interpretation and uncertainty.
- [x] **BOOK-06:** Provide major-event deep dives, chronology, causes, and consequences, retaining references to supporting passages.
- [x] **BOOK-07:** Include an about-the-author section with cited sources and a clear distinction between book content and externally researched biographical information.
- [x] **BOOK-08:** Research related film/TV adaptations through live web search, distinguish actual adaptations from loosely related works, and avoid asserting a match without source evidence.
- [x] **BOOK-09:** Find source-backed purchase links, including hardcover options when available, and distinguish editions/formats and current availability without inventing prices or links. I only link to vendors; I do not purchase anything.
- [x] **BOOK-10:** Label book passages and web sources separately, preserve depth/spoiler scope, and test shared web tools with whole-book permission and their absence under chapter scope.

## Anonymous chats and upload limits

- [x] **SESSION-01 — design decision:** Define one anonymous browser owner with multiple isolated chats, no login/logout, and persistent same-chat memory. I distinguish server-derived `owner_id`, chat `session_id`, and request `turn_id` consistently in my guidelines, architecture, and design.
- [x] **SESSION-02 — durable behavior:** Implement chat list/create/select/delete, restore messages and book/preferences after refresh, and prove recovery after Cloud Run instance replacement. I keep graph checkpoints scoped to the authorized owner/chat pair, prevent cross-chat context leakage, and deduplicate retried turns.
- [x] **SESSION-03:** Preserve previous chats and books when starting a new chat. I require Stop before switching context while streaming and disable context controls during generation. I browser-tested Stop, saved cancelled status, refresh, separate tabs selecting different books, and the deletion confirmation; I cancelled rather than deleting user data. API tests verify deletion and loss-of-identity/other-owner isolation.
- [x] **SESSION-04 — upload design:** Set the initial limit to 25 MB (25,000,000 bytes) per file, at most 500 actual PDF pages, or at most 125,000 extracted words for EPUB/TXT (approximately 500 pages at 250 words/page), plus at most 250,000 extracted tokens for every format. I display every applicable limit before upload and never silently truncate a book. These engineering limits are selected to support the requested 300–400-page target; I subsequently verified substantial 300/400/500-page parsing fixtures and the 115,831-word Walden corpus; I do not claim every PDF layout is supported.
- [x] **SESSION-05:** Passed real-tokenizer tests on the 115,831-word Walden source and 300/400/500-page generated PDFs containing 60,000/80,000/100,000 words from it, plus 501-page rejection, exact admission boundaries, encryption, malformed files, and EPUB expansion/entity rejection. These are substantial controlled fixtures, not proof of every PDF layout.
- [x] **SESSION-06 — contract alignment:** Align backend/client/live-test requests with `{query, session_id, turn_id, book_id, depth, spoiler_limit}`, server-side owner authorization, and chat/source/cancellation endpoints. The added fields extend the professor's example request rather than changing the mandated POST/SSE behavior.

## Engineering and release checks

- [x] **WORK-REVIEW:** Reviewed imports, module consumers, executable scripts, static assets, and dependencies. Ruff and formatting checks passed; I found no unused imports or orphaned source files in that review.
- [x] **TEST-OFFLINE:** Passed 171 Python tests and 98 JavaScript tests with no failures, errors, or skips. I isolate offline state, credentials, network access, and temporary files inside the project.
- [x] **TEST-FAILURES:** Cover invalid input, worker/provider failures, truncation, stream framing, silent cancellation, ownership, duplicate turns, expired leases, storage failure, and ingestion retry/idempotency.
- [x] **TEST-LONG-BOOKS:** Checked real-tokenizer Walden chunks and substantial 300/400/500-page PDF fixtures, plus over-limit, malformed, encrypted, and unsafe EPUB inputs.
- [x] **TEST-LIVE:** Verified PDF/EPUB/TXT ingestion, source isolation, multi-provider answers, shared MCP tools, unrehearsed fiction/nonfiction questions, off-topic redirects, and exact saved-answer recovery through another revision.
- [x] **TEST-STRESS:** Retained the initial 429 failures, adjusted concurrency, and passed the final 120-read/12-worker run. I keep fixture stress tests separate from measured cloud results.
- [x] **CICD:** Run Python 3.13 checks, JavaScript tests, and a non-root container check before deployment. I use repository/main-scoped OIDC and Secret Manager, deploy the tested image digest and matching ingestion job, verify the candidate, promote it, and verify the public URL. I configure traffic/job-image rollback; I have not forced a production rollback drill.
- [x] **DOC-REVIEW:** Checked Markdown links, required paths, first-person wording, sample queries, corpus reproducibility, and the four-section process log containing my personal reflection. I preserve instructor references unchanged.
- [x] **PACKAGE:** Build the source ZIP from tracked files, check required contents and archive integrity, and scan its contents—including the expanded corpus snapshot—for configured secrets. I exclude environments, private state, caches, credentials, and generated vector binaries.

- [x] **TEST-CITATIONS:** Added three regression cases for fabricated, other-owner, and nonexistent chunk IDs. I strengthened live checks to compare answer citations with authorized source cards and retained the failed qualitative review in evaluation evidence.
- [x] **RELEASE-CITATIONS:** Revised prompts and source-ID validation passed nine candidate and nine public CI checks. I reviewed the three added book answers, retained their evidence and the remaining retrieval/grounding limitations, and refreshed the submission ZIP.

- [x] **MANUAL-DIAGRAM:** Rendered and visually inspected all four Mermaid diagrams. I changed the compressed horizontal RAG diagram to a readable vertical flow and verified all four SVGs rendered without errors.

## Evidence and verification limits

My full measurements are in [evaluation_results.json](../docs/evaluation_results.json). My citation-validated application passed [CI run 40627570217](https://github.com/Arya-Wadhwani07/book_reader/actions/runs/40627570217) at commit `b1ec3e5`: nine candidate and nine public tests, with no failures or skips. The expanded nine-question evaluation uses that same application revision. Later documentation and evaluation-data updates do not change application behavior; each push starts a new CI/CD run.

My expanded RAGAS means are faithfulness **0.8719**, answer relevance **0.7665**, context precision **0.5920**, and context recall **0.8889**. These cover nine fixed questions across all eight books and 36 completed metric calculations. I retain the earlier results and the new retrieval/grounding weaknesses, rather than presenting the strongest run as universal performance.

My browser checks covered streaming, original passages, traces, refresh, Stop, separate chats/tabs, keyboard focus, responsive widths, and selected text contrast. I retain these additional manual checks as unverified rather than claiming complete browser/accessibility coverage:

- [ ] **MANUAL-A11Y:** Verify actual 200% browser zoom, screen-reader announcements, and reduced-motion interaction. Native Chrome access was rejected during the final review; I did not bypass that restriction. Responsive-width and semantic-markup checks do not replace those observations.
- [ ] **MANUAL-UPLOAD:** Verify the browser file picker and private-upload retry/category controls. I kept existing file permissions as requested; API and unit checks already cover formats, retries, and category ownership.

I do not treat these unexecuted observations as missing application features or as passing tests. I also do not claim exhaustive model correctness, a measured final infrastructure invoice, or a verified remaining cloud-credit balance.

## Submission

- [ ] **SUBMIT-01:** Submit my live, public Cloud Run URL to Brightspace and verify it still handles arbitrary reasonable queries at submission time. [PDF p. 12]
- [x] **SUBMIT-02:** Prepare a source-code ZIP including exact-pinned `requirements.txt` and placeholder `.env.example`, excluding `.env`, secrets, and generated vector-index artifacts where appropriate. I ensure excluded artifacts remain reproducible or available through my documented deployment/index setup. [PDF p. 12]
- [x] **SUBMIT-03:** Write `docs/architecture.md` with an orchestration diagram (Mermaid or embedded image), agents/nodes, communication paths, relevant state schema, responsibilities/tool access, per-agent provider/model choices, and routing dimensions. [PDF pp. 12–14]
- [x] **SUBMIT-04:** Include corpus source, chunking strategy, retrieval k, augmentation prompt template, selected sharing/protocol rationale, and conditional durable-state design in `docs/architecture.md`. [PDF pp. 12, 16]
- [x] **SUBMIT-05:** Write `docs/evaluation.md` with the fixed question set, all four concrete RAGAS metrics, retrieval/LLM/total latency, TTFT, separate cold/warm results, per-query cost, and provider comparison. [PDF pp. 12–13]
- [x] **SUBMIT-06:** Write a **200–300 word** `PROCESS_LOG.md` with exactly the four requested sections: AI tools used (including versions where known), development narrative (successes, failures, and blockers encountered), verification narrative (testing beyond simply running code), and what I learned that AI tools could not do for me. I base personal claims on my actual experience. [PDF p. 13]
- [x] **SUBMIT-07:** Write `README.md` covering setup, local run instructions, deploy instructions, provider requirements, and current implementation-specific cost/access information, plus my HTMX choice if applicable. [PDF pp. 4, 13, 15]
- [x] **SUBMIT-08:** Review the ZIP and all written deliverables for completeness, valid links, consistency with deployed behavior, first-person prose, and absence of secrets or unfinished-step lists outside this file.
- [x] **SUBMIT-09:** Reconcile every applicable requirement against evidence, account explicitly for unselected alternatives, and audit all six rubric categories before submission. [PDF pp. 14–16]

My Brightspace submission consists of one URL in the comments—**https://book-companion-a6lyssed7q-uw.a.run.app**—and five files: the source ZIP, `docs/architecture.md`, `docs/evaluation.md`, `PROCESS_LOG.md`, and `README.md`. The local package is `reports/book_companion_source_draft.zip`; I retain the draft label while manual verification limits and the actual hand-in remain open.

My two-pass submission review checks document content against the required sections, then verifies the packaged copies against the working files. Architecture includes the exact Research augmentation prompt, typed graph state, and the implemented deep-mode routing rule; evaluation includes exact model IDs and the token-cost calculation.

## Academic integrity

- [x] **INTEGRITY-01:** Confirmed in conversation on October 27 that I followed the individual-work rules.
- [x] **INTEGRITY-02:** Confirmed in conversation on October 27 that I followed the no-source-sharing rules.
- [x] **INTEGRITY-03:** Document AI assistance accurately and understand the system I submit; I use AI to help write/debug/refactor rather than to replace my understanding. [PDF p. 13]
- [x] **INTEGRITY-04:** Document frameworks and per-agent provider/model choices in README and architecture, and retain the supplied USC integrity rules as my submission obligations. I confirmed following the course rules in conversation.

## Answer-formatting review

- [x] **UI-MARKDOWN:** Render supported Markdown during streaming and when restoring saved chats; retain source links and reject executable HTML/unsafe URL schemes. Eight new automated cases and a real-browser fixture check cover the reported formatting bug.
- [x] **UI-MODELS:** Show deduplicated provider/model badges and expandable exact model IDs, tasks, agents, and routing reasons. Keep full trace data available.
