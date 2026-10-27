# My Book Companion

I built this CSCI 599 Assignment 2 project around a LangGraph supervisor, three specialist agents, Pinecone RAG, shared Tavily Remote MCP tools, and a FastAPI-served reading interface. I use eight public-domain fiction/nonfiction books and accept private English PDF, EPUB, and TXT uploads.

My public application is **https://book-companion-a6lyssed7q-uw.a.run.app**. I retain my actual measurements in [docs/evaluation.md](docs/evaluation.md).

I keep my architecture in [docs/architecture.md](docs/architecture.md), design rules in [agent_docs/design.md](agent_docs/design.md), and the complete rubric checklist and verification status in [agent_docs/requirements.md](agent_docs/requirements.md).

## My local setup

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

I fill `.env` locally with provider keys and a random session secret of at least 32 characters. I never commit it. I use the exact verified IDs `gpt-6-luna`, `claude-sonnet-5`, and `nvidia/nemotron-3-ultra-550b-a55b`. I require funded OpenAI access for embeddings/planning, my NVIDIA student access for ordinary responses, Anthropic for deep responses, Tavily Remote MCP access, and a 1,536-dimensional cosine Pinecone index.

I create the `book-companion` dense cosine index in my Pinecone account with 1,536 dimensions (my Starter deployment uses serverless AWS `us-east-1`) before ingestion. I set `PINECONE_INDEX` if I choose another name.

```sh
.venv/bin/python -m scripts.prepare_library
.venv/bin/python -m uvicorn src.app:create_app --factory --host 127.0.0.1 --port 8080
```

I open `http://127.0.0.1:8080`. I select a ready book, choose a spoiler boundary and depth, and ask a question. I can maintain separate saved chats in the same browser without an account. Clearing the browser identity removes access to those chats; I do not promise cross-device recovery.

I use an official Gutenberg mirror and retain original source files and edition metadata. My curated manifest is [corpus/manifest.json](corpus/manifest.json). My private uploads are limited to 25 MB, 500 PDF pages or 125,000 EPUB/TXT words, and 250,000 extracted tokens. I reject encrypted/scanned-only or unreadable files and unsupported languages.

I ship my exact **October 27, 2026, pipeline-2** corpus snapshot in `corpus/snapshot.json.gz`: eight public originals with their Gutenberg licenses, 864 chunks, structured evidence maps, source URLs, timestamps, and SHA-256 checksums. I exported it from deployed storage. My preparation script prefers these pinned originals and verifies their hashes; if the snapshot is absent, it downloads current mirror files, which may represent a different edition snapshot. I omit private uploads, conversations, credentials, and Pinecone vector binaries. I keep the complete chunk and fact records inspectable in the compressed JSON.

I estimate **10–30 minutes** for a fresh eight-book embedding/extraction rebuild, depending on provider latency and quotas; this is a planning estimate, not a measured clean-rebuild duration. Download is unnecessary with my shipped snapshot. Regeneration still requires the documented APIs and can produce different probabilistic chapter summaries. I preserve the deployed maps in my snapshot for comparison. I do not overwrite a populated index or spending ledger to demonstrate reproducibility.

I keep my assistant focused on books. For unrelated weather requests or unrelated creative tasks, I return a short redirect with example book questions, emit an explicit off-topic/no-worker decision, and invoke no specialist or web search. Book-related creative questions and follow-ups remain in scope. I show actual supervisor transitions and full trace details in Activity, including the Summary Agent's input scope and original chunk IDs.

I allow 30 chat attempts per anonymous owner per hour and 600 across the service; uploads/retries allow 3 per owner and 24 service-wide per hour. These transactional limits complement my global paid-provider budgets. They are not identity-proof abuse prevention: clearing the anonymous cookie changes identity. I offer Retry for failed private uploads and a category selector for private books. I preserve completed chats across refresh; after process loss, an expired 330-second turn lease becomes interrupted rather than falsely completed. Silent generation can be stopped without waiting for another model token.

## My tests and evaluation

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

## My Google Cloud deployment

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

## My cost and access policy

I cap total project usage at **$5 OpenAI** and **$2.50 Anthropic**, with transactional reservations before paid requests. I verified the following standard rates on October 27, 2026:

| My model | Input per million tokens | Output per million tokens |
| --- | ---: | ---: |
| GPT-6 Luna | $0.10 | $0.50 |
| Claude Sonnet 5 | $2.00 | $10.00 |
| text-embedding-3-small | $0.02 | Not applicable |

I use the confirmed NVIDIA/Tavily student plans and eligible GCP credits; I do not assume those cover other provider bills. I have not enabled paid plan upgrades or automatic top-ups. I use short bounded prompts for the quoted generation rates and retain conservative charges when a request's actual billing is unknown. I stop paid requests when my ledger cannot reserve their upper bound.

I source these rates from [OpenAI's model catalog](https://developers.openai.com/api/docs/models/gpt-6-luna), [OpenAI embedding pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small), and [Anthropic's Sonnet 5 documentation](https://platform.claude.com/docs/en/models/sonnet-5/overview). I report actual usage evidence separately from listed prices.

I record my development and verification narrative in [PROCESS_LOG.md](PROCESS_LOG.md). I keep the current completion status in [my requirements checklist](agent_docs/requirements.md).
