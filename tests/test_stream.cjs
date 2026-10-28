const test = require('node:test');
const assert = require('node:assert/strict');
const BookStream = require('../static/stream.js');
const frame = (event, data) => `event: ${event}\r\ndata: ${JSON.stringify(data)}\r\n\r\n`;
const source = Buffer.from(frame('token', {text:'café 📚'}) + frame('done', {success:true}));
for (let split = 0; split <= source.length; split++) {
  test(`UTF-8 and CRLF boundary ${split}`, () => {
    const events = []; const reader = new BookStream((...args) => events.push(args));
    reader.push(source.subarray(0, split)); reader.push(source.subarray(split), true);
    assert.deepEqual(events, [['token', {text:'café 📚'}], ['done', {success:true}]]);
  });
}
test('truncated frame fails', () => assert.throws(() => new BookStream(()=>{}).push(Buffer.from('event: token\ndata: {}'), true)));
test('EOF without done fails', () => assert.throws(() => new BookStream(()=>{}).push(Buffer.from(frame('token', {text:'a'})), true)));
test('data after done fails', () => assert.throws(() => new BookStream(()=>{}).push(Buffer.from(frame('done', {success:true}) + frame('token', {text:'late'})), true)));
test('non-object payload fails', () => assert.throws(() => new BookStream(()=>{}).push(Buffer.from(frame('token', [])), true)));
test('failed done remains failed', () => {
  let payload; new BookStream((event, data)=>{payload=data}).push(Buffer.from(frame('done', {success:false})), true);
  assert.equal(payload.success,false);
});

const Markdown = require('../static/markdown.js');
test('answer headings, emphasis and nested lists render', () => {
  const html = Markdown.render('**Main idea** in *The Prince*.\n\n### Content\n* **States:** republics\n* Types\n  * **Hereditary:** established family\n  * **New:** new territory\n\n### Research\nNone mentioned.');
  assert.match(html, /<strong>Main idea<\/strong>/);
  assert.match(html, /<em>The Prince<\/em>/);
  assert.match(html, /<h3>Content<\/h3>/);
  assert.match(html, /<li><p>Types<\/p><ul><li>/);
  assert.match(html, /<h3>Research<\/h3><p>None mentioned\.<\/p>/);
});
test('ordered lists preserve numbering and continuation text', () => {
  const html = Markdown.render('3. First item\n   Continued here.\n4. Second item');
  assert.match(html, /<ol start="3">/);
  assert.match(html, /First item Continued here/);
  assert.equal((html.match(/<li>/g) || []).length, 2);
});
test('raw HTML stays inert, including inside code', () => {
  const html = Markdown.render('<img src=x onerror=alert(1)>\n\n```html\n<script>alert(1)</script>\n```');
  assert.ok(!html.includes('<img'));
  assert.ok(!html.includes('<script'));
  assert.match(html, /&lt;img/);
  assert.match(html, /<pre><code>&lt;script&gt;/);
});
test('unsafe URL schemes cannot create links', () => {
  for (const url of ['javascript:alert', 'data:text/html,test', 'vbscript:test', 'file:///etc/passwd']) {
    assert.ok(!Markdown.render(`[click](${url})`).includes('<a '));
  }
  assert.match(Markdown.render('[Read](https://example.test/book?q=%22)'), /rel="noopener noreferrer"/);
});
test('only known unambiguous citations become buttons', () => {
  const id = `${'a'.repeat(32)}-s1-t0`, other = `${'b'.repeat(32)}-s1-t0`;
  assert.match(Markdown.render(`[${id}]`, [id]), new RegExp(`data-source="${id}"`));
  assert.match(Markdown.render('【s1-t0】', [id]), /<button /);
  assert.ok(!Markdown.render('[s1-t0]', [id,other]).includes('<button'));
  assert.ok(!Markdown.render(`[${other}]`, [id]).includes('<button'));
});
test('Markdown blocks render quotes, tables and inline code', () => {
  const html = Markdown.render('> A **quote**\n\n| Agent | Model |\n| --- | --- |\n| Research | `Nemotron` |');
  assert.match(html, /<blockquote><p>A <strong>quote<\/strong>/);
  assert.match(html, /<th scope="col">Agent<\/th>/);
  assert.match(html, /<td><code>Nemotron<\/code><\/td>/);
});
test('streamed partial Markdown converges to the complete rendering', () => {
  const text = '### Summary\n\nA **bold** claim and *context*.\n\n* First\n  * Second';
  for (let split=0; split<=text.length; split++) {
    let accumulated = '';
    for (const part of [text.slice(0,split),text.slice(split)]) {
      accumulated += part;
      assert.doesNotThrow(() => Markdown.render(accumulated));
    }
    assert.equal(Markdown.render(accumulated), Markdown.render(text));
  }
});
test('quotes in link attributes remain escaped', () => {
  const html = Markdown.render('[safe](https://example.test/"onmouseover="alert)');
  assert.ok(!html.includes('"onmouseover='));
  assert.match(html, /<a href="https:\/\/example.test\//);
});
