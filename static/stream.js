"use strict";
class BookStream {
  constructor(onEvent) { this.onEvent = onEvent; this.buffer = ""; this.decoder = new TextDecoder("utf-8", {fatal: true}); this.done = false; }
  push(bytes, final = false) {
    this.buffer += this.decoder.decode(bytes, {stream: !final});
    let boundary;
    while ((boundary = /\r?\n\r?\n/.exec(this.buffer))) {
      const frame = this.buffer.slice(0, boundary.index);
      this.buffer = this.buffer.slice(boundary.index + boundary[0].length);
      let event = "message"; const lines = [];
      for (const line of frame.split(/\r?\n/)) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) lines.push(line.slice(5).replace(/^ /, ""));
      }
      if (!lines.length) continue;
      if (this.done) throw new Error("The server sent data after completion.");
      const data = JSON.parse(lines.join("\n"));
      if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Invalid stream payload.");
      if (event === "done") { if (typeof data.success !== "boolean") throw new Error("Invalid completion status."); this.done = true; }
      this.onEvent(event, data);
    }
    if (final && (this.buffer.trim() || !this.done)) throw new Error("Connection interrupted. The response is incomplete.");
  }
}
if (typeof module !== "undefined") module.exports = BookStream;
