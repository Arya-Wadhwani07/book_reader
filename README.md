# Book Companion

I built this book companion for CSCI 599 Assignment 2 with help from OpenAI Codex. My aim was to make long books easier to explore: start with a summary, then follow up on a character, event, argument, or passage without losing the source. I included eight public-domain fiction and nonfiction books, plus private English PDF, EPUB, and TXT uploads.

For the architecture, I chose a LangGraph supervisor coordinating Research, Summary, and Data agents. Pinecone handles book retrieval, Tavily Remote MCP provides web research, and FastAPI serves the reading interface.

My deployed application is available at **https://book-companion-a6lyssed7q-uw.a.run.app**. My measured results, including slower responses and imperfect retrieval scores, are in [docs/evaluation.md](docs/evaluation.md).

For a closer look at my design and results, the main documents are [architecture.md](docs/architecture.md), [design.md](agent_docs/design.md), and the [requirements checklist](agent_docs/requirements.md).

## Sample queries

My usual starting point is a ready book with the spoiler scope already set. These examples cover passage retrieval, nonfiction analysis, and web research:

| Book and settings | Sample query |
| --- | --- |
| Alice's Adventures in Wonderland · Brief · Chapter 1 | Why does Alice follow the White Rabbit? Use original passages and avoid spoilers beyond chapter 1. |
| The Art of War · Detailed · Chapter 1 | Explain the five constant factors in chapter 1. How do they relate to planning, and which passages support the explanation? |
| Alice's Adventures in Wonderland · Detailed · Whole book | Tell me about Lewis Carroll, find a film adaptation of this book, and look for a hardcover edition to buy. Cite the web sources and distinguish confirmed details from uncertain matches. |

The **Source** button opens an original passage, while **Activity** lets me inspect agent, provider, and tool decisions. Web research needs whole-book scope because external pages may reveal later events. I can also ask follow-up questions or start a separate saved chat.

## Local setup

My local setup starts from the repository root. The container and CI use Python 3.13; the environment, caches, test data, and reports all stay inside this folder.

```sh
python3.13 -m venv .venv
mkdir -p .cache/tmp .cache/pip reports
export TMPDIR="$PWD/.cache/tmp"
export PIP_CACHE_DIR="$PWD/.cache/pip"
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m pip install -r requirements.txt -r requirements-ci.txt
cp .env.example .env
```

My credentials go in the local, ignored `.env` file. The setup needs:

- A random session secret of at least 32 characters.
- Funded OpenAI access for embeddings and planning: `text-embedding-3-small` and `gpt-6-luna`.
- NVIDIA student access for ordinary responses: `nvidia/nemotron-3-ultra-550b-a55b`.
- Anthropic access for deep responses: `claude-sonnet-5`.
- Tavily Remote MCP access and a 1,536-dimensional cosine Pinecone index.

Before ingestion, my Pinecone account needs a dense cosine index with 1,536 dimensions. I named it `book-companion` and used serverless AWS `us-east-1` on Starter; `PINECONE_INDEX` allows a different name.

```sh
.venv/bin/python -m scripts.prepare_library
.venv/bin/python -m uvicorn src.app:create_app --factory --host 127.0.0.1 --port 8080
```

Once the server is running, `http://127.0.0.1:8080` opens the reading interface. From there, I choose a ready book, spoiler boundary, and depth before asking a question. Separate chats stay saved in the same browser without an account. Clearing the browser identity removes access to those chats; I do not promise cross-device recovery.

## Books, uploads, and saved chats

My curated library contains eight complete public-domain books from a Project Gutenberg mirror, with titles and editions recorded in [corpus/manifest.json](corpus/manifest.json).

- **Uploads:** English, text-based PDF/EPUB/TXT files are supported up to 25 MB, with caps of 500 PDF pages, 125,000 EPUB/TXT words, and 250,000 extracted tokens. Encrypted, scanned-only, unreadable, and unsupported-language files receive a rejection message.
- **Recovery:** Completed chats survive refresh. After process loss, an expired 330-second turn lease becomes interrupted rather than complete. Stop can cancel silent generation without waiting for another token.
- **Private books:** Retry handles failed processing, and a category selector allows correction of fiction/nonfiction classification.
- **Scope:** Unrelated requests receive a book-focused redirect and an off-topic/no-worker trace. Book-related creative questions and follow-ups remain supported.
- **Admission:** Hourly limits are 30 chat attempts per owner and 600 service-wide, plus 10 uploads/retries per owner and 80 service-wide. Clearing the anonymous cookie changes identity, so these limits are not a substitute for authenticated abuse prevention.

### Rebuilding the curated library

To make my library reproducible, I included the exact **October 27, 2026, pipeline-2** snapshot in `corpus/snapshot.json.gz`, containing:

- Eight original books with Gutenberg licenses and source URLs.
- All 864 chunks and structured evidence maps.
- Edition timestamps and SHA-256 checksums exported from deployed storage.

Private uploads, conversations, credentials, and Pinecone vector binaries are excluded from that snapshot. My preparation script verifies and uses the pinned originals; without the snapshot, it downloads mirror files that may have changed.

My planning estimate for a fresh eight-book embedding/extraction rebuild is **10–30 minutes**. This is a planning estimate, not a measured clean-rebuild duration. The included snapshot avoids downloading the books, but regeneration still needs API access and can produce different chapter summaries. I preserve deployed maps for comparison and do not overwrite a populated index or spending ledger.

## Tests and evaluation

```sh
TIKTOKEN_CACHE_DIR="$PWD/.cache/tiktoken" .venv/bin/python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest tests --ignore=tests/live --junitxml=reports/offline.xml
.venv/bin/python scripts/verify_release.py report reports/offline.xml
node --test tests/test_stream.cjs
```

Node is only a test dependency for my vanilla stream parser; the container needs no frontend framework, package installation, or Node runtime. My offline Python suite uses project-local temporary storage, blocked external socket connections, and outside-write guards. I test real service calls separately:

```sh
BASE_URL="https://MY_CLOUD_RUN_URL" .venv/bin/python -m pytest tests/live --junitxml=reports/live.xml
.venv/bin/python scripts/verify_release.py report reports/live.xml
.venv/bin/python -m pip install -r requirements-eval.txt
.venv/bin/python -m src.eval.ragas_eval --url "https://MY_CLOUD_RUN_URL" --cloud
```

The fixed questions and reference answers in `src/eval/questions.json` make my RAGAS evaluation repeatable across faithfulness, answer relevance, context precision, and context recall. My evaluation calls share the same spending ledger as the cloud application. I distinguish fixture timings from real provider and Cloud Run measurements.

## Google Cloud deployment

My deployment setup requires a billing-enabled project with eligible credits, authenticated Google Cloud CLI/application-default credentials, and owner-equivalent provisioning permissions. For a fresh project, I set its ID and region explicitly; my scripts create the application's dedicated resources without using Assignment 1 files.

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

These commands assume the official Google Cloud CLI is installed under `.cache/tools/google-cloud-sdk`. My provisioning script creates a separate private bucket, application-prefixed Firestore collections, Artifact Registry repository, runtime identity, secret versions, and ingestion job. I migrate the cumulative spending ledger once and stop paid local calls before switching to cloud execution. I never overwrite an existing cloud budget ledger.

For another repository/project, I update `REPOSITORY` in `scripts/github_setup.py` and the workflow’s `GCP_PROJECT_ID`/region before running its setup. I authenticate the project-local GitHub CLI as the repository owner. I configure repository/main-scoped GitHub Workload Identity Federation with `scripts.github_setup`. My workflow runs on pushes and pull requests and deploys only `main`. I pass the tested container between jobs, deploy its digest, run candidate acceptance, promote it, and test the public URL. A failed post-promotion check restores the previous revision's traffic. I store actual API keys in Secret Manager, not GitHub variables or source.

## Cost and access policy

My total project budgets are **$5 OpenAI** and **$5 Anthropic**, enforced through transactional reservations before paid requests. The standard rates I verified on October 27, 2026 are:

| Model | Input per million tokens | Output per million tokens |
| --- | ---: | ---: |
| GPT-6 Luna | $0.10 | $0.50 |
| Claude Sonnet 5 | $2.00 | $10.00 |
| text-embedding-3-small | $0.02 | Not applicable |

For the other services, my setup uses NVIDIA/Tavily student access, Pinecone Starter, and existing GCP credits. Those allowances do not cover OpenAI or Anthropic charges. I disabled automatic budget expansion: a paid request stops if the shared ledger cannot reserve its estimated maximum cost. Unknown charges remain conservatively reserved. I have not enabled paid plan upgrades or automatic top-ups.

For a rough per-run budget, I use my measured examples below. These are paid generation costs, not complete invoices; query embeddings, web searches, ingestion, and cloud resources are separate.

| Run I measured | Recorded paid generation | How I use the estimate |
| --- | ---: | --- |
| One brief cited answer in my nine-question run | $0.0000534–$0.0008403 | About $0.005–$0.084 for 100 comparable answers; provider recovery increased some calls. NVIDIA did not return billed usage. |
| One whole-book deep query using all three specialists | $0.15197 | Roughly $0.15 per comparable deep query; length, evidence size, and fallback calls can change the cost substantially. |

For embedding alone, I estimate about **$0.0114** to process my 570,802-token corpus once at $0.02 per million tokens, before overlap and request overhead. This is a lower-bound component estimate, not the price of a full rebuild: chapter extraction and later generation add cost. I include the measured traces in [evaluation_results.json](docs/evaluation_results.json).

Before and after ingestion, evaluations, or repeated live tests, my usage review covers:

- OpenAI Usage and Anthropic Console totals, compared with my shared spending ledger.
- Remaining Tavily credits and Pinecone usage, tracked separately from model tokens.
- Google Cloud Billing reports and budget alerts for compute, storage, and credit consumption.
- Whether account totals or remaining credits still fit my budget; otherwise, paid testing stops.

Provider dashboards remain my billing reference. My ledger limits this application, but it cannot account for unrelated activity on the same accounts.

My rate references are [OpenAI's model catalog](https://developers.openai.com/api/docs/models/gpt-6-luna), [OpenAI embedding pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small), and [Anthropic's Sonnet 5 documentation](https://platform.claude.com/docs/en/models/sonnet-5/overview). I report actual usage evidence separately from listed prices.

My [process log](PROCESS_LOG.md) covers development, verification, and personal learning; the [requirements checklist](agent_docs/requirements.md) records completion status.
