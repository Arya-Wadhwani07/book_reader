# Assignment 2 Working Guidelines

## Scope and layout

My working boundary is `CSCI 599/Assignment 2/`, including dependencies, caches, temporary files, test data, and reports. My one-time inspection of Assignment 1's deployment configuration is complete; I do not access that folder again.

- Directory names follow lowercase snake_case, apart from required tool names such as `.github`.
- Submission paths follow the professor's requirements: root `README.md` and `PROCESS_LOG.md`, plus `docs/architecture.md` and `docs/evaluation.md`.
- Other authored Markdown belongs in `agent_docs/`; supplied instructor references stay unchanged in `agent_docs/reference_docs/`.
- These guidelines are read at the start of work rather than relying on root `AGENTS.md` discovery.
- Local activity stays within the assignment folder. GitHub's managed runners and Google Cloud execution are the external services used by my authorized deployment workflow.

## Documentation and decisions

The assignment PDF and supplied references define my grading contract. All unfinished steps and completion checkboxes belong in `agent_docs/requirements.md`.

- My writing stays in first person, with varied sentence openings, short paragraphs, useful bullets, and tables for comparisons.
- Explanations cover concrete choices and results, acknowledge AI assistance, and draw personal reflections from my own experience.
- Assistant-style narration, repetitive “I do” statements, generic learning claims, and stale planning notes do not belong in deliverables.
- Measured results and limitations stay intact; completion needs supporting evidence.
- Material unknowns need clarification, while independent work can continue.

## Chats, ownership, and uploads

My chat design supports multiple saved conversations under one anonymous browser identity, without login/logout. A server-verified `owner_id` identifies that browser, while `session_id` separates its conversations.

- Messages, book context, preferences, citations, and checkpoints persist outside the Cloud Run instance. The cookie identifies the owner; it does not contain the conversation.
- Starting a new chat preserves earlier conversations; deletion requires explicit confirmation.
- Server-side authorization and tests cover isolation, refresh, concurrent sessions, and recovery after instance replacement.
- The interface explains that clearing browser identity removes access and that cross-device recovery is outside the scope.

My supported inputs are English text-based PDF, EPUB, and TXT files within these displayed limits:

| Limit | Policy I enforce |
| --- | --- |
| File size | 25 MB (25,000,000 bytes) |
| PDF length | 500 physical pages |
| EPUB/TXT length | 125,000 words, approximately 500 pages at 250 words per page |
| Extracted input | 250,000 tokens |

Excess or unreadable input receives a clear rejection, never silent truncation. Support claims need substantial 300–400-page fixtures and checks at the 500-page boundary.

## Implementation and isolation

My code should remain simple enough to explain and maintain. Every file, dependency, helper, and import needs a concrete use.

- Unused imports, dead code, duplicate logic, abandoned scaffolding, and commented-out implementations are removed.
- Dependencies are pinned, expected failures handled explicitly, and credentials excluded from source, logs, traces, images, and archives.
- Python runs through `.venv/bin/python` and lint through `.venv/bin/ruff`, without global package installation. My container uses `/app/.venv`, and CI creates its environment inside the checkout.
- `TMPDIR`, pip caches, bytecode, fixtures, and reports stay inside Assignment 2.
- Offline tests use temporary stores, fake credentials, blocked external network access, and outside-write guards. Real service calls are identified separately.
- Every change gets a review for correctness, necessity, ownership boundaries, cost, and rubric coverage.

## Testing and acceptance

My acceptance standard is a nonempty suite with no failures, errors, skips, expected failures, or unexpected passes. I fix the cause of a failure rather than weakening assertions, disabling tests, or using `continue-on-error`.

- Coverage uses meaningful unit, integration, smoke, happy-path, failure-path, concurrency, black-box, and white-box cases.
- Functional checks cover agent routing, provider choices, RAG citations, shared tools, streaming, uploads, spoilers, ownership, and persistent state.
- Product checks span fiction and nonfiction, characters/events or concepts/arguments, author research, adaptations, and purchase-link evidence.
- Mocked behavior stays separate from real API evidence. An intentionally rejected invalid request is a passing test only when its expected behavior is asserted.
- Affected checks run after changes, followed by the full acceptance suite before release. Commands, results, limitations, and the tested revision are retained.
- Unavailable services remain blockers in requirements; unexecuted checks cannot count as passes, and passing tests do not promise defect-free output.

## Deployment and live verification

My repository is `https://github.com/Arya-Wadhwani07/book_reader`, rooted at Assignment 2. CI runs on pushes and pull requests; only `main` deploys to the public service.

- Deployment uses repository/branch-scoped Workload Identity Federation, Secret Manager, and a dedicated runtime identity.
- Assignment 2 resources remain separate from Assignment 1.
- Release order is container validation, deployment of that same image as a candidate, live acceptance, promotion, and another check of the public URL.
- A failing live check means a failed release. A smoke test does not replace the full suite.
- Live verification covers cold/warm behavior, actual incremental tokens, unrehearsed queries, source passages, all selected agents/providers, shared web tools, upload isolation, and cross-revision recovery.

VS Code-integrated testing was my first choice. After its access was rejected, I authorized Chrome only for this Assignment 2 application. I do not inspect unrelated tabs or broaden browser file permissions. I record browser limitations separately from API test evidence.
