# My Book Companion Design System

I use a quiet reading interface with warm surfaces, restrained controls, and visible evidence. I track implementation and verification only in [requirements.md](requirements.md).

## My assignment constraints

I follow the [assignment description](../docs/Assignment_2_Description%20%281%29.pdf) and [supplied frontend reference](reference_docs/frontend_vibecode_prompt.md): FastAPI-served vanilla HTML/CSS/JavaScript, actual POST SSE streaming, per-turn agent/provider/reason, inspectable activity, and original-source citations. My colors and typography are my design choices, not professor-mandated styling.

## My visual tokens

| My token | My value | My use |
| --- | --- | --- |
| `--canvas` | `#F7F6F2` | I use a warm background. |
| `--surface` | `#FFFFFF` | I separate controls and reading surfaces. |
| `--text` | `#202825` | I use dark primary text. |
| `--muted` | `#59655F` | I distinguish supporting labels. |
| `--accent` | `#245C46` | I identify primary actions, links, and focus. |
| `--border` | `#D6DDD7` | I separate sections. |
| `--control` | `#79867D` | I give controls a visible boundary. |
| `--error` | `#A12D35` | I identify errors with readable text. |

- I use system sans-serif for controls and Georgia for answers and passages.
- I use 16 px base text, 18 px reading text, 1.65 reading line height, and roughly 70-character answer lines.
- I use 8 px control corners, restrained borders, visible focus rings, and approximately 44 px primary touch targets.
- I use no downloaded fonts, decorative imagery, simulated typing, or frontend framework build.

## My responsive composition

| My width | My layout |
| --- | --- |
| At least 1200 px | I place a 240 px library rail beside the reading area and a 300 px evidence rail. |
| 768–1199 px | I retain a 220 px library rail and put Sources/Activity below the reading area. |
| Below 768 px | I use one column, a collapsible Library & chats panel, wrapping controls, and evidence disclosures below the answer. |

I keep routing visible per turn. I avoid a sticky composer that obscures text or conflicts with the mobile keyboard. I respect reduced-motion preferences and allow text reflow.

## My reading controls

| My control | My behavior |
| --- | --- |
| Library | I show title, author, and actual ingestion state; I enable ready books only. |
| Book heading | I show the selected title, author/type, and extracted word count when available. |
| Content prompts | I offer Overview, Chapters, Characters & concepts, Events & arguments, Author, Adaptations, and Find a copy as editable questions. I do not automatically generate every view. |
| Depth | I offer Brief, Detailed, and Deep dive; the server receives the actual selection. |
| Spoiler scope | I offer recognized chapter/section boundaries and explicit whole-book access. A source with only Full text requires a deliberate whole-book selection. |
| Composer | I provide multiline input, Send, Stop, Enter-to-send, and Shift+Enter for a newline; I respect input composition. |
| Chats | I provide New chat, saved-chat selection, and separately confirmed deletion. I require stopping an active response before switching context. |

I adapt prompts to fiction/nonfiction rather than claiming every book has fictional characters. I label web research separately from original book evidence and warn that author/adaptation/edition searches require whole-book scope because external results can reveal plot details.

## My uploads and memory

I display English PDF/EPUB/TXT, 25 MB, 500 PDF pages, 125,000 EPUB/TXT words (approximately 500 pages), and 250,000 extracted tokens before upload. I require text-based files and show extraction/indexing/summarization/readiness or a failure reason. I never silently truncate a book.

I restore the chat, book, depth, spoiler scope, answer, and evidence after refresh using server-side records. My signed browser identity owns multiple isolated chats without login. I explain that clearing site data removes access; I do not promise cross-device recovery.

## My streamed answer and evidence

I POST `{query, session_id, turn_id, book_id, depth, spoiler_limit}` to `/api/chat` and parse complete SSE frames across arbitrary UTF-8/network boundaries.

| My event | My presentation |
| --- | --- |
| `token` | I append actual generated text immediately. |
| `trace` | I show agent, provider/model, tool, reason, and recovery/failure events. |
| `citation` | I deduplicate original-book and web sources. |
| `error` | I mark the response incomplete and retain visible partial text. |
| `done` | I show completion only when the server reports success and unlock the composer. |

I distinguish Agent, Model, Retrieval, and Tool with text badges and color. I retain per-turn evidence through an Inspect control. I open original passages in a native dialog and web links in a separate tab. I resolve recognized inline source identifiers into Source buttons, including alternate bracket styles.

I render untrusted model/book/web content through text nodes, not executable HTML. I restrict external links to HTTP(S), use `noopener noreferrer`, label Book/Web, and show web retrieval timestamps. I leave unsupported formatting as readable text rather than introducing an unsafe HTML renderer.

I disable overlapping submission and freeze book/depth/scope during a turn. Stop requests backend cancellation and aborts the browser stream. I preserve the question for an explicit retry instead of silently repeating a paid request. I stop auto-follow when the reader scrolls upward and provide Jump to latest.

## My accessibility and honest states

I use semantic landmarks, labelled controls, keyboard-operable disclosures, a skip link, native dialog focus, and polite status announcements. I use text alongside color and do not announce every token. I target WCAG text/control contrast and verify actual layouts separately from this specification.

I distinguish no selection, processing, no evidence, partial specialist failure, provider recovery, incomplete stream, and successful completion. I keep deployment/storage details in the activity view and technical documentation. I do not promise lossless summaries, perfect factuality, or guaranteed retailer stock.
