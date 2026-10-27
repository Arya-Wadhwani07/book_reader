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
