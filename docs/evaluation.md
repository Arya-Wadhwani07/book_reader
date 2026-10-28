# Book Companion Evaluation

My evaluation on October 27, 2026 used real model, Pinecone, Tavily MCP, and Cloud Run calls. The raw measurements are in [evaluation_results.json](evaluation_results.json) and my fixed questions/references in [questions.json](../src/eval/questions.json). I distinguish my initial quality baseline from later release and regression checks.

## Fixed RAGAS evaluation

For a repeatable quality check, I use nine fixed questions covering all eight books. RAGAS 0.4.3 received the actual retrieved passages, reference answers, and generated responses, using a budgeted GPT-6 Luna judge and text-embedding-3-small embeddings. All 36 metric computations completed with `raise_exceptions=True` on application commit `b1ec3e5`.

| Metric | Expanded nine-question run | Earlier six-question run |
| --- | ---: | ---: |
| Faithfulness | 0.8719 | 0.9028 |
| Answer relevance | 0.7665 | 0.8931 |
| Context precision | 0.5920 | 0.7361 |
| Context recall | 0.8889 | 1.0000 |

The question sets differ, so this is not a controlled before/after quality comparison. I retain both runs and the initial baseline in the raw JSON; I do not select whichever run scores best.

The four metrics answer different questions about my results:

- **Faithfulness:** Are the answer claims supported by the supplied evidence?
- **Answer relevance:** How well does the response address the question?
- **Context precision:** Do useful retrieved passages rank ahead of irrelevant ones?
- **Context recall:** How much of the reference answer is supported by the retrieved passages?

Nine questions still represent a small sample. The harder additions exposed weak retrieval and imperfect grounding. In particular, the Walden question received zero relevance, precision, and recall: its required passage was not retrieved, and the answer acknowledged that limitation. Franklin's revised answer used valid original IDs and scored 1.0 faithfulness; Frankenstein scored 0.625, so valid IDs alone do not establish faithful claims.

During review, I corrected the evaluator to use actual `rag_retrieval.chunk_ids` rather than all citations from Summary/Data. My pinned RAGAS compatibility wrappers emit deprecation notices; all metrics execute, and evaluator failures are not suppressed. The earlier six-question run remains recorded at `d21cf5d`; the expanded run uses newly generated answers from `b1ec3e5`, including a traced provider recovery rather than discarding that slower case.

| Question | Retrieval (s) | LLM work (s) | Total (s) | TTFT (s) | Paid generation (USD) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q1: Why does Alice follow the White Rabbit at the beginning of the story? | 1.304 | 5.706 | 8.119 | 6.922 | $0.0000534 |
| Q2: What happens when Alice drinks from the bottle labelled DRINK ME? | 1.222 | 4.882 | 6.905 | 5.736 | $0.0007108 |
| Q3: What does the Time Traveller say the fourth dimension is? | 0.854 | 4.677 | 6.372 | 5.382 | $0.0006798 |
| Q4: What does Mr Enfield see Hyde do to a little girl? | 0.940 | 8.677 | 10.396 | 9.460 | $0.0001337 |
| Q5: What five constant factors does Sun Tzu say govern the art of war? | 0.845 | 7.696 | 9.314 | 4.918 | $0.0005845 |
| Q6: How does Machiavelli distinguish hereditary principalities from new principalities? | 0.916 | 22.500 | 24.673 | 21.226 | $0.0002225 |
| Q7: Why does Walton want a friend in his opening letters, despite having a crew? Distinguish his words from your interpretation. | 0.914 | 8.587 | 10.509 | 6.455 | $0.0006750 |
| Q8: Why does Thoreau say he went to the woods, and what did he want to learn there? Support your explanation with passages. | 0.986 | 11.274 | 13.138 | 11.128 | $0.0002234 |
| Q9: How did Franklin use his notebook and weekly routine to work on his virtues? Explain the method rather than just listing the virtues. | 0.933 | 6.101 | 8.193 | 5.894 | $0.0008403 |

Retrieval and generation are timed separately in my measurements. My client total includes obtaining original passages for verification; TTFT ends at the first streamed token. The paid-generation column excludes separately reserved embeddings, student-plan NVIDIA usage, and infrastructure costs. I retain exact usage traces and answers in the JSON evidence.

## Additional book coverage and citation review

My later review added three ordinary reader questions covering Frankenstein, Walden, and Franklin’s autobiography, without specifying worker names. The first run exposed two quality defects despite successful transport and source-panel checks: an unsupported Walden quotation and invented Franklin chunk IDs. I retain the answers and passages under `additional_books_pre_fix` in the raw evidence.

The revised Research prompt explicitly rejects remembered quotations absent from retrieved passages. Synthesis receives an authorized source-ID list and cannot report successful completion with an unknown chunk identifier. Regression tests cover fabricated, other-owner, and nonexistent chunk IDs; the expanded live suite also compares answer IDs against emitted sources. These checks establish source identity, not semantic entailment. The nine-question RAGAS table above measures the revised candidate, including these changes. I verified the Walden source vector exists, matches its original text, and has cosine similarity 0.999997 to a regenerated embedding. Its absence from a diagnostic top-30 search is a ranking limitation, not a missing corpus artifact.

## Latency measurements

To compare idle and warm behavior, I used a separately tagged revision and repeated the same two-sentence Alice question. End-to-end TTFT includes anonymous-session bootstrap and chat creation; query TTFT starts immediately before the chat request. My first-hit figure includes client/network/setup overhead and is not a measurement of container initialization alone.

| Run | Bootstrap (s) | End-to-end TTFT (s) | Query TTFT (s) | Query total (s) |
| --- | ---: | ---: | ---: | ---: |
| first_hit_after_idle | 25.561 | 38.724 | 12.791 | 18.533 |
| warm | 0.240 | 11.447 | 11.037 | 12.089 |

The following table separates retrieval from generation for those same calls. My total also includes orchestration, checkpoint persistence, and network overhead, so it exceeds their sum.

| Run | Retrieval (s) | Sum of LLM calls (s) | Recorded paid generation cost (USD) |
| --- | ---: | ---: | ---: |
| first_hit_after_idle | 1.683 | 16.252 | $0.0000402 |
| warm | 1.095 | 10.623 | $0.0000452 |

NVIDIA did not return billed usage for my student-plan calls, so those costs remain unknown rather than measured zero. The generation-cost column excludes separately reserved query embeddings, web searches, and cloud infrastructure.

## Provider comparison

For my provider comparison, each model received the same Alice question and the same two original chunks through the budgeted adapter. For each call, I checked that the response contained an answer and an original chunk ID. These are direct generation timings, not full graph or Cloud Run timings.

| Provider and model | TTFT (s) | Total (s) | Recorded token cost (USD) |
| --- | ---: | ---: | ---: |
| NVIDIA `nvidia/nemotron-3-ultra-550b-a55b` | 1.633 | 2.607 | Student plan; usage unavailable |
| OpenAI `gpt-6-luna` | 1.095 | 1.841 | $0.0001954 |
| Anthropic `claude-sonnet-5` | 1.085 | 3.504 | $0.0068420 |

All three answers identified curiosity and the pocket watch. OpenAI was shortest; NVIDIA added modest explanation; Sonnet explicitly separated fact from interpretation. I would not rank the providers from this one example; it shows how they handled the same evidence in this run. Exact models and dated prices appear in my [architecture](architecture.md) and [README](../README.md).

## Corpus and product verification

My indexed corpus contains eight complete public-domain books: 425,982 extracted words, 570,802 tokens, and 864 original chunks. My largest source, Walden with Civil Disobedience, contains 115,831 words and 153,361 tokens. I preserve source URLs and original files.

- My offline suite passed 173 Python tests and 102 JavaScript stream/Markdown tests without failures or skips. My offline tests block external socket access and writes outside Assignment 2; I do not describe Python guards as an OS security sandbox.
- **Uploads:** Live checks covered PDF, EPUB, and TXT ingestion, duplicate rejection, private-book listing isolation, and original-source authorization. My synthetic files completed in approximately 28.6, 31.6, and 32.3 seconds respectively.
- **Load:** An earlier 120-read/12-worker stress test produced three HTTP 429 responses. After increasing Cloud Run request concurrency to 16, all 120 reads passed in 3.515 seconds. My final 120-read/12-worker rerun also passed, taking 21.847 seconds; latency varies under concurrent verification. I do not claim an unbounded production load capacity.
- **Agent cooperation:** Research and Data invoked the same Tavily MCP tool with different queries. A separate deep query exercised all three specialists plus OpenAI/Sonnet routing (98.171 s TTFT; 113.421 s total). I show activity during that wait, because a deep response can take much longer than a brief answer.
- **Persistence:** A saved answer returned unchanged through a separate revision, including its completed status. I also verified refresh restoration and opening an original passage in Chrome.
- **Regression coverage:** Integration exposed browser-origin rejection behind TLS termination, unreliable explicit-retrieval delegation, a missing ingestion-job override permission, Unicode boundary corruption, transient provider failures, and incomplete generation. I retain regression checks and failed-run evidence.

## Costs and interpretation

My per-query paid-generation estimate sums each model call as `(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`. The rates recorded for October 27, 2026 are $0.10/$0.50 for GPT-6 Luna input/output and $2.00/$10.00 for Sonnet 5. Query embeddings are separate at $0.02 per million tokens; NVIDIA student-plan usage is unknown where the API supplied no billing metadata. This is a token-based estimate rather than an account invoice, and the query table labels its exclusions.

All paid ingestion, generation, evaluation, recovery attempts, and verification share my transactional spending ledger. My earlier shared-ledger snapshot, before the expanded evaluation, recorded $0.498718 spent plus $0.003640 reserved for OpenAI, and $0.490894 spent plus $0 reserved for Anthropic. Active verification calls explain the reservations. Every call uses the same ledger and cannot reserve above the approved $5/$5 limits. Embedding reservations conservatively use UTF-8 byte counts because the wrapper does not return billed token usage; generation uses reported tokens when available.

My other services use confirmed NVIDIA/Tavily student access, Pinecone Starter, and existing GCP credits. I have not measured final infrastructure invoices or claimed that credits make resource consumption free. Firestore, GCS, Cloud Run, Artifact Registry, and Cloud Build are separate from LLM usage.

Scanned/OCR books, non-English books, cross-device account recovery, and lossless summaries remain outside my implemented scope. Whole-text sources without recognizable chapter headings provide coarse spoiler boundaries. Model answers remain probabilistic; passing software tests does not prove every literary claim correct.

## Instructor-clarification regression review

The instructor's clarifications led me to add explicit off-topic/no-worker handling, per-hop state traces, pre-generation Summary evidence traces, and an inspectable trace-data panel. I added regression cases for silent-provider cancellation, storage failure before completion, expired process leases, ingestion resume/idempotency, owner-scoped retries, malformed EPUB metadata/entities, and hourly admission. My realistic long-book parser check reproduces all Walden chunks with the actual tokenizer and checks its 115,831 words against the deployed snapshot. I also parse generated 300/400/500-page PDFs containing 60,000/80,000/100,000 words from that source with the real tokenizer, alongside minimal boundary fixtures. I do not claim exhaustive PDF-layout coverage.

VS Code was my planned testing environment, but its browser access was unavailable. I used Chrome for this application instead; the browser observations below come from Chrome.

## Infrastructure cost method

My infrastructure cost method uses the official pricing references checked on October 27, 2026. In my cost estimates, I separate Cloud Run CPU-seconds/GiB-seconds/requests and network transfer, ingestion-job compute, Firestore document/index reads and writes plus storage, GCS stored bytes/operations/transfer, and image/build storage and execution. I calculate infrastructure cost as measured usage multiplied by the applicable regional rate. I have not obtained a final billing export, so I do not report an infrastructure total. My web service uses 1 CPU/1 GiB, concurrency 16, min 0/max 2; ingestion uses 1 CPU/2 GiB with a one-hour deadline. My prior 120-read stress run informed the concurrency choice. [Cloud Run pricing](https://cloud.google.com/run/pricing), [Firestore pricing](https://cloud.google.com/firestore/pricing), [GCS pricing](https://cloud.google.com/storage/pricing).

My Basic Tavily searches are listed at one credit per request, with a published free allowance of 1,000 credits/month. Two successful shared-tool calls consume two search credits, distinct from any LLM tokens. I rely on my student access rather than assuming unlimited quota. Pinecone lists Starter as free; I do not enable an upgrade. Remaining account balances are separate from publicly listed allowances. [Tavily credits](https://docs.tavily.com/documentation/api-credits), [Pinecone plans](https://www.pinecone.io/pricing/).

## Browser observations and limits

My Chrome review of the deployed service covered:

- An off-topic redirect, a cited Alice interpretation, and an unsupported nonfiction premise.
- Summary input details, original-source passages, refresh restoration, and two tabs with separate selected contexts.
- Stop, keyboard focus, and the deletion confirmation, which I cancelled.
- An answer growing from 1 to 2,092 characters while generation remained active.
- 390/640/1024-pixel viewports, where content and scroll widths matched. The checked rendered text pairs had contrast ratios from 5.63:1 to 13.95:1.

I kept the existing browser file permissions, so my upload evidence comes from API checks for all three formats, not the file picker. I also did not establish actual 200% browser zoom through keyboard automation; responsive-width checks are separate evidence. I record those verification limits in my requirements checklist.

My architecture review rendered all four Mermaid diagrams successfully. I changed the RAG flow to a vertical layout after finding that its horizontal version compressed the labels, then inspected the revised nodes and connections.

My Markdown UI review used a local no-API fixture based on the reported Prince answer. I verified incremental rendering, saved-chat refresh, nested lists, source dialogs, provider badges, exact task/model explanations, and repeated evidence inspection without duplicate badges. At a 390-pixel viewport the page had no horizontal overflow. These are fixture/browser observations, separate from live model quality measurements.
