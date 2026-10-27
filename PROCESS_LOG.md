# AI tools used

I used OpenAI Codex to help inspect the assignment, design the application, implement code, debug failures, and review test evidence. My application uses OpenAI GPT-6 Luna for planning and structured extraction, NVIDIA Nemotron for ordinary answers, and Anthropic Claude Sonnet 5 for deep analysis. I record exact dependency versions and model identifiers in my requirements and architecture files. I distinguish coding assistance from the models executing inside my deployed application.

# Development narrative

I developed a book companion with a LangGraph supervisor, three specialists, original-source retrieval, private uploads, and persistent anonymous chats. Integration exposed HTTPS-origin rejection, missing ingestion-job permissions, Unicode chunk corruption, provider interruptions, and truncated answers. I fixed these defects and preserved regression cases. Instructor clarifications led me to add explicit off-topic redirects, actual supervisor-hop traces, Summary input evidence, and a reproducible curated corpus snapshot. I kept the implementation inside my assignment directory and used a project-local Python environment.

# Verification narrative

I separated isolated unit, integration, concurrency, and failure tests from paid live-service checks. I verified real streamed answers, source passages, multiple providers, shared Tavily MCP calls, upload isolation, and saved-state recovery across cloud revisions. I ran the four required RAGAS metrics and retained imperfect scores rather than selecting only favorable answers. My deployment pipeline tests a candidate before promotion and checks the public URL afterward. I report browser-permission limitations and infrastructure billing uncertainty honestly.

# What I learned that AI tools could not do for me
