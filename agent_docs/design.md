# My Book Companion Design System

I propose a quiet, reading-first interface with warm neutral surfaces, clear typography, and visible evidence. I define design rules here; I track implementation and verification only in [requirements.md](requirements.md).

## My source boundaries

| My source | My design constraint |
| --- | --- |
| [Assignment description](../docs/Assignment_2_Description%20%281%29.pdf), §§2.6, 4.3, 7.2 | I provide FastAPI-served chat, actual SSE token streaming, visible agent/provider routing with reasons, inspectable orchestration traces, and linked citations. |
| [Professor's frontend prompt](reference_docs/frontend_vibecode_prompt.md) | I adopt vanilla HTML/CSS/JS, POST streaming, the five named events, separate trace/citation panels, distinct trace badges, submit locking, and Reset. |
| [Professor's supporting documents](requirements.md#my-source-inventory-and-interpretation) | I preserve their provider, retrieval, persistence, sharing, and evaluation constraints; I do not infer a prescribed color palette or typography from them. |
| [My architecture](../docs/architecture.md) | I reflect the three specialists, curated library/uploads, fiction/nonfiction views, background ingestion, and separation of book evidence from web research. |

I choose the visual tokens below; I do not present them as professor-specified styling. I use the permitted vanilla frontend path, without React, Vue, Angular, Svelte, a Node build step, or `node_modules` in my runtime image.

## My visual foundations

| My token | My value | My use |
| --- | --- | --- |
| `--color_canvas` | `#F7F6F2` | I use a warm page background. |
| `--color_surface` | `#FFFFFF` | I use white reading and input surfaces. |
| `--color_text` | `#202825` | I use dark primary text. |
| `--color_muted` | `#59655F` | I use readable secondary labels. |
| `--color_accent` | `#245C46` | I use forest green for primary actions, links, and focus. |
| `--color_accent_hover` | `#194533` | I darken primary actions on hover. |
| `--color_border` | `#D6DDD7` | I use subtle decorative dividers. |
| `--color_control_border` | `#79867D` | I give inputs and outlined controls a stronger boundary. |
| `--color_info` | `#285E8E` | I identify model-routing information. |
| `--color_tool` | `#66508C` | I identify external tool activity. |
| `--color_warning` | `#875713` | I label partial results or delayed processing. |
| `--color_error` | `#A12D35` | I identify failures with text and an icon. |

- I use system sans-serif for navigation/controls and `Georgia, serif` for long-form answers; I require no downloaded fonts.
- I use 16 px body/input text, 18 px reading text with 1.65 line height, 14 px supporting labels, and 24–32 px headings.
- I limit answer text to approximately 70 characters per line and retain readable zoom/reflow.
- I use a 4/8/12/16/24/32/48 px spacing scale, 8 px control corners, 12 px card corners, and 1 px borders.
- I use one filled primary action per interaction area, restrained outlines elsewhere, and no decorative gradients or large shadows.
- I use short 120–160 ms control transitions, no simulated typing effect, and no essential animation.

## My page composition

```text
Header: Book Companion                         Library / Upload / New Chat
Library rail       Reading workspace           Evidence rail
Search and books   Book title + content views   Sources panel
Upload progress    Depth + spoiler controls    Activity panel
                   Conversation + answer      Agent/provider/reason
                   Question composer + Reset
```

| My viewport | My layout rule |
| --- | --- |
| Desktop, ≥1200 px | I use a 240 px library rail, flexible reading area, and 300 px evidence rail within a 1440 px shell. |
| Tablet, 768–1199 px | I put the library in a drawer and stack Sources/Activity beneath the answer. |
| Mobile, <768 px | I use one column, a library button, wrapping controls, and separate Sources/Activity disclosures beneath each answer. |

I keep a compact routing summary visible with every turn at every width. I make full traces and citations available without leaving the page. I avoid a sticky composer that hides content or conflicts with the mobile keyboard.

## My book navigation

| My view | My content rule |
| --- | --- |
| Overview | I show the selected book/edition, a concise summary, and adjustable depth. |
| Chapters | I show chapter summaries with expandable evidence and progress through the book. |
| Characters / Concepts | I show character sketches/relationships for fiction and concepts, arguments, or relevant real people for nonfiction. |
| Events / Arguments | I show major events, chronology, causes, or a nonfiction argument outline. |
| Author | I distinguish sourced biography from claims contained in the book. |
| Adaptations | I identify evidenced film/TV adaptations, distinguish related works, and show source links. |
| Buy | I show verified retailer links, edition, format, and retrieval date; I do not invent availability or prices. |

I limit my initial input scope to English PDF, EPUB, and TXT. I restore the saved-chat list, active conversation, and its book context after refresh from server-side state. I support multiple isolated chats under the same anonymous browser identity without login/logout.

I keep Library and Upload as entry points into the same reading workspace. I show “Not applicable” or “No supported result found” where appropriate instead of fabricating content. I keep technical storage and deployment details out of these reading views.

### My visible upload message

I display this helper text beside Upload:

> English PDF, EPUB or TXT · Up to 25 MB per file. PDFs: up to 500 pages. EPUB/TXT: up to 125,000 words (approximately 500 pages). An extracted-text limit of 250,000 tokens also applies. Text-based files only.

I show the measured page/word count after extraction and name the exact limit if rejected. I never advertise that every 500-page file is supported regardless of size or text density. I label saved chats as available in this browser and explain that clearing site data can remove access.

## My reusable components

| My component | My behavior |
| --- | --- |
| Book item | I display title, author, fiction/nonfiction label, edition, and readiness state; I allow selection only when its required content is ready. |
| Upload control | I provide a labelled file picker plus optional drag-and-drop and show the exact limit message below before selection. |
| Chat list | I show saved chat titles, New Chat, and the active selection; I restore each chat's own messages, book, depth, and spoiler settings. |
| Progress row | I show actual stages: uploading, extracting, indexing, summarizing, ready, or failed; I show percentages only when measured. |
| Depth control | I offer Brief, Detailed, and Deep Dive; I retain the choice for the selected book. |
| Spoiler control | I offer “Up to chapter…” and explicit “Whole book”; I require a deliberate whole-book choice before revealing the ending. |
| Composer | I provide a labelled multiline input, Send, Stop while active, and Reset; I support Enter to send and Shift+Enter for a newline, respecting text composition. |
| Answer | I render readable sections incrementally, distinguish interpretation, and preserve a partial answer after an interrupted stream. |
| Citation | I use numbered inline links opening the Sources panel at the matching document/chapter/page-or-location/chunk excerpt. |
| Source card | I label Book or Web, identify the source/edition, and provide a valid passage or external link; I timestamp web retrieval. |
| Routing summary | I show every invoked agent and provider/model with the actual reason; I retain fallback decisions rather than replacing their history. |
| Activity row | I show event type, agent, state transition or tool, status, and available elapsed time in chronological order. |
| Status message | I combine plain-language text with an icon; I offer a relevant retry or edit action without exposing raw stack traces. |

I use labels with distinct badge colors: **Agent** (`agent_route`, green), **Model** (`llm_route`, blue), **Retrieval** (`rag_retrieval`, neutral), and **Tool** (`mcp_tool_call`, purple). I retain readable labels so meaning never depends on color alone.

## My streaming and interaction contract

I serve one HTML page and its local static assets through FastAPI. I POST JSON `{query, session_id, turn_id, book_id, depth, spoiler_limit}` to `/api/chat`; I use `session_id` as the selected chat ID and derive the owning browser identity from its signed cookie. I consume `text/event-stream` through `fetch()` and `ReadableStream`, and parse complete SSE frames across arbitrary network chunks.

| My event | My rendering rule |
| --- | --- |
| `token` | I append actual generated answer text immediately, without waiting for the whole answer. |
| `trace` | I update Activity and the per-turn routing summary from real backend events. |
| `citation` | I add a deduplicated source card and resolve its matching inline reference. |
| `error` | I show the failure and retain any useful partial answer, clearly marked incomplete. |
| `done` | I finalize the turn according to its success status and restore the composer controls. |

- I disable Send while a turn is active and expose Stop; I do not permit overlapping submissions from the same composer.
- I allow switching to another saved chat after stopping an active response; each chat restores its own context.
- I keep the active turn's book, depth, and spoiler scope fixed; I require stopping it before changing that context.
- I distinguish “Searching sources” progress from answer tokens and avoid fake progress or fake time-to-first-token claims.
- I stop following the stream when the reader scrolls upward and show “Jump to latest” instead of pulling the viewport down.
- I treat EOF without successful completion as interrupted, release disabled controls, and expose Retry without silently issuing another paid request.
- I make Stop abort the stream and request backend cancellation; I show “Stopping” until acknowledged and preserve partial output.
- I make New Chat/Reset stop the active turn, clear the active workspace, and create a fresh chat under the same browser identity. Previous chats and uploaded books remain accessible; deleting a chat requires a separate confirmation.
- I clear previous turn evidence from the active panels when starting a new turn but keep it accessible with its original message.

## My empty, loading, and failure states

| My state | My response |
| --- | --- |
| First visit | I show the curated library, one clear Upload action, and a short explanation of book-grounded answers. |
| No selected book | I ask for a library selection or upload before book-specific questions. |
| Large upload | I retain visible progress while allowing browsing of ready books. |
| Unsupported/scanned file | I identify the limitation and suggest a supported text-based file without claiming successful ingestion. |
| No evidence or web match | I state what could not be established and keep unsupported claims out of the answer. |
| Cold start or slow provider | I show an honest waiting status and Stop; I avoid an unexplained blank panel. |
| Worker/provider failure | I label partial results and any actual fallback; I never label an incomplete answer “Complete.” |
| Connection loss | I preserve the visible answer, mark interruption, and offer an explicit retry. |

## My accessibility and content rules

- I target at least 4.5:1 contrast for normal text and 3:1 for functional control boundaries/focus; I check actual foreground/background combinations.
- I use semantic headings, buttons, labels, landmarks, keyboard-operable disclosures, and visible focus rings. I provide approximately 44 px touch targets.
- I give drawers proper focus entry/return and Escape handling; I make all actions usable without hover.
- I announce stage changes politely rather than every token; I keep the final answer available to assistive technology without repeatedly interrupting reading.
- I support reduced motion, 200% zoom, and narrow layouts without page-level horizontal scrolling.
- I render model/book/web content as safe text or sanitized formatting, never executable HTML; I restrict citation/purchase links to safe web URLs.
- I use short product labels such as “Ask about this book,” “Show sources,” and “View hardcover.” I reserve implementation terms for the requested trace details.
- I write my documentation in first person; I keep product microcopy direct and reader-facing.

## My design review

| My risk | My decision |
| --- | --- |
| An overloaded dashboard | I prioritize reading and reveal detailed evidence progressively while keeping routing visible. |
| Hidden grading evidence | I provide distinct Sources and Activity panels and preserve inspectable per-turn history. |
| Misleading completeness | I offer adjustable depth and cited detail without a “nothing omitted” promise. |
| Expensive automatic actions | I load external research on intent and avoid generating every section just because a book is opened. |
| Spoiler leakage | I carry the selected boundary into evidence retrieval and label or suppress incompatible external results. |
| A polished mockup mistaken for a working product | I assess the implemented UI through real streamed responses and live browser checks; this document is a specification. |
