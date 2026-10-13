const test = require('node:test');
const assert = require('node:assert/strict');
const {compute, parseTimestamp} = require('./timing.js');
const start = '2026-10-13T10:00';
const now = new Date('2026-10-13T10:30:00');
const input = {pathway:'urgent',recognition:start,lactate:'',cultures:'',antibiotic:''};
test('one-hour pathway computes deadline', () => {
  const result = compute(input,now);
  assert.equal(result.deadline.getHours(),11);
  assert.equal(result.remainingMs,1800000);
  assert.equal(result.antibioticStatus,'pending');
});
test('three-hour pathway and due soon', () => {
  const result = compute({...input,pathway:'possible'},new Date('2026-10-13T12:50:00'));
  assert.equal(result.targetHours,3);
  assert.equal(result.antibioticStatus,'due-soon');
});
test('overdue and on-time records distinct', () => {
  assert.equal(compute(input,new Date('2026-10-13T11:00:01')).antibioticStatus,'overdue');
  assert.equal(compute({...input,antibiotic:'2026-10-13T10:55'},new Date('2026-10-13T11:30')).antibioticStatus,'recorded');
  assert.equal(compute({...input,antibiotic:'2026-10-13T11:05'},new Date('2026-10-13T11:30')).antibioticStatus,'after-target');
});
test('culture-before-antibiotic ordering', () => {
  const timely = compute({...input,cultures:'2026-10-13T10:10',antibiotic:'2026-10-13T10:20'},now);
  assert.equal(timely.cultureOrder,'before-or-same');
  assert.equal(compute({...input,cultures:'2026-10-13T10:25',antibiotic:'2026-10-13T10:20'},now).cultureOrder,'after-antibiotic');
});
test('invalid, unknown, future times rejected', () => {
  assert.throws(()=>compute({...input,pathway:'other'},now),/pathway/);
  assert.throws(()=>compute({...input,recognition:'2026-10-13T11:00'},now),/future/);
  assert.throws(()=>compute({...input,antibiotic:'2026-10-13T10:40'},now),/future/);
  assert.throws(()=>parseTimestamp('abc','Time'),/local date/);
  assert.throws(()=>parseTimestamp('2026-02-30T12:00','Time'),/invalid/);
});
test('offset-safe arithmetic crosses midnight', () => {
  const result=compute({...input,recognition:'2026-10-13T23:30'},new Date('2026-10-14T00:05'));
  assert.equal(result.deadline.getDate(),14);
  assert.equal(result.deadline.getHours(),0);
  assert.equal(result.elapsedMinutes,35);
});
