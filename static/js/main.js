/* ═══════════════════════════════════════════════════════════════════════════
   QueryMind — main.js
   Linear Editorial Client Interactions, Command Palette, & Voice Dictation
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Auto-dismiss flashes ─────────────────────────────────────────────────────
document.querySelectorAll('.flash-alert, .flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateY(-4px)';
    setTimeout(() => el.remove(), 400);
  }, 4500);
});

// ── Mobile Drawer Navigation Toggle ──────────────────────────────────────────
function toggleMobileSidebar() {
  const sb = document.querySelector('.sidebar-rail');
  if (sb) sb.classList.toggle('open');
}

// ── Command Palette (Ctrl+K / Cmd+K) ─────────────────────────────────────────
function openCommandPalette() {
  const cp = document.getElementById('commandPalette');
  if (cp) {
    cp.style.display = 'flex';
    const inp = document.getElementById('cpSearchInput');
    if (inp) {
      inp.value = '';
      inp.focus();
    }
  }
}

function closeCommandPalette() {
  const cp = document.getElementById('commandPalette');
  if (cp) cp.style.display = 'none';
}

function filterCommandPalette(query) {
  const q = query.toLowerCase().trim();
  const items = document.querySelectorAll('.cp-results-list .cp-item');
  items.forEach(item => {
    const text = item.textContent.toLowerCase();
    item.style.display = (!q || text.includes(q)) ? 'flex' : 'none';
  });
}

// ── Global Keyboard Shortcuts ────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // Ctrl+K or Cmd+K: Open/Close Command Palette
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    const cp = document.getElementById('commandPalette');
    if (cp && cp.style.display !== 'none') {
      closeCommandPalette();
    } else {
      openCommandPalette();
    }
    return;
  }

  // Escape: Close Command Palette
  if (e.key === 'Escape') {
    closeCommandPalette();
  }

  // / key: focus query input if not in form input
  if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
    e.preventDefault();
    const inp = document.getElementById('questionInput');
    if (inp) { inp.focus(); inp.select(); }
  }
});

// ── Suggestion Chip Helper ───────────────────────────────────────────────────
function ask(el) {
  const q = el.getAttribute('data-q') || el.textContent.trim();
  const inp = document.getElementById('questionInput');
  if (inp) {
    inp.value = q;
    inp.focus();
    // Auto-submit if queryForm exists
    const form = document.getElementById('queryForm');
    if (form) form.submit();
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// Zero-Cost Voice Ingress Subsystem (Client-Side Streaming ASR)
// ═════════════════════════════════════════════════════════════════════════════
let activeRecognition = null;
let isListening = false;

function toggleVoiceDictation(targetInputId = 'questionInput', micBtnId = 'micBtn', statusBarId = 'voiceStatus') {
  if (isListening) {
    stopVoiceDictation(micBtnId, statusBarId);
  } else {
    startVoiceDictation(targetInputId, micBtnId, statusBarId);
  }
}

function startVoiceDictation(targetInputId = 'questionInput', micBtnId = 'micBtn', statusBarId = 'voiceStatus') {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari, or type your query.");
    return;
  }

  const inputEl = document.getElementById(targetInputId);
  const micBtn = document.getElementById(micBtnId);
  const statusBar = document.getElementById(statusBarId);
  const statusText = document.getElementById('voiceStatusText');

  try {
    activeRecognition = new SpeechRecognition();
    activeRecognition.continuous = false;
    activeRecognition.interimResults = true;
    activeRecognition.lang = 'en-US';

    activeRecognition.onstart = function() {
      isListening = true;
      if (micBtn) micBtn.classList.add('listening');
      if (statusBar) statusBar.style.display = 'flex';
      if (statusText) statusText.textContent = 'Listening to voice input... Speak your inquiry';
    };

    activeRecognition.onresult = function(event) {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const currentSpeech = finalTranscript || interimTranscript;
      if (inputEl && currentSpeech) {
        inputEl.value = currentSpeech.trim();
      }
      if (statusText && currentSpeech) {
        statusText.textContent = 'Transcribed: "' + currentSpeech.trim() + '"';
      }
    };

    activeRecognition.onerror = function(event) {
      console.warn("Speech Recognition Error:", event.error);
      if (statusText) {
        if (event.error === 'not-allowed') {
          statusText.textContent = 'Microphone permission denied. Enable microphone in browser settings.';
        } else if (event.error === 'no-speech') {
          statusText.textContent = 'No speech detected. Please speak clearly into your mic.';
        } else {
          statusText.textContent = 'Voice error: ' + event.error;
        }
      }
      setTimeout(() => stopVoiceDictation(micBtnId, statusBarId), 2500);
    };

    activeRecognition.onend = function() {
      stopVoiceDictation(micBtnId, statusBarId);
    };

    activeRecognition.start();
  } catch (err) {
    console.error("Failed to start voice recognition:", err);
    stopVoiceDictation(micBtnId, statusBarId);
  }
}

function stopVoiceDictation(micBtnId = 'micBtn', statusBarId = 'voiceStatus') {
  isListening = false;
  if (activeRecognition) {
    try { activeRecognition.stop(); } catch (e) {}
    activeRecognition = null;
  }
  const micBtn = document.getElementById(micBtnId);
  const statusBar = document.getElementById(statusBarId);
  if (micBtn) micBtn.classList.remove('listening');
  if (statusBar) statusBar.style.display = 'none';
}
