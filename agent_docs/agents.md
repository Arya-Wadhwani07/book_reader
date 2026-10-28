# Assignment 2 Working Guidelines

## Scope and layout

I keep all project work inside `CSCI 599/Assignment 2/`, including dependencies, caches, temporary files, test data, and reports. My one-time inspection of Assignment 1's deployment configuration is complete; I do not access that folder again.

- I use lowercase snake_case for project-owned directories and preserve tool-required names such as `.github`.
- I follow the professor's required paths: root `README.md` and `PROCESS_LOG.md`, plus `docs/architecture.md` and `docs/evaluation.md`.
- I keep other authored Markdown in `agent_docs/` and preserve instructor references unchanged in `agent_docs/reference_docs/`.
- I read these guidelines at the start of work; I do not depend on automatic discovery of a root `AGENTS.md`.
- I keep local activity within the assignment folder. GitHub's managed runners and Google Cloud execution are the external services used by my authorized deployment workflow.

## Documentation and decisions

I use the assignment PDF and supplied references as the grading contract. I track every unfinished step and completion checkbox only in `agent_docs/requirements.md`.

- I write in first person, with short paragraphs, useful bullets, and tables for comparisons.
- I explain concrete choices and results, acknowledge AI assistance, and base personal reflections on my own experience.
- I avoid assistant-style narration, generic learning claims, and stale planning notes in deliverables.
- I preserve measured results and limitations; I mark completion only when supported by evidence.
- I clarify material unknowns while continuing work that does not depend on the answer.

## Chats, ownership, and uploads

I support multiple saved chats within one anonymous browser identity, without login/logout. I use server-verified `owner_id` for identity and `session_id` for a separate conversation.

- I persist messages, book context, preferences, citations, and checkpoints outside the Cloud Run instance. The cookie identifies the owner; it does not contain the conversation.
- I preserve earlier chats when starting a new one and require explicit confirmation for deletion.
- I authorize access on the server and test isolation, refresh, concurrent sessions, and recovery after instance replacement.
- I explain that clearing browser identity removes access and that cross-device recovery is outside the scope.

I accept English text-based PDF, EPUB, and TXT files within these displayed limits:

| Limit | Policy I enforce |
| --- | --- |
| File size | 25 MB (25,000,000 bytes) |
| PDF length | 500 physical pages |
| EPUB/TXT length | 125,000 words, approximately 500 pages at 250 words per page |
| Extracted input | 250,000 tokens |

I reject excess or unreadable input with a clear reason rather than silently truncating it. I verify substantial 300–400-page fixtures and the 500-page boundary before claiming support.

## Implementation and isolation

I keep the code simple enough to explain and maintain. Every file, dependency, helper, and import needs a concrete use.

- I remove unused imports, dead code, duplicate logic, abandoned scaffolding, and commented-out implementations.
- I pin dependencies, handle expected failures explicitly, and keep credentials out of source, logs, traces, images, and archives.
- I run Python through `.venv/bin/python` and lint through `.venv/bin/ruff`; I never install project packages globally. My container uses `/app/.venv`, and CI creates its environment inside the checkout.
- I keep `TMPDIR`, pip caches, bytecode, fixtures, and reports inside Assignment 2.
- I isolate offline tests with temporary stores, fake credentials, blocked external network access, and outside-write guards. I identify real service calls separately.
- I review each change for correctness, necessity, ownership boundaries, cost, and rubric coverage.

## Testing and acceptance

I require a nonempty acceptance suite with no failures, errors, skips, expected failures, or unexpected passes. I fix the cause of a failure rather than weakening assertions, disabling tests, or using `continue-on-error`.

- I choose meaningful unit, integration, smoke, happy-path, failure-path, concurrency, black-box, and white-box cases.
- I check agent routing, provider choices, RAG citations, shared tools, streaming, uploads, spoilers, ownership, and persistent state.
- I cover fiction and nonfiction, characters/events or concepts/arguments, author research, adaptations, and purchase-link evidence.
- I distinguish mocked behavior from real API evidence. An intentionally rejected invalid request is a passing test only when its expected behavior is asserted.
- I run affected checks after changes and the full acceptance suite before release. I retain commands, results, limitations, and the tested revision.
- I record unavailable services as blockers in requirements; I never report an unexecuted check as passed or promise defect-free output.

## Deployment and live verification

I use `https://github.com/Arya-Wadhwani07/book_reader`, with Assignment 2 as its repository root. CI runs on pushes and pull requests; only `main` deploys to the public service.

- I use repository/branch-scoped Workload Identity Federation, Secret Manager, and a dedicated runtime identity.
- I keep Assignment 2 resources separate from Assignment 1.
- I validate the container, deploy the same tested image as a candidate, run live acceptance, promote it, and verify the public URL again.
- I treat a failing live check as a failed release. A smoke test does not replace the full suite.
- I verify cold/warm behavior, actual incremental tokens, unrehearsed queries, source passages, all selected agents/providers, shared web tools, upload isolation, and cross-revision recovery.

I prefer VS Code-integrated browser testing. After its access was rejected, I authorized Chrome only for this Assignment 2 application. I do not inspect unrelated tabs or broaden browser file permissions. I record browser limitations separately from API test evidence.
