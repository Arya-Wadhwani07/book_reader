# My Assignment 2 Working Guidelines

## My scope

I apply these rules to all work in this project and every directory beneath it. My project root is `CSCI 599/Assignment 2/`. I keep source, documentation, environments, caches, temporary files, test outputs, and repository metadata inside that root. I use a project-local `.venv` and `.cache` and set tool cache/temp locations explicitly when necessary.

I have completed my one-time authorized read of Assignment 1's deployment configuration. That exception is closed. I do not revisit Assignment 1 or inspect other projects. I retain the non-secret deployment facts in `agent_docs/requirements.md`. I keep remote CI files within the repository checkout where configurable; GitHub's managed runner/tool installation and Google Cloud's managed execution are the external services explicitly required by my deployment workflow.

## My directory and documentation rules

I name project-owned directories in lowercase snake_case, such as `agent_docs` and `reference_docs`. I preserve required tool-owned names such as `.github` and generated dependency directories. I keep every authored Markdown file under `agent_docs/`, except root `README.md`. I also store supplied Markdown references under `agent_docs/reference_docs/`, preserving their contents. I use `agent_docs/agents.md` as my working guidelines and explicitly read it at task start; I do not rely on root `AGENTS.md` discovery.

## My source of truth and documentation

I use the supplied assignment PDF and supporting documents as my grading contract. I track all unfinished work, open decisions, implementation steps, and completion checkboxes exclusively in `agent_docs/requirements.md`. This file contains standing rules, not a second backlog.

I write original documentation in first person. I describe actual behavior and measured results accurately. I preserve supplied instructor documents. I update my requirements when a decision changes and mark completion only with reviewed evidence. I ask when material information is missing, but continue independent authorized work.

## My code standard

I choose the simplest readable implementation that satisfies the requirement. I create a file, function, class, dependency, configuration value, or abstraction only when it has an actual consumer or concrete verification purpose. I keep functions focused and names clear.

I remove unused imports, variables, unreachable code, abandoned implementations, duplicate logic, commented-out code, and unnecessary lines. I do not add speculative scaffolding, empty placeholder modules, or unused dependencies. I use linting to catch unused imports and variables and review manually for unused abstractions and unnecessary files.

I pin dependencies exactly, handle expected failures explicitly, and keep credentials outside source, logs, traces, images, and archives. I do not suppress failures merely to make a check green. I review every change for correctness, simplicity, scope, security, and rubric coverage.

## My testing and acceptance standard

I require every test in my acceptance suite to pass, with zero failures, errors, skipped tests, expected failures, unexpected passes, or empty test collections. I do not use `continue-on-error`, blanket exception handlers, weakened assertions, disabled tests, or artificial success responses to bypass a failed check. If a required external service or credential is unavailable, I record the blocker only in my requirements and do not call the acceptance run passed.

I use meaningful unit, integration, smoke, happy-path, failure-path, sandbox, black-box, white-box, regression, and end-to-end tests as appropriate. I test routing across actual providers, specialist behavior, RAG citations, live retrieval, shared MCP/A2A behavior, streaming, input handling, concurrency/session isolation, and conditional durable-state recovery. I test both fiction and nonfiction, curated books and supported uploads, characters/events where applicable, author information, adaptations, and purchase-link evidence.

I isolate deterministic tests from paid/network calls without misrepresenting mocked tests as live verification. I keep all fixtures and generated test files within the project. I test failure handling intentionally; an expected application error correctly asserted by a test is a passing test, not an exception to my acceptance standard.

I run relevant checks after each change and the complete acceptance suite before release/submission. I preserve evidence of commands, results, limitations, and the tested revision. I never invent coverage percentages, RAGAS scores, latencies, costs, or successful deployments. Passing tests reduces risk; I do not promise that software is defect-free.

## My continuous integration and deployment standard

I use `https://github.com/Arya-Wadhwani07/book_reader` with Assignment 2 as the repository root. I run CI on pushes and pull requests. I deploy from `main` only after all required local/CI gates pass; feature branches do not replace my public submission service.

I authenticate GitHub Actions to Google Cloud using Workload Identity Federation scoped to my repository and deployment branch. I keep runtime API credentials in Secret Manager and use a dedicated runtime identity. I keep Assignment 2's Cloud Run service separate from Assignment 1.

I validate the built container and the deployed candidate, check a real streamed RAG answer with routing traces and citations, and promote only a passing candidate. I check the public URL again after promotion. I treat any failing live check as a failed release, not a warning. My smoke check supplements my complete live acceptance suite; it does not replace it.

## My live submission verification

I test the actual public Cloud Run URL in a browser and through its API. I verify cold and warm requests, unrehearsed reasonable queries, visible incremental tokens, citations, agent/provider rationale, all selected specialists and providers, current web retrieval, failure handling, and uploaded-book isolation. If I claim durable state, I verify instance-replacement recovery.

I require the complete live suite to pass on the submitted revision, not merely on localhost or an earlier deployment. I fix failures and rerun affected checks before submission. I retain my live URL and measured evidence and confirm that the frontend connects to the deployed backend.
