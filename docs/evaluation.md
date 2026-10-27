# My Book Companion Evaluation

I measured real provider, Pinecone, Tavily MCP, and Cloud Run behavior on October 27, 2026. I keep reproducible raw measurements in [evaluation_results.json](evaluation_results.json) and my fixed questions/references in [questions.json](../src/eval/questions.json). I distinguish my initial quality baseline from later release and regression checks.

## My fixed RAGAS baseline

I evaluated six fixed questions across Alice, The Time Machine, Jekyll and Hyde, The Art of War, and The Prince. I supplied original retrieved passages, reference answers, and generated responses to RAGAS 0.4.3 with a budgeted GPT-6 Luna judge and text-embedding-3-small embeddings. I used `raise_exceptions=True`; all 24 metric computations completed.

| My metric | My mean |
| --- | ---: |
| Faithfulness | 0.8611 |
| Answer relevance | 0.9357 |
| Context precision | 0.6944 |
| Context recall | 1.0000 |

I obtained this baseline on revision `book-companion-00001-dac`. I do not present six questions as comprehensive book coverage or a grade guarantee. Context recall was high, while precision showed irrelevant retrieved passages; unsupported elaboration reduced faithfulness in several answers. I retained these weaker results rather than selecting only successful-looking answers. A later rerun failed during generation and therefore did not produce a replacement quality score.

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

- I passed 142 offline Python tests and 90 JavaScript stream-parser tests without failures or skips. My offline tests block external socket access and writes outside Assignment 2; I do not describe Python guards as an OS security sandbox.
- I exercised real PDF, EPUB, and TXT cloud ingestion, duplicate rejection, private-book listing isolation, and original-source authorization. My synthetic files completed in approximately 40.0, 32.8, and 28.7 seconds respectively.
- I reproduced three HTTP 429 responses in an earlier 120-read/12-worker stress test. After increasing Cloud Run request concurrency to 16, all 120 reads passed in 3.515 seconds. I do not claim an unbounded production load capacity.
- I verified Research and Data invoking the same Tavily MCP tool with different queries, and a separate deep query exercised all three specialists plus OpenAI/Sonnet routing.
- I restored a saved answer through a separately deployed revision, checking exact answer equality and completed status. I also verified refresh restoration and opening an original passage in Chrome.
- I found browser-origin rejection behind TLS termination, unreliable explicit-retrieval delegation, a missing ingestion-job override permission, Unicode boundary corruption, transient provider failures, and incomplete generation. I retain regression checks and failed-run evidence.

## My costs and interpretation

I use a shared transactional ledger for paid ingestion, generation, evaluation, recovery attempts, and verification. My recorded comparison snapshot was $0.448953 OpenAI and $0.007024 Anthropic, with no pending reservations. Subsequent calls use the same ledger and cannot reserve above the approved $5/$2.50 limits. Embedding reservations conservatively use UTF-8 byte counts because the wrapper does not return billed token usage; generation uses reported tokens when available.

I use confirmed NVIDIA/Tavily student access, Pinecone Starter, and existing GCP credits. I have not measured final infrastructure invoices or claimed that credits make resource consumption free. Firestore, GCS, Cloud Run, Artifact Registry, and Cloud Build are separate from LLM usage.

I keep scanned/OCR books, non-English books, cross-device account recovery, and lossless summaries outside the implemented scope. Whole-text sources without recognizable chapter headings provide coarse spoiler boundaries. Model answers remain probabilistic; passing software tests does not prove every literary claim correct.
