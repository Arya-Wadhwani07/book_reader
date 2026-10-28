# AI tools used

OpenAI Codex helped me plan, implement, debug, test, and document this project. My application uses GPT-6 Luna for planning and extraction, NVIDIA Nemotron for ordinary answers, and Claude Sonnet 5 for deep analysis. Exact model IDs and dependencies are recorded in the repository.

# Development narrative

My book summarizer grew into a reading companion with a supervisor and three specialists: Research, Summary, and Data.

- Integration exposed HTTPS-origin rejection, a missing ingestion permission, and Unicode corruption. With Codex's help, I fixed these and added regression tests.
- Instructor clarifications prompted off-topic routing and visible Summary inputs.

# Verification narrative

Mocked responses could not prove my integrations worked, so offline and live tests stayed separate.

- Checks covered citations, uploads, cancellation, shared Tavily calls, and saved-answer recovery across revisions.
- My evidence retains imperfect RAGAS scores and the failed stress run. Release checks covered candidate and public deployments.

# What I learned that AI tools could not do for me

AI helped implement my choices, but setting boundaries and judging the results remained my responsibility.

- Clear folder boundaries, upload limits, and repository structure reduced assumptions; repeated review helped catch mistakes.
- Authentication approvals required my judgment about appropriate access.
- Understanding delegation, Pinecone, RAGAS, and asynchronous FastAPI meant making sense of the components myself, not simply accepting generated code.
- Cold and warm measurements showed me why one timing is misleading. Time to first token also differs from the wait for a complete answer.
- Deep analysis took longer and cost more than brief answers, making response depth a practical tradeoff in my design.
- Concurrent reads exposed 429 errors that individual requests missed. The passing rerun supported my concurrency adjustment, not a claim of unlimited capacity.
