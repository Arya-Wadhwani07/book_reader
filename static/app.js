"use strict";
const $ = (id) => document.getElementById(id);
const state = { books: [], chats: [], chat: null, book: null, active: false, controller: null, follow: true };

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try { message = (await response.json()).detail || message; } catch { /* I retain the HTTP error. */ }
    throw new Error(typeof message === "string" ? message : "Please check your input.");
  }
  return response.status === 204 ? null : response.json();
}
function jsonOptions(body) { return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }; }
function notice(message) { $("notice").textContent = message || ""; }
function button(text, action) { const node = document.createElement("button"); node.textContent = text; node.addEventListener("click", () => Promise.resolve(action()).catch((e) => notice(e.message))); return node; }
function clearEvidence() { $("sources").replaceChildren(); $("activity").replaceChildren(); $("source-count").textContent = "0"; }

function renderBooks() {
  const search = $("book-search").value.toLowerCase();
  $("books").replaceChildren();
  for (const book of state.books.filter((b) => `${b.title} ${b.author || ""}`.toLowerCase().includes(search))) {
    const node = button("", () => selectBook(book));
    const title = document.createElement("strong"); title.textContent = book.title;
    const subtitle = document.createElement("span"); subtitle.textContent = `${book.author || "Uploaded book"} · ${book.status}`;
    node.append(title, subtitle); node.disabled = book.status !== "ready" || state.active;
    node.classList.toggle("selected", state.book?.id === book.id); $("books").append(node);
    if (book.status === "failed" && book.owner_id !== "public") {
      const retry = button(`Retry ${book.title}`, async () => {
        retry.disabled = true;
        try { await api(`/api/books/${encodeURIComponent(book.id)}/retry`, jsonOptions({})); state.books = await api("/api/books"); renderBooks(); }
        finally { retry.disabled = false; }
      });
      retry.disabled = state.active; $("books").append(retry);
    }
  }
  if (!state.books.length) $("books").textContent = "No books yet. Add a text-based book to begin.";
}
function renderChats() {
  $("chats").replaceChildren();
  for (const chat of state.chats) {
    const node = button(chat.title, () => selectChat(chat.id));
    node.classList.toggle("selected", state.chat?.id === chat.id); node.disabled = state.active; $("chats").append(node);
  }
}
function showBook(book) {
  state.book = book;
  $("category-control").hidden = !book || book.owner_id === "public";
  $("category").value = book?.kind || "Book";
  $("book-title").textContent = book?.title || "Make room for a good book.";
  $("book-author").textContent = book ? `${book.author || "Unknown author"} · ${book.kind || "Book"}${book.words ? ` · ${book.words.toLocaleString()} words` : ""}` : "Choose a book from the library or bring your own.";
  $("spoiler").replaceChildren();
  for (const chapter of book?.chapters || [{ number: 1, title: "Chapter 1" }]) {
    const option = document.createElement("option"); option.value = chapter.number; option.textContent = `Through ${chapter.title}`; $("spoiler").append(option);
  }
  if (book?.chapters?.length === 1 && book.chapters[0].title === "Full text") { $("spoiler").replaceChildren(); const choice = document.createElement("option"); choice.value = ""; choice.textContent = "Choose scope — no chapter markers"; $("spoiler").append(choice); }
  const all = document.createElement("option"); all.value = "all"; all.textContent = "Whole book — includes the ending"; $("spoiler").append(all);
  renderBooks(); setActive(state.active);
  if (!state.active) $("turn-status").textContent = book ? "Ready for your question." : "Select a ready book to begin.";
}
async function selectBook(book) {
  if (state.active) return;
  if (state.chat?.book_id && state.chat.book_id !== book.id) await newChat();
  showBook(book);
  $("library-panel").classList.remove("is-open"); $("toggle-library").setAttribute("aria-expanded", "false");
}
async function newChat(force = false) {
  if (state.active && !force) return;
  const chat = await api("/api/chats", jsonOptions({}));
  state.chats.unshift(chat); state.chat = chat;
  $("conversation").replaceChildren(); clearEvidence(); renderChats();
  localStorage.setItem("active_chat", chat.id); $("query").focus();
}
async function selectChat(id) {
  if (state.active) return;
  const data = await api(`/api/chats/${id}`);
  state.chat = data.chat;
  showBook(state.books.find((b) => b.id === data.chat.book_id) || null);
  $("depth").value = data.chat.depth;
  $("spoiler").value = data.chat.spoiler_limit === null ? "all" : String(data.chat.spoiler_limit);
  $("conversation").replaceChildren(); clearEvidence();
  for (const turn of data.turns) {
    const view = createTurn(turn.query); view.text = turn.answer;
    clearEvidence();
    for (const event of turn.events) if (event.event !== "token") renderEvent(event.event, event.data, view);
    linkCitations(view);
    if (turn.status !== "complete") view.status.textContent = turn.status === "running" ? "Interrupted or still running" : turn.status;
    const inspect = button("Inspect this answer’s evidence", () => { clearEvidence(); for (const event of turn.events) renderEvent(event.event, event.data, view, true); });
    view.root.append(inspect);
  }
  localStorage.setItem("active_chat", id); renderChats();
}
function linkCitations(view) {
  if (view.renderFrame) cancelAnimationFrame(view.renderFrame);
  view.renderFrame = null;
  view.answer.innerHTML = BookMarkdown.render(view.text, [...view.citations.keys()]);
}
async function openPassage(data) {
  const source = await api(`/api/books/${encodeURIComponent(data.source_id)}/sources/${encodeURIComponent(data.chunk_id)}`);
  $("passage-label").textContent = source.label || source.id;
  $("passage-text").textContent = source.text; $("passage").showModal();
}
function createTurn(query) {
  const root = document.createElement("article"); root.className = "turn";
  const question = document.createElement("div"); question.className = "question"; question.textContent = query;
  const routing = document.createElement("div"); routing.className = "route-summary";
  const models = document.createElement("div"); models.className = "model-chips";
  const details = document.createElement("details"); details.className = "routing-details";
  const heading = document.createElement("summary"); heading.textContent = "How this answer was made";
  const summary = document.createElement("div"); summary.className = "routing-steps";
  details.append(heading, summary); routing.append(models, details);
  const answer = document.createElement("div"); answer.className = "answer";
  const status = document.createElement("div"); status.className = "answer-status"; status.setAttribute("role", "status");
  root.append(question, routing, status, answer); $("conversation").append(root);
  const view = { root, summary, models, status, answer, text: "", citations: new Map(), routeKeys: new Set(), modelKeys: new Set(), renderFrame: null };
  answer.addEventListener("click", (event) => {
    const key = event.target.closest("button[data-source]")?.dataset.source;
    if (key && view.citations.has(key)) openPassage(view.citations.get(key)).catch((e) => notice(e.message));
  });
  return view;
}
function renderRoute(data, view) {
  if (data.type === "llm_route") {
    const key = `${data.provider}:${data.model}`;
    const provider = ({ openai: "OpenAI", anthropic: "Anthropic", nvidia: "NVIDIA" })[data.provider] || data.provider;
    if (!view.modelKeys.has(key)) {
      const chip = document.createElement("span"); chip.className = "model-chip";
      const name = document.createElement("strong"); name.textContent = provider;
      const model = document.createElement("span"); model.textContent = ({ "gpt-6-luna": "GPT-6 Luna", "claude-sonnet-5": "Claude Sonnet 5", "nvidia/nemotron-3-ultra-550b-a55b": "Nemotron 3 Ultra" })[data.model] || data.model; chip.title = data.model;
      chip.append(name, model); view.models.append(chip); view.modelKeys.add(key);
    }
  }
  const key = JSON.stringify([data.type, data.agent, data.task, data.provider, data.model, data.reason]);
  if (view.routeKeys.has(key)) return;
  view.routeKeys.add(key);
  const row = document.createElement("div"); row.className = "routing-step";
  const title = document.createElement("strong");
  const task = ({ plan: "Planning", research: "Research", summary: "Summary", data: "Structured analysis", answer: "Final answer", reduce: "Evidence reduction" })[data.task] || data.task || "Generation";
  title.textContent = data.type === "agent_route" ? `Agent · ${data.agent}` : `${task} · ${data.model}`;
  const reason = document.createElement("span"); reason.textContent = data.reason || "";
  row.append(title, reason); view.summary.append(row);
}
function safeUrl(value) { try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : null; } catch { return null; } }
function renderEvent(event, data, view, evidenceOnly = false) {
  if (event === "token" && !evidenceOnly) {
    view.text += data.text;
    if (!view.renderFrame) view.renderFrame = requestAnimationFrame(() => {
      view.renderFrame = null; linkCitations(view);
      if (state.follow) view.answer.scrollIntoView({ block: "end" }); else $("latest").hidden = false;
    });
  }
  if (event === "trace") {
    const row = document.createElement("div"); row.className = `trace ${data.type || ""}`;
    const badge = document.createElement("span"); badge.className = "badge"; badge.textContent = ({ agent_route: "AGENT", llm_route: "MODEL", rag_retrieval: "RETRIEVAL", mcp_tool_call: "TOOL" })[data.type] || "STATUS";
    const label = document.createElement("div"); label.textContent = [data.agent, data.provider, data.model, data.tool, data.reason || data.message].filter(Boolean).join(" · ");
    row.append(badge, label); $("activity").append(row);
    const details = document.createElement("details");
    const heading = document.createElement("summary"); heading.textContent = "Inspect trace data";
    const payload = document.createElement("pre"); payload.textContent = JSON.stringify(data, null, 2);
    details.append(heading, payload); row.append(details);
    if (!evidenceOnly && ["agent_route", "llm_route"].includes(data.type)) renderRoute(data, view);
    if (state.active) $("turn-status").textContent = data.message || data.reason || "Working with your sources…";
  }
  if (event === "citation") {
    const key = data.chunk_id || data.url;
    if (data.chunk_id) view.citations.set(data.chunk_id, data);
    if ([...$("sources").children].some((n) => n.dataset.key === key)) return;
    const card = document.createElement("div"); card.className = "source-card"; card.dataset.key = key;
    if (data.chunk_id) {
      card.append(button(`${data.label || data.chunk_id} · Book`, () => openPassage(data)));
    } else if (safeUrl(data.url)) {
      const link = document.createElement("a"); link.href = safeUrl(data.url); link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = `${data.title || data.url} · Web`; card.append(link);
      const date = document.createElement("p"); date.textContent = data.retrieved_at ? `Retrieved ${data.retrieved_at}` : "External source"; card.append(date);
    } else return;
    $("sources").append(card); $("source-count").textContent = $("sources").children.length;
  }
  if (event === "error" && !evidenceOnly) view.status.textContent = data.message;
}
function setActive(active) {
  state.active = active;
  for (const id of ["new-chat", "delete-chat", "depth", "spoiler", "upload", "category"]) $(id).disabled = active;
  $("send").disabled = active || !state.book || $("spoiler").value === ""; $("stop").hidden = !active;
  for (const node of document.querySelectorAll("#views button")) node.disabled = active || !state.book;
}
async function send(event) {
  event.preventDefault(); if (state.active || !state.book) return;
  const query = $("query").value.trim(); if (!query) return;
  setActive(true);
  try { if (!state.chat) await newChat(true); } catch (error) { setActive(false); notice(error.message); return; }
  notice(""); clearEvidence(); const view = createTurn(query);
  $("turn-status").textContent = "Starting your response…";
  setActive(true); renderBooks(); renderChats(); state.follow = true; state.controller = new AbortController();
  let complete = false;
  try {
    const response = await fetch("/api/chat", { ...jsonOptions({ query, session_id: state.chat.id, turn_id: crypto.randomUUID(), book_id: state.book.id, depth: $("depth").value, spoiler_limit: $("spoiler").value === "all" ? null : Number($("spoiler").value) }), signal: state.controller.signal });
    if (!response.ok) { const error = await response.json(); throw new Error(typeof error.detail === "string" ? error.detail : "The request was rejected."); }
    if (!response.headers.get("content-type")?.includes("text/event-stream")) throw new Error("The server did not return a stream.");
    const reader = response.body.getReader();
    const parser = new BookStream((type, data) => {
      renderEvent(type, data, view);
      if (type === "done") { complete = data.success; $("turn-status").textContent = data.success ? "Complete" : "Response incomplete"; }
    });
    while (true) {
      const {value, done} = await reader.read(); parser.push(value, done);
      if (done) break;
    }
    linkCitations(view);
    if (!complete) throw new Error("The response did not complete. Any partial answer is marked incomplete.");
    $("query").value = "";
  } catch (error) { view.status.textContent = error.name === "AbortError" ? "Stopped · partial answer" : "Response incomplete"; $("turn-status").textContent = view.status.textContent; if (error.name !== "AbortError") notice(error.message); }
  finally { linkCitations(view); setActive(false); state.controller = null; state.chats = await api("/api/chats").catch(() => state.chats); state.chat = state.chats.find((c) => c.id === state.chat.id) || state.chat; renderChats(); renderBooks(); }
}
async function upload() {
  const file = $("file").files[0]; if (!file) throw new Error("Choose a file first.");
  if (file.size > 25000000) throw new Error("The file exceeds 25 MB.");
  $("upload").disabled = true; $("upload-status").textContent = "Uploading…";
  try {
    const book = await api("/api/books", { method: "POST", headers: { "Content-Type": "application/octet-stream", "X-Filename": encodeURIComponent(file.name) }, body: file });
    $("upload-status").textContent = "Processing your book. You can keep reading other books."; state.books.push(book); renderBooks();
  } finally { $("upload").disabled = false; }
}
async function refreshBooks() {
  if (!state.books.some((b) => !["ready", "failed"].includes(b.status))) return;
  state.books = await api("/api/books"); renderBooks();
  $("upload-status").textContent = state.books.filter((b) => b.owner_id !== "public").map((b) => `${b.title}: ${b.status}${b.error ? ` — ${b.error}` : ""}`).join(" · ");
}
$("toggle-library").addEventListener("click", () => { const open = $("library-panel").classList.toggle("is-open"); $("toggle-library").setAttribute("aria-expanded", String(open)); });
$("composer").addEventListener("submit", send);
$("query").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); $("composer").requestSubmit(); } });
$("new-chat").addEventListener("click", () => newChat().catch((e) => notice(e.message)));
$("stop").addEventListener("click", async () => { $("turn-status").textContent = "Stopping…"; try { await api(`/api/chats/${state.chat.id}/cancel`, jsonOptions({})); state.controller?.abort(); } catch (e) { notice(e.message); } });
$("delete-chat").addEventListener("click", async () => { if (!state.chat || !confirm("Delete this conversation? This cannot be undone.")) return; try { await api(`/api/chats/${state.chat.id}`, { method: "DELETE" }); state.chats = state.chats.filter((c) => c.id !== state.chat.id); state.chat = null; localStorage.removeItem("active_chat"); $("conversation").replaceChildren(); clearEvidence(); renderChats(); } catch (e) { notice(e.message); } });
$("upload").addEventListener("click", () => upload().catch((e) => notice(e.message)));
$("book-search").addEventListener("input", renderBooks);
$("spoiler").addEventListener("change", () => setActive(state.active));
$("category").addEventListener("change", async () => {
  try {
    const book = await api(`/api/books/${state.book.id}`, { ...jsonOptions({kind: $("category").value}), method: "PATCH" });
    state.books = state.books.map((b) => b.id === book.id ? book : b);
    const scope = $("spoiler").value; showBook(book); $("spoiler").value = scope;
  } catch (error) { notice(error.message); $("category").value = state.book.kind || "Book"; }
});
$("close-passage").addEventListener("click", () => $("passage").close());
$("latest").addEventListener("click", () => { state.follow = true; $("composer").scrollIntoView({ block: "end" }); $("latest").hidden = true; });
window.addEventListener("wheel", (e) => { if (e.deltaY < 0 && state.active) state.follow = false; }, { passive: true });
for (const node of document.querySelectorAll("#views button")) node.addEventListener("click", () => { $("query").value = node.dataset.query; if (/author|adaptations|purchase/.test(node.dataset.query) && $("spoiler").value !== "all") notice("Web research can reveal plot details. Choose Whole book to enable author, adaptation, or edition searches."); $("query").focus(); });
async function initialize() {
  const data = await api("/api/bootstrap"); state.books = data.books; state.chats = data.chats;
  renderBooks(); renderChats(); setActive(false);
  if (data.readiness.length) notice("The library is available, but AI services need configuration before questions can be answered.");
  const previous = localStorage.getItem("active_chat"); if (state.chats.some((c) => c.id === previous)) await selectChat(previous);
  setInterval(() => refreshBooks().catch((e) => notice(e.message)), 4000);
}
initialize().catch((error) => notice(error.message));
