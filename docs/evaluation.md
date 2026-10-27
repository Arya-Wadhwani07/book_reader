# My Book Companion Evaluation

I measured real provider, Pinecone, Tavily MCP, and Cloud Run behavior on October 27, 2026. I keep reproducible raw measurements in [evaluation_results.json](evaluation_results.json) and my fixed questions/references in [questions.json](../src/eval/questions.json). I distinguish my initial quality baseline from later release and regression checks.

## My fixed RAGAS evaluation

I evaluated six fixed questions across Alice, The Time Machine, Jekyll and Hyde, The Art of War, and The Prince. I supplied actual vector-retrieval passages, reference answers, and generated responses to RAGAS 0.4.3 with a budgeted GPT-6 Luna judge and text-embedding-3-small embeddings. I used `raise_exceptions=True`; all 24 metric computations completed. I evaluated the provider-recovery implementation from commit `a84c809`.

| My metric | My released-run mean | My initial baseline |
| --- | ---: | ---: |
| Faithfulness | 0.8551 | 0.8611 |
| Answer relevance | 0.9003 | 0.9357 |
| Context precision | 0.7139 | 0.6944 |
| Context recall | 1.0000 | 1.0000 |

I do not present six questions as comprehensive book coverage or a grade guarantee. Recall was high, while precision showed irrelevant retrieved passages and unsupported elaboration reduced faithfulness. I retain weaker results rather than selecting successful-looking answers. My initial baseline used revision `book-companion-00001-dac`.

I corrected my evaluator to use the actual `rag_retrieval.chunk_ids`, rather than all citations from Summary/Data. I reused the already-generated responses after correcting that context selection; I did not regenerate answers to improve their scores. One released-run question exercised provider recovery, and I include its added latency. My pinned RAGAS compatibility wrappers emit deprecation notices; all metrics still execute, and I do not suppress evaluator failures.

| My question | Retrieval (s) | LLM work (s) | Total (s) | TTFT (s) | Paid generation (USD) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q1: Why does Alice follow the White Rabbit at the beginning of the story? | 1.060 | 12.602 | 14.587 | 11.327 | $0.0000445 |
| Q2: What happens when Alice drinks from the bottle labelled DRINK ME? | 0.788 | 30.003 | 31.405 | 8.333 | $0.0005776 |
| Q3: What does the Time Traveller say the fourth dimension is? | 0.748 | 8.950 | 10.330 | 5.354 | $0.0000422 |
| Q4: What does Mr Enfield see Hyde do to a little girl? | 1.012 | 9.257 | 10.954 | 8.369 | $0.0000409 |
| Q5: What five constant factors does Sun Tzu say govern the art of war? | 0.954 | 16.160 | 17.801 | 11.785 | $0.0000416 |
| Q6: How does Machiavelli distinguish hereditary principalities from new principalities? | 0.900 | 23.941 | 25.463 | 13.574 | $0.0000450 |

I time retrieval independently from generation. My client total includes obtaining original passages for verification; TTFT ends at the first streamed token. The paid-generation column excludes separately reserved embeddings, student-plan NVIDIA usage, and infrastructure costs. I retain exact usage traces and answers in the JSON evidence.

## My latency measurements

I measured first-hit behavior on an idle, separately tagged revision and then repeated the same two-sentence Alice question. End-to-end TTFT includes anonymous-session bootstrap and chat creation; query TTFT starts immediately before the chat request. My first-hit figure includes client/network/setup overhead and is not a measurement of container initialization alone.

| My run | Bootstrap (s) | End-to-end TTFT (s) | Query TTFT (s) | Query total (s) |
| --- | ---: | ---: | ---: | ---: |
| first_hit_after_idle | 25.561 | 38.724 | 12.791 | 18.533 |
| warm | 0.240 | 11.447 | 11.037 | 12.089 |

I measured the following retrieval and generation work separately on those same calls. My total includes orchestration, checkpoint persistence, and network overhead, so it exceeds the sum of model execution and vector retrieval.

| My run | Retrieval (s) | Sum of LLM calls (s) | Recorded paid generation cost (USD) |
| --- | ---: | ---: | ---: |
| first_hit_after_idle | 1.683 | 16.252 | $0.0000402 |
| warm | 1.095 | 10.623 | $0.0000452 |

I report unknown NVIDIA billing metadata as unknown rather than as measured zero. My confirmed student plan supplies that access. The generation-cost column excludes separately reserved query embeddings, web searches, and cloud infrastructure.

## My provider comparison

I sent the same Alice question and the same two original chunks to each provider through my budgeted adapter. I required a nonempty answer with an original chunk ID. These are direct generation timings, not full graph or Cloud Run timings.

| My provider | TTFT (s) | Total (s) | Recorded token cost (USD) |
| --- | ---: | ---: | ---: |
| nvidia | 1.633 | 2.607 | Student plan; usage unavailable |
| openai | 1.095 | 1.841 | $0.0001954 |
| anthropic | 1.085 | 3.504 | $0.0068420 |

I found that all three answers identified curiosity and the pocket watch. OpenAI was shortest; NVIDIA added modest explanation; Sonnet explicitly separated fact from interpretation. This single matched example supports a transparent comparison, not a general model ranking. Exact models and dated prices appear in my [architecture](architecture.md) and [README](../README.md).

## My corpus and product verification

I indexed eight complete public-domain books: 425,982 extracted words, 570,802 tokens, and 864 original chunks. My largest source, Walden with Civil Disobedience, contains 115,831 words and 153,361 tokens. I preserve source URLs and original files.

- I passed 144 offline Python tests and 90 JavaScript stream-parser tests without failures or skips. My offline tests block external socket access and writes outside Assignment 2; I do not describe Python guards as an OS security sandbox.
- I exercised real PDF, EPUB, and TXT cloud ingestion, duplicate rejection, private-book listing isolation, and original-source authorization. My synthetic files completed in approximately 40.0, 32.8, and 28.7 seconds respectively.
- I reproduced three HTTP 429 responses in an earlier 120-read/12-worker stress test. After increasing Cloud Run request concurrency to 16, all 120 reads passed in 3.515 seconds. I do not claim an unbounded production load capacity.
- I verified Research and Data invoking the same Tavily MCP tool with different queries, and a separate complete deep query exercised all three specialists plus OpenAI/Sonnet routing (91.677 s TTFT; 107.154 s total). I expose activity while waiting for the multi-stage result.
- I restored a saved answer through a separately deployed revision, checking exact answer equality and completed status. I also verified refresh restoration and opening an original passage in Chrome.
- I found browser-origin rejection behind TLS termination, unreliable explicit-retrieval delegation, a missing ingestion-job override permission, Unicode boundary corruption, transient provider failures, and incomplete generation. I retain regression checks and failed-run evidence.

## My costs and interpretation

I use a shared transactional ledger for paid ingestion, generation, evaluation, recovery attempts, and verification. My later shared-ledger snapshot recorded $0.473099 spent plus $0.001993 reserved for OpenAI, and $0.178154 spent plus $0.057254 reserved for Anthropic. Active verification calls explain the reservations. Every call uses the same ledger and cannot reserve above the approved $5/$2.50 limits. Embedding reservations conservatively use UTF-8 byte counts because the wrapper does not return billed token usage; generation uses reported tokens when available.

I use confirmed NVIDIA/Tavily student access, Pinecone Starter, and existing GCP credits. I have not measured final infrastructure invoices or claimed that credits make resource consumption free. Firestore, GCS, Cloud Run, Artifact Registry, and Cloud Build are separate from LLM usage.

I keep scanned/OCR books, non-English books, cross-device account recovery, and lossless summaries outside the implemented scope. Whole-text sources without recognizable chapter headings provide coarse spoiler boundaries. Model answers remain probabilistic; passing software tests does not prove every literary claim correct.

## My instructor-clarification regression review

I added explicit off-topic/no-worker handling, per-hop state traces, pre-generation Summary evidence traces, and an inspectable trace-data panel. I added regression cases for silent-provider cancellation, storage failure before completion, expired process leases, ingestion resume/idempotency, owner-scoped retries, malformed EPUB metadata/entities, and hourly admission. My realistic long-book parser check reproduces all Walden chunks with the actual tokenizer and checks its 115,831 words against the deployed snapshot. I distinguish that from my synthetic 300/400/500-page PDF boundary fixtures; I do not claim exhaustive PDF-layout coverage.

I requested VS Code-integrated testing, but computer-use access to Code was rejected. I then explicitly authorized Chrome only for Assignment 2 testing. I distinguish those Chrome checks from VS Code verification.

## My infrastructure cost method

I checked the official pricing references on October 27, 2026. I account separately for Cloud Run CPU-seconds/GiB-seconds/requests and network transfer, ingestion-job compute, Firestore document/index reads and writes plus storage, GCS stored bytes/operations/transfer, and image/build storage and execution. I use the applicable regional rate multiplied by measured usage when billing exports are available; I do not report an unobserved invoice as zero. My web service uses 1 CPU/1 GiB, concurrency 16, min 0/max 2; ingestion uses 1 CPU/2 GiB with a one-hour deadline. My prior 120-read stress run informed the concurrency choice. [Cloud Run pricing](https://cloud.google.com/run/pricing), [Firestore pricing](https://cloud.google.com/firestore/pricing), [GCS pricing](https://cloud.google.com/storage/pricing).

I use Basic Tavily searches, listed at one credit per request; the published free allowance is 1,000 credits/month. Two successful shared-tool calls consume two search credits, distinct from any LLM tokens. I rely on the user's confirmed student access rather than assuming unlimited quota. Pinecone lists Starter as free; I do not enable an upgrade. Remaining account balances are separate from publicly listed allowances. [Tavily credits](https://docs.tavily.com/documentation/api-credits), [Pinecone plans](https://www.pinecone.io/pricing/).
