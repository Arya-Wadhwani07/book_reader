# My Book Companion Architecture

I use one LangGraph supervisor and three specialists. I serve a vanilla browser client from FastAPI and stream actual answer tokens, citations, and execution traces. I keep acceptance evidence and unfinished work exclusively in [my requirements](../agent_docs/requirements.md).

## My agent topology

```mermaid
flowchart TD
    Q[Reader question and book scope] --> S[Supervisor: classify and plan]
    S --> R[Research]
    S --> M[Summary]
    S --> D[Data]
    R --> S
    M --> S
    D --> S
    S --> F[Synthesis supervisor]
    F --> O[SSE answer and sources]
```

| My node | My prompt and tools |
| --- | --- |
| Supervisor | I classify the request into relevant workers through structured model output and inspect `plan`/`completed` state. |
| Research | I answer from a LangChain LCEL semantic retriever and original passages; I use Tavily for author/adaptation research. |
| Summary | I read ordered chapter evidence maps, reduce large collections, preserve chronology, and retain original chunk references. |
| Data | I query structured JSON records for characters, concepts, and events; I use Tavily for editions and purchase sources. |
| Synthesis | I combine successful worker results, retain citations, disclose failed workers, and stream the final answer. |

I give each specialist a separate system prompt and a different tool surface. My supervisor does not count toward the three-specialist requirement. Each worker returns to the supervisor; a failed worker records a structured failure, and successful workers can still contribute. If every selected worker fails, I return an incomplete response.

## My provider routing

| My task | My normal provider/model | My rationale |
| --- | --- | --- |
| Planning and evidence extraction | OpenAI `gpt-6-luna` | I use low-cost, schema-constrained output for bounded structured work. |
| Brief/detailed evidence-based responses | NVIDIA `nvidia/nemotron-3-ultra-550b-a55b` | I use my confirmed student access for ordinary generation. |
| Deep cross-section synthesis | Anthropic `claude-sonnet-5` | I use the selected Sonnet model for detailed interpretation. |
| Embeddings | OpenAI `text-embedding-3-small`, 1,536 dimensions | I use one compatible embedding space for indexing and queries; this does not count as a generation provider. |

I route by task and requested depth. I emit provider, exact model, task, and reason in `llm_route` events. I select another configured provider when the preferred provider is unconfigured. If a configured provider fails before publishing text, I attempt at most one alternative with a visible recovery reason and a separate budget reservation. I can discard an unpublished, incomplete specialist draft before that fallback. I never mix providers after final-answer text starts, and I treat provider-reported output truncation as an incomplete response.

I reserve a conservative cost bound before each OpenAI/Anthropic call. I settle actual token costs when available and retain the reservation when billing is uncertain. My separate limits are $5 OpenAI and $2.50 Anthropic. I record embedding costs as conservative byte-token estimates. My cloud ledger is shared across workers and instances.

## My ingestion and RAG

```mermaid
flowchart LR
    B[Eight public-domain books or private upload] --> V[Format, size, language and extraction checks]
    V --> A[(Original and chunk artifacts)]
    A --> C[Chapter or section chunks: 800 tokens, overlap 120]
    C --> E[Budgeted OpenAI embeddings]
    E --> P[(Pinecone)]
    C --> X[Structured evidence extraction]
    X --> J[(Chapter summaries and JSON facts)]
    P --> READY[Publish ready status]
    J --> READY
    READY --> RET[Top-6 semantic retrieval]
    RET --> AUG[LCEL evidence prompt]
    AUG --> GEN[Cited generation]
```

- I curate four fiction and four nonfiction books through the official Project Gutenberg mirror. I preserve original files and source URLs; my manifest is `corpus/manifest.json`.
- I accept English PDF/EPUB/TXT, at most 25 MB. I cap PDFs at 500 physical pages, EPUB/TXT at 125,000 words, and extracted input at 250,000 tokens.
- I reject encrypted or unreadable input, unsafe EPUB paths, and excessive expanded EPUB size. I use deterministic language detection before paid processing.
- I assign stable book/section/token-offset chunk identifiers and preserve PDF page locations. A text without recognized headings is labelled `Full text` rather than given invented chapter boundaries.
- I exclude a repeated heading-only contents list from narrative chapter numbering. I keep the original document separately.
- I embed and store chunks in a namespace belonging to the owner, or `public` for my curated library. I filter semantic retrieval by authorized book and spoiler boundary.
- I use `RunnableLambda(retrieve) | PromptTemplate | RunnableLambda(generate)` for Research's retrieve–augment–generate chain.
- I augment with `[chunk_id] original passage` blocks and require original source IDs in factual answers. I treat evidence as data, never as instructions.
- I map every chunk into a bounded structured extraction group. Summary reads all evidence maps within scope, rather than treating top-k retrieval as a whole-book summary.
- I query stored character/event/concept JSON records in Data. I order records numerically by section and token offset.
- I preserve validated extracted JSON and record the size of any discarded model continuation. I never discard original book text to repair model output.

## My memory and runtime

```mermaid
flowchart LR
    U[Browser: signed anonymous cookie] --> API[FastAPI]
    API --> CHAT[(Firestore: owner-scoped chats and turns)]
    API --> GRAPH[LangGraph]
    GRAPH --> CP[(Firestore: checkpoints and pending writes)]
    GRAPH --> P[(Pinecone: authorized vectors)]
    GRAPH --> G[(GCS: original passages)]
    API --> JOB[Cloud Run ingestion job]
    JOB --> G
    JOB --> P
    JOB --> FACT[(Firestore: facts and readiness)]
```

| My state group | My actual fields |
| --- | --- |
| Identity | `owner_id`, `session_id`, `book_id` |
| Request | `query`, `depth`, `spoiler_limit`, bounded `history` |
| Execution | `plan`, `completed`, `initialized` |
| Results | `results`, `errors`, `citations`, `answer` |

I derive ownership from a signed HttpOnly cookie; a caller-supplied chat ID is not authorization. I isolate multiple chats, preserve them when creating a new chat, and require explicit deletion. I filter incomplete turns and exclude prior answers outside a reduced spoiler boundary from model history.

I atomically reserve a chat and its turn, reject duplicate IDs and concurrent turns, and persist successful completion before emitting success. I persist LangGraph checkpoints and intermediate writes through a shared storage adapter. Local development uses SQLite; Cloud Run uses application-prefixed Firestore collections and GCS artifacts. I do not mix conversation checkpoints with Pinecone's book index.

I use a separate Cloud Run Job for cloud ingestion. I use a tracked asynchronous task locally. My artifact/checkpoint adapters and ready-state records separate long-running ingestion from reader requests.

## My complete workflow

```mermaid
flowchart TB
    USER[Reader] --> UI[Vanilla HTML/CSS/JS]
    UI --> API[FastAPI: signed ownership and admission]
    API --> ING[Ingestion job]
    ING --> KNOW[(GCS / Pinecone / Firestore facts)]
    API --> SUP[LangGraph Supervisor]
    SUP --> TEAM[Research / Summary / Data]
    TEAM <--> KNOW
    TEAM --> ROUTE[Task and depth router]
    ROUTE --> O[OpenAI]
    ROUTE --> N[NVIDIA]
    ROUTE --> A[Anthropic]
    TEAM --> MCP[Tavily Remote MCP search]
    MCP --> WEB[Author / adaptation / edition sources]
    WEB --> TEAM
    TEAM --> FINAL[Cited synthesis]
    FINAL -->|SSE| UI
    SUP <--> MEMORY[(Firestore checkpoints and conversations)]
    ROUTE <--> BUDGET[(Transactional spending ledger)]
    GH[GitHub main] --> CI[Offline tests and container verification]
    CI --> CAND[Candidate image digest]
    CAND --> LIVE[Live acceptance]
    LIVE --> RUN[Cloud Run public service]
    RUN --> API
```

I expose the same `tavily_search` MCP tool to Research and Data through Streamable HTTP. Research searches author/adaptation sources; Data searches editions and retailers. I record distinct agent/query contexts in tool traces. I suppress Research web expansion under a chapter spoiler boundary; I do not present retailer availability as guaranteed.

I render model text safely and link original source passages. I parse arbitrary UTF-8/network frame boundaries, reject malformed or incomplete streams, disable overlapping submission, and preserve per-turn traces. My UI offers overview, chapter, character/concept, event/argument, author, adaptation, and purchase-question entry points.

My container uses a multistage Python 3.13-slim build, `/app/.venv`, a non-root user, and Cloud Run's `PORT`. My workflow uses repository/main-scoped OIDC, Secret Manager, a tested image passed between jobs, candidate checks, promotion, public checks, and traffic rollback after a failed post-promotion check.

## My practical limits

I cannot preserve every detail in a compressed summary. I keep original source passages inspectable and distinguish interpretation from evidence. Language detection is probabilistic, PDF pages are not necessarily chapters, and files without explicit headings provide coarse spoiler boundaries. I report failed processing rather than publishing a partially indexed book as ready. I distinguish synthetic tests, actual external-service execution, and measured live deployment evidence in my requirements and evaluation report.
