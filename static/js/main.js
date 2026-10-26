/* QueryMind – main.js */

// ── Auto-dismiss flashes ─────────────────────────────────────────────────────
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  }, 4000);
});

// ── Keyboard shortcut: / to focus query input ────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
    e.preventDefault();
    const inp = document.getElementById('questionInput');
    if (inp) { inp.focus(); inp.select(); }
  }
});
