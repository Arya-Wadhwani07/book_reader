# Book Companion Evaluation

I evaluated the deployed book companion on October 27, 2026, using real model, Pinecone, Tavily MCP, and Cloud Run calls. I keep the raw measurements in [evaluation_results.json](evaluation_results.json) and my fixed questions/references in [questions.json](../src/eval/questions.json). I distinguish my initial quality baseline from later release and regression checks.

## Fixed RAGAS evaluation

I evaluated six fixed questions across Alice, The Time Machine, Jekyll and Hyde, The Art of War, and The Prince. I supplied actual vector-retrieval passages, reference answers, and generated responses to RAGAS 0.4.3 with a budgeted GPT-6 Luna judge and text-embedding-3-small embeddings. I used `raise_exceptions=True`; all 24 metric computations completed. I evaluated the provider-recovery implementation from commit `d21cf5d`.

| Metric | Released-run mean | Initial baseline |
| --- | ---: | ---: |
| Faithfulness | 0.9028 | 0.8611 |
| Answer relevance | 0.8931 | 0.9357 |
| Context precision | 0.7361 | 0.6944 |
| Context recall | 1.0000 | 1.0000 |

I interpret the four metrics as follows:

- **Faithfulness:** I check whether answer claims are supported by the supplied evidence.
- **Answer relevance:** I check how well the response addresses the question.
- **Context precision:** I check whether useful retrieved passages rank ahead of irrelevant ones.
- **Context recall:** I check how much of the reference answer is supported by the retrieved passages.

I used six questions to get a repeatable comparison, so these scores cover a small sample of the library. Recall was high, but retrieval still returned irrelevant passages, and some answers added unsupported detail. I kept those weaker results in the report. My initial baseline used revision `book-companion-00001-dac`.

I corrected my evaluator to use the actual `rag_retrieval.chunk_ids`, rather than all citations from Summary/Data. I reused the already-generated responses after correcting that context selection; I did not regenerate answers to improve their scores. My prior `a84c809` run exercised provider recovery; I preserve that run separately in the JSON. I regenerated all six fixed questions on the final implementation, without selecting answers by score. My pinned RAGAS compatibility wrappers emit deprecation notices; all metrics still execute, and I do not suppress evaluator failures.

| Question | Retrieval (s) | LLM work (s) | Total (s) | TTFT (s) | Paid generation (USD) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q1: Why does Alice follow the White Rabbit at the beginning of the story? | 1.358 | 5.803 | 8.698 | 7.205 | $0.0000554 |
| Q2: What happens when Alice drinks from the bottle labelled DRINK ME? | 0.794 | 5.137 | 6.377 | 4.703 | $0.0000538 |
| Q3: What does the Time Traveller say the fourth dimension is? | 1.311 | 8.574 | 10.619 | 8.926 | $0.0000524 |
| Q4: What does Mr Enfield see Hyde do to a little girl? | 0.979 | 5.656 | 7.348 | 5.853 | $0.0000529 |
| Q5: What five constant factors does Sun Tzu say govern the art of war? | 0.841 | 15.522 | 17.044 | 14.850 | $0.0000539 |
| Q6: How does Machiavelli distinguish hereditary principalities from new principalities? | 1.157 | 15.100 | 16.949 | 9.212 | $0.0000526 |

I time retrieval independently from generation. My client total includes obtaining original passages for verification; TTFT ends at the first streamed token. The paid-generation column excludes separately reserved embeddings, student-plan NVIDIA usage, and infrastructure costs. I retain exact usage traces and answers in the JSON evidence.

## Latency measurements

I measured first-hit behavior on an idle, separately tagged revision and then repeated the same two-sentence Alice question. End-to-end TTFT includes anonymous-session bootstrap and chat creation; query TTFT starts immediately before the chat request. My first-hit figure includes client/network/setup overhead and is not a measurement of container initialization alone.

| Run | Bootstrap (s) | End-to-end TTFT (s) | Query TTFT (s) | Query total (s) |
| --- | ---: | ---: | ---: | ---: |
| first_hit_after_idle | 25.561 | 38.724 | 12.791 | 18.533 |
| warm | 0.240 | 11.447 | 11.037 | 12.089 |

I measured the following retrieval and generation work separately on those same calls. My total includes orchestration, checkpoint persistence, and network overhead, so it exceeds the sum of model execution and vector retrieval.

| Run | Retrieval (s) | Sum of LLM calls (s) | Recorded paid generation cost (USD) |
| --- | ---: | ---: | ---: |
| first_hit_after_idle | 1.683 | 16.252 | $0.0000402 |
| warm | 1.095 | 10.623 | $0.0000452 |

I report unknown NVIDIA billing metadata as unknown rather than as measured zero. My confirmed student plan supplies that access. The generation-cost column excludes separately reserved query embeddings, web searches, and cloud infrastructure.

## Provider comparison

I sent the same Alice question and the same two original chunks to each provider through my budgeted adapter. For each call, I checked that the response contained an answer and an original chunk ID. These are direct generation timings, not full graph or Cloud Run timings.

| Provider | TTFT (s) | Total (s) | Recorded token cost (USD) |
| --- | ---: | ---: | ---: |
| nvidia | 1.633 | 2.607 | Student plan; usage unavailable |
| openai | 1.095 | 1.841 | $0.0001954 |
| anthropic | 1.085 | 3.504 | $0.0068420 |

I found that all three answers identified curiosity and the pocket watch. OpenAI was shortest; NVIDIA added modest explanation; Sonnet explicitly separated fact from interpretation. I would not rank the providers from this one example; it shows how they handled the same evidence in this run. Exact models and dated prices appear in my [architecture](architecture.md) and [README](../README.md).

## Corpus and product verification

I indexed eight complete public-domain books: 425,982 extracted words, 570,802 tokens, and 864 original chunks. My largest source, Walden with Civil Disobedience, contains 115,831 words and 153,361 tokens. I preserve source URLs and original files.

- My offline suite passed 168 Python tests and 90 JavaScript stream-parser tests without failures or skips. My offline tests block external socket access and writes outside Assignment 2; I do not describe Python guards as an OS security sandbox.
- I tested PDF, EPUB, and TXT ingestion on the live service, duplicate rejection, private-book listing isolation, and original-source authorization. My synthetic files completed in approximately 28.6, 31.6, and 32.3 seconds respectively.
- I reproduced three HTTP 429 responses in an earlier 120-read/12-worker stress test. After increasing Cloud Run request concurrency to 16, all 120 reads passed in 3.515 seconds. My final 120-read/12-worker rerun also passed, taking 21.847 seconds; latency varies under concurrent verification. I do not claim an unbounded production load capacity.
- I verified Research and Data invoking the same Tavily MCP tool with different queries, and a separate complete deep query exercised all three specialists plus OpenAI/Sonnet routing (98.171 s TTFT; 113.421 s total). I show activity during that wait, because a deep response can take much longer than a brief answer.
- I restored a saved answer through a separately deployed revision, checking exact answer equality and completed status. I also verified refresh restoration and opening an original passage in Chrome.
- I found browser-origin rejection behind TLS termination, unreliable explicit-retrieval delegation, a missing ingestion-job override permission, Unicode boundary corruption, transient provider failures, and incomplete generation. I retain regression checks and failed-run evidence.

## Costs and interpretation

I use a shared transactional ledger for paid ingestion, generation, evaluation, recovery attempts, and verification. My later shared-ledger snapshot recorded $0.498718 spent plus $0.003640 reserved for OpenAI, and $0.490894 spent plus $0 reserved for Anthropic. Active verification calls explain the reservations. Every call uses the same ledger and cannot reserve above the approved $5/$2.50 limits. Embedding reservations conservatively use UTF-8 byte counts because the wrapper does not return billed token usage; generation uses reported tokens when available.

I use confirmed NVIDIA/Tavily student access, Pinecone Starter, and existing GCP credits. I have not measured final infrastructure invoices or claimed that credits make resource consumption free. Firestore, GCS, Cloud Run, Artifact Registry, and Cloud Build are separate from LLM usage.

I keep scanned/OCR books, non-English books, cross-device account recovery, and lossless summaries outside the implemented scope. Whole-text sources without recognizable chapter headings provide coarse spoiler boundaries. Model answers remain probabilistic; passing software tests does not prove every literary claim correct.

## Instructor-clarification regression review

I added explicit off-topic/no-worker handling, per-hop state traces, pre-generation Summary evidence traces, and an inspectable trace-data panel. I added regression cases for silent-provider cancellation, storage failure before completion, expired process leases, ingestion resume/idempotency, owner-scoped retries, malformed EPUB metadata/entities, and hourly admission. My realistic long-book parser check reproduces all Walden chunks with the actual tokenizer and checks its 115,831 words against the deployed snapshot. I also parse generated 300/400/500-page PDFs containing 60,000/80,000/100,000 words from that source with the real tokenizer, alongside minimal boundary fixtures. I do not claim exhaustive PDF-layout coverage.

I originally planned to test through VS Code, but its browser access was unavailable. I used Chrome for this application instead; the browser observations below come from Chrome.

## Infrastructure cost method

I checked the official pricing references on October 27, 2026. In my cost estimates, I separate Cloud Run CPU-seconds/GiB-seconds/requests and network transfer, ingestion-job compute, Firestore document/index reads and writes plus storage, GCS stored bytes/operations/transfer, and image/build storage and execution. I calculate infrastructure cost as measured usage multiplied by the applicable regional rate. I have not obtained a final billing export, so I do not report an infrastructure total. My web service uses 1 CPU/1 GiB, concurrency 16, min 0/max 2; ingestion uses 1 CPU/2 GiB with a one-hour deadline. My prior 120-read stress run informed the concurrency choice. [Cloud Run pricing](https://cloud.google.com/run/pricing), [Firestore pricing](https://cloud.google.com/firestore/pricing), [GCS pricing](https://cloud.google.com/storage/pricing).

I use Basic Tavily searches, listed at one credit per request; the published free allowance is 1,000 credits/month. Two successful shared-tool calls consume two search credits, distinct from any LLM tokens. I rely on my student access rather than assuming unlimited quota. Pinecone lists Starter as free; I do not enable an upgrade. Remaining account balances are separate from publicly listed allowances. [Tavily credits](https://docs.tavily.com/documentation/api-credits), [Pinecone plans](https://www.pinecone.io/pricing/).

## Browser observations and limits

I used Chrome against the deployed service and recorded these observations:

- I checked an off-topic redirect, a cited Alice interpretation, and an unsupported nonfiction premise.
- I opened Summary input details and original-source passages, restored chats after refresh, and used two tabs with separate selected contexts.
- I checked Stop, keyboard focus, and the deletion confirmation, which I cancelled.
- I observed an answer grow from 1 to 2,092 characters while generation remained active.
- I checked 390/640/1024-pixel viewports: content and scroll widths matched. The checked rendered text pairs had contrast ratios from 5.63:1 to 13.95:1.

I kept the existing browser file permissions, so my upload evidence comes from API checks for all three formats, not the file picker. I also did not establish actual 200% browser zoom through keyboard automation; responsive-width checks are separate evidence. I record those verification limits in my requirements checklist.
