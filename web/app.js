/* No network calls, browser storage, patient fields, or simulated audit records. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const fields = ['recognition','pathway','lactate','cultures','antibiotic'];
  const formatLocal = date => [date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-') + 'T' + String(date.getHours()).padStart(2,'0') + ':' + String(date.getMinutes()).padStart(2,'0');
  const showDate = date => date ? date.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}) : '—';
  const signedMinutes = ms => { const m = Math.ceil(Math.abs(ms)/60000); return `${Math.floor(m/60)}h ${String(m%60).padStart(2,'0')}m`; };
  let lastResult = null;
  function render() {
    const recognition = $('recognition').value;
    $('error').hidden = true;
    $('error').textContent = '';
    if (!recognition) {
      lastResult = null;
      $('countdown').textContent = '—'; $('deadline').textContent = '—'; $('elapsed').textContent = '—';
      $('countdown-caption').textContent = 'Enter a recognition time'; $('antibiotic-status').textContent = 'Not started';
      $('antibiotic-label').textContent = 'Not recorded'; $('lactate-label').textContent = 'Not recorded';
      $('cultures-label').textContent = 'Not recorded'; $('order').textContent = 'Culture-before-antibiotic ordering: not assessable until both events are recorded.';
      return;
    }
    try {
      const values = Object.fromEntries(fields.map(k=>[k,$(k).value]));
      const r = SepsisTiming.compute(values);
      lastResult = r;
      const antibioticRecorded = Boolean(r.dates.antibiotic);
      $('countdown').textContent = antibioticRecorded ? 'Recorded' : `${signedMinutes(r.remainingMs)} ${r.remainingMs < 0 ? 'past target' : 'remaining'}`;
      $('countdown').className = r.antibioticStatus === 'overdue' || r.antibioticStatus === 'after-target' ? 'late' : r.antibioticStatus === 'due-soon' ? 'warning' : '';
      $('countdown-caption').textContent = antibioticRecorded ? `${r.antibioticMinutes} min from recognition` : `${r.targetHours}-hour reference, not a treatment instruction`;
      $('deadline').textContent = showDate(r.deadline);
      $('target-caption').textContent = `${r.targetHours}-hour antimicrobial reference`;
      $('elapsed').textContent = `${signedMinutes(Date.now()-r.recognition.getTime())}`;
      $('antibiotic-status').textContent = ({recorded:'Antibiotic timestamp within reference', 'after-target':'Antibiotic timestamp after reference', overdue:'Reference time passed', 'due-soon':'Reference approaching', pending:'Awaiting antibiotic timestamp'})[r.antibioticStatus];
      for (const name of ['lactate','cultures','antibiotic']) $(name+'-label').textContent = r.dates[name] ? 'Recorded: ' + showDate(r.dates[name]) : 'Not recorded';
      $('order').textContent = ({'before-or-same':'Blood culture timestamp is before or equal to antibiotic timestamp.','after-antibiotic':'Blood culture timestamp is after antibiotic timestamp; review ordering.','unknown':'Culture-before-antibiotic ordering: not assessable until both events are recorded.'})[r.cultureOrder];
    } catch(e) {
      lastResult=null;
      $('error').textContent=e.message; $('error').hidden=false;
      $('countdown').textContent='—'; $('deadline').textContent='—'; $('elapsed').textContent='—';
    }
  }
  $('start-now').addEventListener('click', () => { $('recognition').value = formatLocal(new Date()); render(); });
  $('reset').addEventListener('click', () => { for (const k of fields) if(k!=='pathway') $(k).value=''; $('pathway').value='urgent'; render(); });
  for (const name of fields) $(name).addEventListener('change', render);
  for (const btn of document.querySelectorAll('[data-now]')) btn.addEventListener('click',()=>{ $(btn.dataset.now).value=formatLocal(new Date()); render(); });
  $('export').addEventListener('click',()=>{
    if (!lastResult) { $('error').textContent='Enter valid timestamps before exporting.'; $('error').hidden=false; return; }
    const values = Object.fromEntries(fields.map(k=>[k,$(k).value]));
    const data = {...values,reference_deadline:formatLocal(lastResult.deadline),reference_hours:lastResult.targetHours,antibiotic_status:lastResult.antibioticStatus,culture_order:lastResult.cultureOrder};
    const cells = Object.values(data).map(v=>'"'+String(v).replace(/"/g,'""')+'"');
    const csv = Object.keys(data).join(',')+'\r\n'+cells.join(',')+'\r\n';
    const url = URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const link=document.createElement('a');link.href=url;link.download='sepsis-timing-record.csv';link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  render();
  setInterval(()=>{if($('recognition').value) render();},15000);
})();
