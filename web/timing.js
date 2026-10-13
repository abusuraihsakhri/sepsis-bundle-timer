/* Pure timestamp calculations; no clinical decisions or patient identifiers. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.SepsisTiming = api;
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';
  const PATHWAYS = Object.freeze({
    urgent: { hours: 1, label: 'Shock or probable/definite sepsis' },
    possible: { hours: 3, label: 'Possible sepsis without shock (if concern persists)' }
  });

  function parseTimestamp(value, label) {
    if (value == null || String(value).trim() === '') return null;
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) {
      throw new Error(label + ' must use a local date and time.');
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) throw new Error(label + ' is invalid.');
    const expected = [parsed.getFullYear().toString().padStart(4,'0'),
      String(parsed.getMonth()+1).padStart(2,'0'), String(parsed.getDate()).padStart(2,'0')].join('-') + 'T' +
      String(parsed.getHours()).padStart(2,'0') + ':' + String(parsed.getMinutes()).padStart(2,'0');
    if (expected !== value) throw new Error(label + ' is invalid or falls in a daylight-saving time gap.');
    return parsed;
  }

  function compute(input, now = new Date()) {
    if (!(now instanceof Date) || Number.isNaN(now.getTime())) throw new Error('Current time is invalid.');
    if (!Object.prototype.hasOwnProperty.call(PATHWAYS, input.pathway)) {
      throw new Error('Select a supported assessment pathway.');
    }
    const recognition = parseTimestamp(input.recognition, 'Recognition time');
    if (!recognition) throw new Error('Enter the recognition time.');
    if (recognition.getTime() > now.getTime()) throw new Error('Recognition time cannot be in the future.');
    const dates = {};
    for (const name of ['lactate','cultures','antibiotic']) {
      const date = parseTimestamp(input[name], name);
      if (date && date.getTime() > now.getTime()) throw new Error(name + ' completion cannot be in the future.');
      dates[name] = date;
    }
    const targetHours = PATHWAYS[input.pathway].hours;
    const deadline = new Date(recognition.getTime() + targetHours * 3600000);
    const remainingMs = deadline.getTime() - now.getTime();
    let antibioticStatus;
    if (dates.antibiotic) {
      antibioticStatus = dates.antibiotic > deadline ? 'after-target' : 'recorded';
    } else if (remainingMs < 0) {
      antibioticStatus = 'overdue';
    } else if (remainingMs <= 15 * 60000) {
      antibioticStatus = 'due-soon';
    } else {
      antibioticStatus = 'pending';
    }
    const cultureOrder = dates.cultures && dates.antibiotic ?
      (dates.cultures <= dates.antibiotic ? 'before-or-same' : 'after-antibiotic') : 'unknown';
    return {
      recognition, deadline, remainingMs, targetHours, antibioticStatus,
      cultureOrder, dates,
      elapsedMinutes: Math.floor((now.getTime() - recognition.getTime()) / 60000),
      antibioticMinutes: dates.antibiotic ? Math.round((dates.antibiotic.getTime() - recognition.getTime()) / 60000) : null
    };
  }
  return Object.freeze({ PATHWAYS, parseTimestamp, compute });
});
