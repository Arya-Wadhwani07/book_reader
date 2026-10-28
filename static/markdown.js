"use strict";
// A small, text-only Markdown renderer: raw HTML and image embeds are never interpreted.
const BookMarkdown = (() => {
  const escape = (value) => String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  function safeUrl(value) {
    try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : null; }
    catch { return null; }
  }
  function inline(text, sources, depth = 0) {
    if (depth > 12) return escape(text);
    const pattern = /`([^`\n]+)`|\[([^\]\n]+)\]\(([^\s)]+)\)|[\[【]((?:[a-f0-9]{32}-)?s\d+-t\d+)[\]】]|\*\*([^\n]+?)\*\*|__([^\n]+?)__|\*([^*\n]+)\*|_([^_\n]+)_/g;
    let html = "", last = 0;
    for (const match of text.matchAll(pattern)) {
      html += escape(text.slice(last, match.index));
      if (match[1] !== undefined) html += `<code>${escape(match[1])}</code>`;
      else if (match[2] !== undefined) {
        const url = safeUrl(match[3]);
        html += url ? `<a href="${escape(url)}" target="_blank" rel="noopener noreferrer">${inline(match[2], sources, depth + 1)}</a>` : escape(match[0]);
      } else if (match[4] !== undefined) {
        const matches = sources.filter((id) => id === match[4] || id.endsWith(`-${match[4]}`));
        html += matches.length === 1 ? `<button type="button" class="inline-citation" data-source="${escape(matches[0])}" aria-label="Open source passage">Source ↗</button>` : escape(match[0]);
      } else {
        const strong = match[5] !== undefined || match[6] !== undefined;
        const value = match[5] ?? match[6] ?? match[7] ?? match[8];
        const tag = strong ? "strong" : "em";
        html += `<${tag}>${inline(value, sources, depth + 1)}</${tag}>`;
      }
      last = match.index + match[0].length;
    }
    return html + escape(text.slice(last));
  }
  const item = (line) => /^( *)([-+*]|\d+[.)])\s+(.*)$/.exec(line);
  const tableRow = (line) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
  function blocks(lines, sources, depth = 0) {
    if (depth > 12) return `<p>${escape(lines.join("\n"))}</p>`;
    let html = "", i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (!line.trim()) { i++; continue; }
      if (/^\s*```/.test(line)) {
        const code = []; i++;
        while (i < lines.length && !/^\s*```/.test(lines[i])) code.push(lines[i++]);
        if (i < lines.length) i++;
        html += `<pre><code>${escape(code.join("\n"))}</code></pre>`; continue;
      }
      const heading = /^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line);
      if (heading) { const level = Math.max(2, heading[1].length); html += `<h${level}>${inline(heading[2], sources)}</h${level}>`; i++; continue; }
      if (/^\s*(?:---+|\*\*\*+|___+)\s*$/.test(line)) { html += "<hr>"; i++; continue; }
      if (/^\s*>/.test(line)) {
        const quote = [];
        while (i < lines.length && /^\s*>/.test(lines[i])) quote.push(lines[i++].replace(/^\s*> ?/, ""));
        html += `<blockquote>${blocks(quote, sources, depth + 1)}</blockquote>`; continue;
      }
      if (i + 1 < lines.length && line.includes("|") && /^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[i + 1])) {
        const headers = tableRow(line); i += 2;
        html += `<div class="answer-table"><table><thead><tr>${headers.map((cell) => `<th scope="col">${inline(cell, sources)}</th>`).join("")}</tr></thead><tbody>`;
        while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
          const cells = tableRow(lines[i++]);
          html += `<tr>${headers.map((_, n) => `<td>${inline(cells[n] || "", sources)}</td>`).join("")}</tr>`;
        }
        html += "</tbody></table></div>"; continue;
      }
      const first = item(line);
      if (first) {
        const indent = first[1].length, ordered = /^\d/.test(first[2]), tag = ordered ? "ol" : "ul";
        html += `<${tag}${ordered ? ` start="${parseInt(first[2], 10)}"` : ""}>`;
        while (i < lines.length) {
          const current = item(lines[i]);
          if (!current || current[1].length !== indent || /^\d/.test(current[2]) !== ordered) break;
          const content = [current[3]]; i++;
          while (i < lines.length) {
            if (!lines[i].trim()) {
              if (i + 1 < lines.length && /^\s+\S/.test(lines[i + 1]) && lines[i + 1].search(/\S/) > indent) { content.push(""); i++; continue; }
              break;
            }
            if (lines[i].search(/\S/) <= indent) break;
            const continuation = lines[i++];
            content.push(continuation.slice(Math.min(indent + 2, continuation.search(/\S/))));
          }
          html += `<li>${blocks(content, sources, depth + 1)}</li>`;
          while (i < lines.length && !lines[i].trim()) i++;
        }
        html += `</${tag}>`; continue;
      }
      const paragraph = [line]; i++;
      while (i < lines.length && lines[i].trim() && !item(lines[i]) && !/^\s*(?:#{1,6}\s|>|```|---+\s*$)/.test(lines[i])) {
        if (i + 1 < lines.length && lines[i].includes("|") && /^\s*\|?\s*:?-{3,}/.test(lines[i + 1])) break;
        paragraph.push(lines[i++]);
      }
      html += `<p>${inline(paragraph.map((part) => part.trim()).join(" "), sources)}</p>`;
    }
    return html;
  }
  return { render: (text, sources = []) => blocks(String(text).replace(/\r\n?/g, "\n").replace(/\t/g, "    ").split("\n"), sources) };
})();
if (typeof module !== "undefined") module.exports = BookMarkdown;
