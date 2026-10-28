# Book Companion Design System

I wanted the interface to feel like a place to read, so I chose a warm background, simple controls, and a generous text area. I keep sources and agent activity close to the answer so I can check how it was produced. I record implementation and test status in [requirements.md](requirements.md).

## Assignment constraints

I follow the [assignment description](../docs/Assignment_2_Description%20%281%29.pdf) and [supplied frontend reference](reference_docs/frontend_vibecode_prompt.md): FastAPI-served vanilla HTML/CSS/JavaScript, actual POST SSE streaming, per-turn agent/provider/reason, inspectable activity, and original-source citations. My colors and typography are my design choices, not professor-mandated styling.

## Visual tokens

| Token | Value | Use |
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

## Responsive composition

| Width | Layout |
| --- | --- |
| At least 1200 px | I place a 240 px library rail beside the reading area and a 300 px evidence rail. |
| 768–1199 px | I retain a 220 px library rail and put Sources/Activity below the reading area. |
| Below 768 px | I use one column, a collapsible Library & chats panel, wrapping controls, and evidence disclosures below the answer. |

I keep routing visible per turn. I avoid a sticky composer that obscures text or conflicts with the mobile keyboard. I respect reduced-motion preferences and allow text reflow.

## Reading controls

| Control | Behavior |
| --- | --- |
| Library | I show title, author, and actual ingestion state; I enable ready books only. |
| Book heading | I show the selected title, author/type, and extracted word count when available. |
| Content prompts | I offer Overview, Chapters, Characters & concepts, Events & arguments, Author, Adaptations, and Find a copy as editable questions. I do not automatically generate every view. |
| Depth | I offer Brief, Detailed, and Deep dive; the server receives the actual selection. |
| Spoiler scope | I offer recognized chapter/section boundaries and explicit whole-book access. A source with only Full text requires a deliberate whole-book selection. |
| Composer | I provide multiline input, Send, Stop, Enter-to-send, and Shift+Enter for a newline; I respect input composition. |
| Chats | I provide New chat, saved-chat selection, and separately confirmed deletion. I require stopping an active response before switching context. |

I adapt prompts to fiction/nonfiction rather than claiming every book has fictional characters. I label web research separately from original book evidence and warn that author/adaptation/edition searches require whole-book scope because external results can reveal plot details.

## Uploads and memory

I show the upload policy before file selection:

- I accept English, text-based PDF, EPUB, and TXT files up to 25 MB.
- I cap PDFs at 500 physical pages and EPUB/TXT at 125,000 words (approximately 500 pages).
- I cap extracted input at 250,000 tokens and reject excess input without silent truncation.
- I show extraction, indexing, summarization, readiness, or a readable failure reason.

I restore the selected chat, book, depth, spoiler scope, answer, and evidence from server-side records after refresh. One signed browser identity owns multiple isolated chats. Clearing site data removes access; I do not promise cross-device recovery.

## Streamed answer and evidence

I POST `{query, session_id, turn_id, book_id, depth, spoiler_limit}` to `/api/chat` and parse complete SSE frames across arbitrary UTF-8/network boundaries.

| Event | Presentation |
| --- | --- |
| `token` | I append actual generated text immediately. |
| `trace` | I show agent, provider/model, tool, reason, and recovery/failure events. |
| `citation` | I deduplicate original-book and web sources. |
| `error` | I mark the response incomplete and retain visible partial text. |
| `done` | I show completion only when the server reports success and unlock the composer. |

I label activity as Agent, Model, Retrieval, or Tool, using text as well as color. I retain per-turn evidence through an Inspect control. I open original passages in a native dialog and web links in a separate tab. I resolve recognized inline source identifiers into Source buttons, including alternate bracket styles.

I keep rendering and interaction predictable:

- I display untrusted book/model/web text through text nodes, never executable HTML. Unsupported formatting remains readable plain text.
- I restrict links to HTTP(S), use `noopener noreferrer`, label Book/Web evidence, and show web retrieval timestamps.
- I lock book/depth/scope and prevent overlapping submissions during a response. Stop cancels the backend request and aborts the browser stream.
- I preserve the question for an explicit retry rather than silently repeating a paid call.
- I stop auto-follow when the reader scrolls upward and provide Jump to latest.

## Accessibility and response states

I use semantic landmarks, labelled controls, keyboard-operable disclosures, a skip link, native dialog focus, and polite status announcements. I use text alongside color and do not announce every token. I use WCAG contrast targets for text and controls; my evaluation report records the layouts and contrast pairs actually checked.

I distinguish no selection, processing, no evidence, partial specialist failure, provider recovery, incomplete stream, and successful completion. I keep deployment/storage details in the activity view and technical documentation. I do not promise lossless summaries, perfect factuality, or guaranteed retailer stock.
