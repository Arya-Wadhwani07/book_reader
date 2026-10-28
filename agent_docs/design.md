# Book Companion Design System

A warm background, simple controls, and a generous text area reflect what I wanted from this interface: a comfortable place to read. Sources and agent activity sit close to the answer, making its evidence easy to inspect. My implementation and test status is recorded in [requirements.md](requirements.md).

## Assignment constraints

My design follows the [assignment description](../docs/Assignment_2_Description%20%281%29.pdf) and [supplied frontend reference](reference_docs/frontend_vibecode_prompt.md): FastAPI-served vanilla HTML/CSS/JavaScript, actual POST SSE streaming, per-turn agent/provider/reason, inspectable activity, and original-source citations. My colors and typography are my design choices, not professor-mandated styling.

## Visual tokens

| Token | Value | Use |
| --- | --- | --- |
| `--canvas` | `#F7F6F2` | Warm page background |
| `--surface` | `#FFFFFF` | Controls and reading surfaces |
| `--text` | `#202825` | Primary text |
| `--muted` | `#59655F` | Supporting labels |
| `--accent` | `#245C46` | Primary actions, links, and focus |
| `--border` | `#D6DDD7` | Section boundaries |
| `--control` | `#79867D` | Visible control boundaries |
| `--error` | `#A12D35` | Readable error messages |

- System sans-serif for controls; Georgia for answers and passages.
- 16 px base text, 18 px reading text, 1.65 reading line height, and roughly 70-character answer lines.
- 8 px control corners, restrained borders, visible focus rings, and approximately 44 px primary touch targets.
- No downloaded fonts, decorative imagery, simulated typing, or frontend framework build.

## Responsive composition

| Width | Layout |
| --- | --- |
| At least 1200 px | 240 px library rail, reading area, and 300 px evidence rail. |
| 768–1199 px | 220 px library rail, with Sources/Activity below the reading area. |
| Below 768 px | One column, collapsible Library & chats, wrapping controls, and evidence below the answer. |

Routing stays visible for each turn. To avoid obscuring text or conflicting with the mobile keyboard, I chose a non-sticky composer. The layout allows text reflow and respects reduced-motion preferences.

## Reading controls

| Control | Behavior |
| --- | --- |
| Library | Show title, author, and actual ingestion state; I enable ready books only. |
| Book heading | Show the selected title, author/type, and extracted word count when available. |
| Content prompts | Offer Overview, Chapters, Characters & concepts, Events & arguments, Author, Adaptations, and Find a copy as editable questions. I do not automatically generate every view. |
| Depth | Offer Brief, Detailed, and Deep dive; the server receives the actual selection. |
| Spoiler scope | Offer recognized chapter/section boundaries and explicit whole-book access. A source with only Full text requires a deliberate whole-book selection. |
| Composer | Provide multiline input, Send, Stop, Enter-to-send, and Shift+Enter for a newline; I respect input composition. |
| Chats | Provide New chat, saved-chat selection, and separately confirmed deletion. I require stopping an active response before switching context. |

Because nonfiction needs different questions from fiction, my prompts adapt to the selected category. I label web research separately from original book evidence and warn that author/adaptation/edition searches require whole-book scope because external results can reveal plot details.

## Uploads and memory

The upload policy appears before file selection:

- English, text-based PDF, EPUB, and TXT files, up to 25 MB.
- At most 500 physical PDF pages or 125,000 EPUB/TXT words (approximately 500 pages).
- A 250,000-token extraction limit, with explicit rejection rather than silent truncation.
- Visible extraction, indexing, summarization, readiness, or a readable failure reason.

After refresh, the selected chat, book, depth, spoiler scope, answer, and evidence return from my server-side records. One signed browser identity owns multiple isolated chats. Clearing site data removes access; I do not promise cross-device recovery.

## Streamed answer and evidence

My streaming client sends `{query, session_id, turn_id, book_id, depth, spoiler_limit}` to `/api/chat` using POST, then parses complete SSE frames across arbitrary UTF-8/network boundaries.

| Event | Presentation |
| --- | --- |
| `token` | Append actual generated text immediately. |
| `trace` | Show agent, provider/model, tool, reason, and recovery/failure events. |
| `citation` | Deduplicate original-book and web sources. |
| `error` | Mark the response incomplete and retain visible partial text. |
| `done` | Show completion only when the server reports success and unlock the composer. |

Text badges distinguish Agent, Model, Retrieval, and Tool activity without relying on color alone. I retain per-turn evidence through an Inspect control. I open original passages in a native dialog and web links in a separate tab. I resolve recognized inline source identifiers into Source buttons, including alternate bracket styles.

For predictable rendering and interaction, my design uses these rules:

- **Text safety:** Untrusted book/model/web content renders through text nodes, never executable HTML. Unsupported formatting remains readable plain text.
- **Links and sources:** HTTP(S) links use `noopener noreferrer`; Book/Web labels and retrieval timestamps make the evidence type clear.
- **During a response:** Book/depth/scope stay locked, and overlapping submissions are blocked. Stop cancels the backend request and aborts the browser stream.
- **Retry:** The question stays available, but another paid call needs an explicit retry.
- **Scrolling:** Moving upward pauses auto-follow; Jump to latest returns to the response.

## Accessibility and response states

Accessibility is part of my interface structure: semantic landmarks, labelled controls, keyboard-operable disclosures, a skip link, native dialog focus, and polite status announcements. Text accompanies color, while announcements avoid reading every token. My evaluation report records the layouts and contrast pairs checked against WCAG targets.

Distinct messages cover no selection, processing, no evidence, partial specialist failure, provider recovery, incomplete streams, and successful completion. I keep deployment/storage details in the activity view and technical documentation. I do not promise lossless summaries, perfect factuality, or guaranteed retailer stock.
