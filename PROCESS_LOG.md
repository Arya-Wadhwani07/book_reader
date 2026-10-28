# AI tools used

I used OpenAI Codex to help plan, implement, debug, test, and document this project. In the application, I used GPT-6 Luna for planning and extraction, NVIDIA Nemotron for ordinary answers, and Claude Sonnet 5 for deep analysis. I record exact model IDs and dependency versions in the repository.

# Development narrative

I expanded my book summarizer into a reading companion with a supervisor and three specialists: Research, Summary, and Data.

- With Codex's help, I fixed HTTPS-origin rejection, a missing ingestion permission, and Unicode corruption at token boundaries.
- I added off-topic routing and visible Summary inputs after reviewing the instructor's clarifications.

# Verification narrative

I kept offline tests separate from live API checks so mocked responses would not count as working integrations.

- I checked citations, private uploads, cancellation, shared Tavily calls, and saved-answer recovery through another cloud revision.
- I retained imperfect RAGAS scores and the failed stress run before the concurrency fix. My pipeline checks both candidate and public deployments.

# What I learned that AI tools could not do for me

I learned that I had to define the boundaries and judge the results myself; AI could help implement those choices but could not make them on my behalf.

- I had to specify folder boundaries, upload limits, and repository structure; vague requests left too much for the tool to assume. Repeated review and testing helped catch mistakes.
- Authentication approvals made me decide which access was appropriate instead of allowing the tool to proceed unchecked.
- I learned how supervisor delegation, Pinecone retrieval, RAGAS metrics, and asynchronous FastAPI fit together. AI could explain these, but I had to develop my own understanding of what each component did and what the test results actually demonstrated.
