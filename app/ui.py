"""The single-page UI, inlined as a constant.

Inlined rather than served from ``static/`` because serverless working directories
are unreliable and a 404 on the judging page would be an unforced loss. It is one
page: run a case, watch the trail, export it.
"""

PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Kit</title>
<style>
  :root { --bg:#fbfbfa; --fg:#1a1a18; --mut:#6b6b63; --line:#e0e0d8; --acc:#2f6f4f; --warn:#a8541f; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#16161a; --fg:#ecebe6; --mut:#9a9a92; --line:#2e2e34; --acc:#7fc4a0; --warn:#e0a06a; }
  }
  * { box-sizing:border-box }
  body { margin:0; background:var(--bg); color:var(--fg);
         font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif }
  .wrap { max-width:900px; margin:0 auto; padding:32px 20px 80px }
  h1 { font-size:22px; margin:0 0 4px; letter-spacing:-.01em }
  .sub { color:var(--mut); margin:0 0 24px }
  textarea { width:100%; min-height:90px; padding:12px; border:1px solid var(--line);
             border-radius:10px; background:transparent; color:var(--fg); font:inherit; resize:vertical }
  .row { display:flex; gap:10px; flex-wrap:wrap; margin:12px 0 24px }
  button { font:inherit; padding:9px 16px; border-radius:9px; border:1px solid var(--line);
           background:transparent; color:var(--fg); cursor:pointer }
  button.primary { background:var(--acc); border-color:var(--acc); color:#fff; font-weight:600 }
  button:disabled { opacity:.5; cursor:default }
  .step { border-left:2px solid var(--line); padding:10px 0 10px 16px; margin-left:6px }
  .step .k { font-size:11px; text-transform:uppercase; letter-spacing:.08em; color:var(--mut) }
  .step .n { font-weight:600 }
  .step pre { white-space:pre-wrap; word-break:break-word; margin:6px 0 0;
              font:12.5px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;
              background:color-mix(in srgb, var(--fg) 5%, transparent);
              padding:9px 11px; border-radius:8px; overflow-x:auto }
  .tool { border-left-color:var(--acc) }
  .error { border-left-color:var(--warn) }
  .final { border-left-color:var(--acc); border-left-width:3px }
  .answer { border:1px solid var(--line); border-radius:12px; padding:16px; margin:24px 0; white-space:pre-wrap }
  .muted { color:var(--mut); font-size:13px }
</style>
<div class="wrap">
  <h1>Agent Kit</h1>
  <p class="sub">Ingest &rarr; reason with tools &rarr; auditable decision. Every step is shown.</p>

  <textarea id="task" placeholder="Describe the task for the agent..."></textarea>
  <div class="row">
    <button class="primary" id="demo">&#9654; Run the demo case</button>
    <button id="run">Run my task</button>
    <button id="export" disabled>Export trail (JSON)</button>
  </div>

  <div id="status" class="muted"></div>
  <div id="answer"></div>
  <div id="trail"></div>
</div>
<script>
let lastRun = null;
const $ = (id) => document.getElementById(id);
const ESC = {'&':'&amp;','<':'&lt;','>':'&gt;'};
function esc(s) { return String(s).replace(/[&<>]/g, (c) => ESC[c]); }

function render(run) {
  lastRun = run;
  $('export').disabled = false;
  $('answer').innerHTML = run.answer
    ? '<div class="answer"><strong>Answer</strong><br>' + esc(run.answer) + '</div>'
    : '';
  $('trail').innerHTML = run.steps.map(function (s) {
    const cls = s.kind === 'tool' ? 'tool'
              : s.kind === 'error' ? 'error'
              : s.kind === 'final' ? 'final' : '';
    const ms = s.ms ? ' &middot; ' + s.ms + ' ms' : '';
    const name = s.name ? ' &middot; ' + esc(s.name) : '';
    return '<div class="step ' + cls + '">'
         + '<div class="k"><span class="n">step ' + s.n + '</span> &middot; '
         + esc(s.kind) + name + ms + '</div>'
         + (s.detail ? '<pre>' + esc(s.detail) + '</pre>' : '')
         + '</div>';
  }).join('');
}

async function call(url, body) {
  $('status').textContent = 'Running the agent...';
  $('answer').innerHTML = '';
  $('trail').innerHTML = '';
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body || {})
    });
    const data = await r.json();
    if (!r.ok) { $('status').textContent = data.detail || 'Request failed.'; return; }
    $('status').textContent = data.ok ? '' : 'The run did not complete cleanly - see the trail.';
    render(data);
  } catch (e) {
    $('status').textContent = 'Network error: ' + e.message;
  }
}

$('demo').onclick = function () { call('/api/demo'); };
$('run').onclick = function () {
  const task = $('task').value.trim();
  if (!task) { $('status').textContent = 'Type a task first, or run the demo case.'; return; }
  call('/api/run', {task: task});
};
$('export').onclick = function () {
  const blob = new Blob([JSON.stringify(lastRun, null, 2)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'agent-trail.json';
  a.click();
};
</script>
"""
