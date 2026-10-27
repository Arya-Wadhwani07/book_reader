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
  $("book-title").textContent = book?.title || "Make room for a good book.";
  $("book-author").textContent = book ? `${book.author || "Unknown author"} · ${book.kind || "Book"}` : "Choose a book from the library or bring your own.";
  $("spoiler").replaceChildren();
  for (const chapter of book?.chapters || [{ number: 1, title: "Chapter 1" }]) {
    const option = document.createElement("option"); option.value = chapter.number; option.textContent = `Through ${chapter.title}`; $("spoiler").append(option);
  }
  const all = document.createElement("option"); all.value = "all"; all.textContent = "Whole book — includes the ending"; $("spoiler").append(all);
  renderBooks(); setActive(state.active);
  if (!state.active) $("turn-status").textContent = book ? "Ready for your question." : "Select a ready book to begin.";
}
async function selectBook(book) {
  if (state.chat?.book_id && state.chat.book_id !== book.id) await newChat();
  showBook(book);
}
async function newChat(force = false) {
  if (state.active && !force) return;
  const chat = await api("/api/chats", jsonOptions({}));
  state.chats.unshift(chat); state.chat = chat;
  $("conversation").replaceChildren(); clearEvidence(); renderChats();
  localStorage.setItem("active_chat", chat.id); $("query").focus();
}
async function selectChat(id) {
  const data = await api(`/api/chats/${id}`);
  state.chat = data.chat;
  showBook(state.books.find((b) => b.id === data.chat.book_id) || null);
  $("depth").value = data.chat.depth;
  $("spoiler").value = data.chat.spoiler_limit === null ? "all" : String(data.chat.spoiler_limit);
  $("conversation").replaceChildren(); clearEvidence();
  for (const turn of data.turns) {
    const view = createTurn(turn.query); view.answer.textContent = turn.answer;
    clearEvidence();
    for (const event of turn.events) renderEvent(event.event, event.data, view);
    linkCitations(view);
    if (turn.status !== "complete") view.summary.append(`\n${turn.status === "running" ? "Interrupted or still running" : turn.status}`);
    const inspect = button("Inspect this answer’s evidence", () => { clearEvidence(); for (const event of turn.events) renderEvent(event.event, event.data, { ...view, summary: document.createElement("div") }); });
    view.root.append(inspect);
  }
  localStorage.setItem("active_chat", id); renderChats();
}
function linkCitations(view) {
  const text = view.answer.textContent;
  const expression = /\[([a-f0-9]{32}-s\d+-t\d+)\]/g;
  let last = 0; view.answer.replaceChildren();
  for (const match of text.matchAll(expression)) {
    view.answer.append(text.slice(last, match.index));
    const source = [...$("sources").children].find((node) => node.dataset.key === match[1]);
    if (source) {
      const link = button("[Source]", () => source.querySelector("button").click());
      link.className = "inline-citation"; view.answer.append(link);
    } else view.answer.append(match[0]);
    last = match.index + match[0].length;
  }
  view.answer.append(text.slice(last));
}
function createTurn(query) {
  const root = document.createElement("article"); root.className = "turn";
  const question = document.createElement("div"); question.className = "question"; question.textContent = query;
  const summary = document.createElement("div"); summary.className = "route-summary";
  const answer = document.createElement("div"); answer.className = "answer";
  root.append(question, summary, answer); $("conversation").append(root);
  return { root, summary, answer };
}
function safeUrl(value) { try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : null; } catch { return null; } }
function renderEvent(event, data, view) {
  if (event === "token") { view.answer.append(data.text); if (state.follow) view.answer.scrollIntoView({ block: "end" }); else $("latest").hidden = false; }
  if (event === "trace") {
    const row = document.createElement("div"); row.className = `trace ${data.type || ""}`;
    const badge = document.createElement("span"); badge.className = "badge"; badge.textContent = ({ agent_route: "AGENT", llm_route: "MODEL", rag_retrieval: "RETRIEVAL", mcp_tool_call: "TOOL" })[data.type] || "STATUS";
    const label = document.createElement("div"); label.textContent = [data.agent, data.provider, data.model, data.tool, data.reason || data.message].filter(Boolean).join(" · ");
    row.append(badge, label); $("activity").append(row);
    if (["agent_route", "llm_route"].includes(data.type)) view.summary.append(`${label.textContent}\n`);
    $("turn-status").textContent = data.message || data.reason || "Working with your sources…";
  }
  if (event === "citation") {
    const key = data.chunk_id || data.url;
    if ([...$("sources").children].some((n) => n.dataset.key === key)) return;
    const card = document.createElement("div"); card.className = "source-card"; card.dataset.key = key;
    if (data.chunk_id) {
      card.append(button(`${data.label || data.chunk_id} · Book`, async () => {
        const source = await api(`/api/books/${encodeURIComponent(data.source_id)}/sources/${encodeURIComponent(data.chunk_id)}`);
        $("passage-label").textContent = source.label || source.id; $("passage-text").textContent = source.text; $("passage").showModal();
      }));
    } else if (safeUrl(data.url)) {
      const link = document.createElement("a"); link.href = safeUrl(data.url); link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = `${data.title || data.url} · Web`; card.append(link);
      const date = document.createElement("p"); date.textContent = data.retrieved_at ? `Retrieved ${data.retrieved_at}` : "External source"; card.append(date);
    } else return;
    $("sources").append(card); $("source-count").textContent = $("sources").children.length;
  }
  if (event === "error") { view.summary.classList.add("error"); view.summary.append(`\n${data.message}`); }
}
function setActive(active) {
  state.active = active;
  for (const id of ["new-chat", "delete-chat", "depth", "spoiler", "upload"]) $(id).disabled = active;
  $("send").disabled = active || !state.book; $("stop").hidden = !active;
  for (const node of document.querySelectorAll("#views button")) node.disabled = active || !state.book;
}
async function send(event) {
  event.preventDefault(); if (state.active || !state.book) return;
  const query = $("query").value.trim(); if (!query) return;
  setActive(true);
  try { if (!state.chat) await newChat(true); } catch (error) { setActive(false); notice(error.message); return; }
  notice(""); clearEvidence(); const view = createTurn(query);
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
  } catch (error) { $("turn-status").textContent = error.name === "AbortError" ? "Stopped" : "Response incomplete"; if (error.name !== "AbortError") notice(error.message); }
  finally { setActive(false); state.controller = null; state.chats = await api("/api/chats").catch(() => state.chats); state.chat = state.chats.find((c) => c.id === state.chat.id) || state.chat; renderChats(); renderBooks(); }
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
$("composer").addEventListener("submit", send);
$("query").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); $("composer").requestSubmit(); } });
$("new-chat").addEventListener("click", () => newChat().catch((e) => notice(e.message)));
$("stop").addEventListener("click", async () => { $("turn-status").textContent = "Stopping…"; try { await api(`/api/chats/${state.chat.id}/cancel`, jsonOptions({})); state.controller?.abort(); } catch (e) { notice(e.message); } });
$("delete-chat").addEventListener("click", async () => { if (!state.chat || !confirm("Delete this conversation? This cannot be undone.")) return; try { await api(`/api/chats/${state.chat.id}`, { method: "DELETE" }); state.chats = state.chats.filter((c) => c.id !== state.chat.id); state.chat = null; localStorage.removeItem("active_chat"); $("conversation").replaceChildren(); clearEvidence(); renderChats(); } catch (e) { notice(e.message); } });
$("upload").addEventListener("click", () => upload().catch((e) => notice(e.message)));
$("book-search").addEventListener("input", renderBooks);
$("close-passage").addEventListener("click", () => $("passage").close());
$("latest").addEventListener("click", () => { state.follow = true; $("composer").scrollIntoView({ block: "end" }); $("latest").hidden = true; });
window.addEventListener("wheel", (e) => { if (e.deltaY < 0 && state.active) state.follow = false; }, { passive: true });
for (const node of document.querySelectorAll("#views button")) node.addEventListener("click", () => { $("query").value = node.dataset.query; $("query").focus(); });
async function initialize() {
  const data = await api("/api/bootstrap"); state.books = data.books; state.chats = data.chats;
  renderBooks(); renderChats(); setActive(false);
  if (data.readiness.length) notice("The library is available, but AI services need configuration before questions can be answered.");
  const previous = localStorage.getItem("active_chat"); if (state.chats.some((c) => c.id === previous)) await selectChat(previous);
  setInterval(() => refreshBooks().catch((e) => notice(e.message)), 4000);
}
initialize().catch((error) => notice(error.message));
