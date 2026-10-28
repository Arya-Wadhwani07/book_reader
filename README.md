# Book Companion

I built this book companion for CSCI 599 Assignment 2 with help from OpenAI Codex. My aim was to make long books easier to explore: start with a summary, then follow up on a character, event, argument, or passage without losing the source. I included eight public-domain fiction and nonfiction books, plus private English PDF, EPUB, and TXT uploads.

I used a LangGraph supervisor to coordinate Research, Summary, and Data agents. Pinecone handles book retrieval, Tavily Remote MCP provides web research, and FastAPI serves the reading interface.

I deployed the application at **https://book-companion-a6lyssed7q-uw.a.run.app**. My measured results, including slower responses and imperfect retrieval scores, are in [docs/evaluation.md](docs/evaluation.md).

I explain the system in [architecture.md](docs/architecture.md), the interface in [design.md](agent_docs/design.md), and requirement-by-requirement status in [requirements.md](agent_docs/requirements.md).

## Sample queries

I select a ready book and set the spoiler scope before asking a question. These examples cover passage retrieval, nonfiction analysis, and web research:

| Book and settings | Sample query |
| --- | --- |
| Alice's Adventures in Wonderland · Brief · Chapter 1 | Why does Alice follow the White Rabbit? Use original passages and avoid spoilers beyond chapter 1. |
| The Art of War · Detailed · Chapter 1 | Explain the five constant factors in chapter 1. How do they relate to planning, and which passages support the explanation? |
| Alice's Adventures in Wonderland · Detailed · Whole book | Tell me about Lewis Carroll, find a film adaptation of this book, and look for a hardcover edition to buy. Cite the web sources and distinguish confirmed details from uncertain matches. |

I open **Source** to read an original passage and **Activity** to inspect agent, provider, and tool decisions. Web research needs whole-book scope because external pages may reveal later events. I can also ask follow-up questions or start a separate saved chat.

## Local setup

I run these commands from the repository root. I use Python 3.13 for my container/CI and keep my Python environment, caches, test data, and reports inside this folder.

```sh
python3.13 -m venv .venv
mkdir -p .cache/tmp .cache/pip reports
export TMPDIR="$PWD/.cache/tmp"
export PIP_CACHE_DIR="$PWD/.cache/pip"
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m pip install -r requirements.txt -r requirements-ci.txt
cp .env.example .env
```

I fill `.env` locally and never commit it. My setup needs:

- A random session secret of at least 32 characters.
- Funded OpenAI access for embeddings and planning: `text-embedding-3-small` and `gpt-6-luna`.
- NVIDIA student access for ordinary responses: `nvidia/nemotron-3-ultra-550b-a55b`.
- Anthropic access for deep responses: `claude-sonnet-5`.
- Tavily Remote MCP access and a 1,536-dimensional cosine Pinecone index.

I create the `book-companion` dense cosine index in my Pinecone account with 1,536 dimensions (my Starter deployment uses serverless AWS `us-east-1`) before ingestion. I set `PINECONE_INDEX` if I choose another name.

```sh
.venv/bin/python -m scripts.prepare_library
.venv/bin/python -m uvicorn src.app:create_app --factory --host 127.0.0.1 --port 8080
```

I open `http://127.0.0.1:8080`. I select a ready book, choose a spoiler boundary and depth, and ask a question. I can maintain separate saved chats in the same browser without an account. Clearing the browser identity removes access to those chats; I do not promise cross-device recovery.

## Books, uploads, and saved chats

I use eight complete public-domain books from a Project Gutenberg mirror. I list titles and editions in [corpus/manifest.json](corpus/manifest.json).

- **Uploads:** I accept English, text-based PDF/EPUB/TXT files up to 25 MB. I cap PDFs at 500 pages, EPUB/TXT at 125,000 words, and all extracted input at 250,000 tokens. I reject encrypted, scanned-only, unreadable, or unsupported-language files.
- **Recovery:** I preserve completed chats after refresh. If a process disappears, I mark its expired 330-second turn lease interrupted rather than complete. Stop can cancel silent generation without waiting for another token.
- **Private books:** I provide Retry after failed processing and a category selector to correct fiction/nonfiction classification.
- **Scope:** I redirect unrelated requests to book questions, with an explicit off-topic/no-worker trace. I keep book-related creative questions and follow-ups in scope.
- **Admission:** I allow 30 chat attempts per owner and 600 across the service per hour; uploads/retries allow 3 per owner and 24 service-wide. Clearing the anonymous cookie changes identity, so these limits are not a substitute for authenticated abuse prevention.

### Rebuilding the curated library

I include the exact **October 27, 2026, pipeline-2** snapshot in `corpus/snapshot.json.gz`. It contains:

- Eight original books with Gutenberg licenses and source URLs.
- All 864 chunks and structured evidence maps.
- Edition timestamps and SHA-256 checksums exported from deployed storage.

I omit private uploads, conversations, credentials, and Pinecone vector binaries. My preparation script verifies and uses the pinned originals; without the snapshot, it downloads mirror files that may have changed.

I estimate **10–30 minutes** for a fresh eight-book embedding/extraction rebuild. This is a planning estimate, not a measured clean-rebuild duration. The included snapshot avoids downloading the books, but regeneration still needs API access and can produce different chapter summaries. I preserve deployed maps for comparison and do not overwrite a populated index or spending ledger.

## Tests and evaluation

```sh
TIKTOKEN_CACHE_DIR="$PWD/.cache/tiktoken" .venv/bin/python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest tests --ignore=tests/live --junitxml=reports/offline.xml
.venv/bin/python scripts/verify_release.py report reports/offline.xml
node --test tests/test_stream.cjs
```

I use Node only for tests of my vanilla stream parser, with no frontend framework, package installation, or Node runtime in my container. My offline Python suite uses project-local temporary storage, blocked external socket connections, and outside-write guards. I test real service calls separately:

```sh
BASE_URL="https://MY_CLOUD_RUN_URL" .venv/bin/python -m pytest tests/live --junitxml=reports/live.xml
.venv/bin/python scripts/verify_release.py report reports/live.xml
.venv/bin/python -m pip install -r requirements-eval.txt
.venv/bin/python -m src.eval.ragas_eval --url "https://MY_CLOUD_RUN_URL" --cloud
```

I define fixed evaluation questions and references in `src/eval/questions.json`. I use RAGAS faithfulness, answer relevance, context precision, and context recall. My evaluation calls share the same spending ledger as the cloud application. I distinguish fixture timings from real provider and Cloud Run measurements.

## Google Cloud deployment

I use a billing-enabled project with eligible credits, authenticated Google Cloud CLI/application-default credentials, and owner-equivalent provisioning permissions. For a fresh project, I set its ID and region explicitly; my scripts create the application's dedicated resources without using Assignment 1 files.

```sh
export GCP_PROJECT_ID="MY_GCP_PROJECT"
export GCP_REGION="us-west1"
export CLOUDSDK_CONFIG="$PWD/.cache/gcloud"
export CLOUDSDK_PYTHON="$PWD/.venv/bin/python"
.cache/tools/google-cloud-sdk/bin/gcloud auth login --update-adc
.venv/bin/python -m scripts.cloud_setup
.cache/tools/google-cloud-sdk/bin/gcloud builds submit --project "$GCP_PROJECT_ID" \
  --tag "$GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/book-companion/book-companion:initial"
.venv/bin/python -m scripts.migrate_corpus
.venv/bin/python -m scripts.deploy_candidate
```

I install the official Google Cloud CLI under `.cache/tools/google-cloud-sdk` for this command layout. I create a separate private bucket, application-prefixed Firestore collections, Artifact Registry repository, runtime identity, secret versions, and ingestion job. I migrate the cumulative spending ledger once and stop paid local calls before switching to cloud execution. I never overwrite an existing cloud budget ledger.

For another repository/project, I update `REPOSITORY` in `scripts/github_setup.py` and the workflow’s `GCP_PROJECT_ID`/region before running its setup. I authenticate the project-local GitHub CLI as the repository owner. I configure repository/main-scoped GitHub Workload Identity Federation with `scripts.github_setup`. My workflow runs on pushes and pull requests and deploys only `main`. I pass the tested container between jobs, deploy its digest, run candidate acceptance, promote it, and test the public URL. A failed post-promotion check restores the previous revision's traffic. I store actual API keys in Secret Manager, not GitHub variables or source.

## Cost and access policy

I cap total project usage at **$5 OpenAI** and **$2.50 Anthropic**, with transactional reservations before paid requests. I verified the following standard rates on October 27, 2026:

| Model | Input per million tokens | Output per million tokens |
| --- | ---: | ---: |
| GPT-6 Luna | $0.10 | $0.50 |
| Claude Sonnet 5 | $2.00 | $10.00 |
| text-embedding-3-small | $0.02 | Not applicable |

I use NVIDIA/Tavily student access, Pinecone Starter, and my existing GCP credits. Those allowances do not cover OpenAI or Anthropic charges. I disabled automatic budget expansion: a paid request stops if the shared ledger cannot reserve its estimated maximum cost. Unknown charges remain conservatively reserved. I have not enabled paid plan upgrades or automatic top-ups.

For a rough per-run budget, I use my measured examples below. These are paid generation costs, not complete invoices; query embeddings, web searches, ingestion, and cloud resources are separate.

| Run I measured | Recorded paid generation | How I use the estimate |
| --- | ---: | --- |
| One brief cited answer, using NVIDIA student access | $0.000052–$0.000055 | About $0.005–$0.006 for 100 similar answers, mainly OpenAI planning; NVIDIA did not return billed usage. |
| One whole-book deep query using all three specialists | $0.15197 | Roughly $0.15 per comparable deep query; length, evidence size, and fallback calls can change the cost substantially. |

For embedding alone, I estimate about **$0.0114** to process my 570,802-token corpus once at $0.02 per million tokens, before overlap and request overhead. This is a lower-bound component estimate, not the price of a full rebuild: chapter extraction and later generation add cost. I include the measured traces in [evaluation_results.json](docs/evaluation_results.json).

I monitor usage before and after ingestion, evaluations, and repeated live tests:

- I compare the OpenAI Usage dashboard and Anthropic Console usage with the shared spending ledger.
- I check remaining Tavily credits and Pinecone usage separately.
- I use Google Cloud Billing reports and budget alerts to track compute, storage, and credit consumption.
- I pause paid testing if account totals or remaining credits no longer fit my budget.

I treat provider dashboards as the billing reference. My ledger limits this application, but it cannot account for unrelated activity on the same accounts.

I source these rates from [OpenAI's model catalog](https://developers.openai.com/api/docs/models/gpt-6-luna), [OpenAI embedding pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small), and [Anthropic's Sonnet 5 documentation](https://platform.claude.com/docs/en/models/sonnet-5/overview). I report actual usage evidence separately from listed prices.

I record my development and verification narrative in [PROCESS_LOG.md](PROCESS_LOG.md). I keep the current completion status in [my requirements checklist](agent_docs/requirements.md).
