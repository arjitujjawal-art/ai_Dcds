/**
 * QueryMind 2.0 — Voice-to-SQL Workspace Controller
 * Handles browser Web Speech API (speech-to-text input), editable transcripts,
 * asynchronous SQL generation, AST validation, execution, and tabular/visual rendering.
 */

let recognition = null;
let isRecording = false;
let currentInputMode = 'text'; // 'voice' or 'text'
let currentChartInstance = null;
let lastVerbalSummary = '';

// Check browser speech recognition availability
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

document.addEventListener('DOMContentLoaded', () => {
  initSpeechRecognition();
});

function initSpeechRecognition() {
  const micStatusDot = document.getElementById('micStatusDot');
  const micStatusText = document.getElementById('micStatusText');

  if (!SpeechRecognition) {
    if (micStatusText) {
      micStatusText.textContent = 'Voice API Unavailable (Use Typing)';
      micStatusDot.className = 'mic-status-dot dot-warning';
    }
    const startBtn = document.getElementById('startRecordBtn');
    if (startBtn) {
      startBtn.title = 'Web Speech API is not supported in this browser. Please use keyboard input.';
    }
    return;
  }

  try {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isRecording = true;
      currentInputMode = 'voice';
      updateInputModeTag('voice');
      toggleRecordingUI(true);
      setMicStatus('listening', 'Listening... Speak your database question');
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const qInput = document.getElementById('questionInput');
      if (qInput) {
        const text = finalTranscript || interimTranscript;
        if (text) {
          qInput.value = text.trim();
        }
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      isRecording = false;
      toggleRecordingUI(false);

      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        setMicStatus('denied', 'Microphone Permission Denied');
        showValidationFeedback('Microphone permission was denied. Please allow microphone access in browser settings, or type your question.', 'warning');
      } else if (event.error === 'no-speech') {
        setMicStatus('idle', 'No speech detected (Ready)');
      } else {
        setMicStatus('error', `Speech error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      isRecording = false;
      toggleRecordingUI(false);
      setMicStatus('ready', 'Microphone Ready');

      const qInput = document.getElementById('questionInput');
      if (qInput && qInput.value.trim().length > 3) {
        // Automatically interpret & generate SQL for inspection (WITHOUT executing)
        triggerGenerateSql();
      }
    };

    setMicStatus('ready', 'Microphone Ready');
  } catch (err) {
    console.error('Failed to initialize speech recognition:', err);
    setMicStatus('error', 'Microphone initialization failed');
  }
}

function startVoiceRecognition() {
  if (!recognition) {
    alert('Web Speech API is not supported in this browser. You can type your question in the text box below.');
    document.getElementById('questionInput')?.focus();
    return;
  }

  if (isRecording) {
    stopVoiceRecognition();
    return;
  }

  try {
    recognition.start();
  } catch (err) {
    console.warn('Could not start recognition:', err);
  }
}

function stopVoiceRecognition() {
  if (recognition && isRecording) {
    try {
      recognition.stop();
    } catch (err) {
      console.warn('Error stopping recognition:', err);
    }
  }
  isRecording = false;
  toggleRecordingUI(false);
}

function setMicStatus(state, message) {
  const dot = document.getElementById('micStatusDot');
  const text = document.getElementById('micStatusText');
  if (!dot || !text) return;

  text.textContent = message;
  dot.className = 'mic-status-dot';

  if (state === 'listening') {
    dot.classList.add('dot-listening');
  } else if (state === 'ready') {
    dot.classList.add('dot-ready');
  } else if (state === 'denied' || state === 'error') {
    dot.classList.add('dot-danger');
  } else {
    dot.classList.add('dot-idle');
  }
}

function toggleRecordingUI(recording) {
  const startBtn = document.getElementById('startRecordBtn');
  const stopBtn = document.getElementById('stopRecordBtn');
  const wave = document.getElementById('listeningWave');

  if (recording) {
    startBtn?.classList.add('hidden');
    stopBtn?.classList.remove('hidden');
    wave?.classList.remove('hidden');
  } else {
    startBtn?.classList.remove('hidden');
    stopBtn?.classList.add('hidden');
    wave?.classList.add('hidden');
  }
}

function onQuestionInputChanged() {
  // If user types manually, update input mode to text
  if (!isRecording) {
    currentInputMode = 'text';
    updateInputModeTag('text');
  }
}

function updateInputModeTag(mode) {
  const badge = document.getElementById('inputModeBadge');
  if (!badge) return;

  if (mode === 'voice') {
    badge.textContent = 'Input Mode: 🎙️ Voice';
    badge.className = 'input-mode-tag mode-voice';
  } else {
    badge.textContent = 'Input Mode: ⌨️ Text';
    badge.className = 'input-mode-tag mode-text';
  }
}

function clearQuestionText() {
  const qInput = document.getElementById('questionInput');
  if (qInput) {
    qInput.value = '';
    qInput.focus();
  }
  const msg = document.getElementById('generateStatusMsg');
  if (msg) msg.textContent = '';
}

function applySuggestion(questionText) {
  const qInput = document.getElementById('questionInput');
  if (qInput) {
    qInput.value = questionText;
    currentInputMode = 'text';
    updateInputModeTag('text');
    triggerGenerateSql();
  }
}

function onDatasetChange(tableName) {
  const label = document.getElementById('activeDbProfileLabel');
  if (label) {
    if (tableName === 'academic') {
      label.textContent = 'AcademicDB Profile (Relational)';
    } else {
      label.textContent = `Custom Dataset: ${tableName}`;
    }
  }
  // If question is already present, regenerate SQL for the newly selected dataset
  const q = document.getElementById('questionInput')?.value.trim();
  if (q) {
    triggerGenerateSql();
  }
}

/**
 * Step 1: Natural Language Interpretation -> SQL Generation (NO EXECUTION)
 */
async function triggerGenerateSql() {
  const qInput = document.getElementById('questionInput');
  const question = qInput ? qInput.value.trim() : '';
  const statusMsg = document.getElementById('generateStatusMsg');
  const datasetSelect = document.getElementById('datasetSelect');
  const tableName = datasetSelect ? datasetSelect.value : 'academic';

  if (!question) {
    if (statusMsg) statusMsg.textContent = 'Please enter or speak a question first.';
    qInput?.focus();
    return;
  }

  if (statusMsg) statusMsg.textContent = 'Interpreting question & matching schema...';

  try {
    const res = await fetch('/api/generate-sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, table_name: tableName })
    });

    const data = await res.json();

    const sqlEditor = document.getElementById('sqlEditor');
    const descTag = document.getElementById('queryIntentDesc');
    const astBadge = document.getElementById('astGovernanceBadge');
    const astText = document.getElementById('astBadgeText');
    const planDrawer = document.getElementById('planDrawer');

    if (data.status === 'success' && data.sql) {
      if (sqlEditor) sqlEditor.value = data.sql;
      if (descTag) descTag.textContent = data.description || 'Schema Matched';
      if (statusMsg) statusMsg.textContent = 'SQL generated successfully! Review below before running.';

      // Pre-validate via AST check
      triggerValidateSql(false);
    } else {
      // Clear any previous SQL to prevent stale execution
      if (sqlEditor) sqlEditor.value = '';
      if (descTag) descTag.textContent = 'Awaiting Valid Query';

      // Reset AST Badge to unvalidated state
      if (astBadge && astText) {
        astBadge.className = 'ast-badge';
        astText.textContent = 'AST Gateway: Awaiting Query';
      }

      // Hide execution plan drawer
      if (planDrawer) planDrawer.classList.add('hidden');

      const message = data.message || data.description || 'Please ask a question about the connected database.';
      if (statusMsg) statusMsg.textContent = message;

      let feedbackType = 'warning';
      if (data.status === 'out_of_scope') feedbackType = 'info';
      else if (data.status === 'unsupported') feedbackType = 'danger';

      let suggestionsHtml = '';
      if (data.suggestions && data.suggestions.length > 0) {
        suggestionsHtml = '<div style="margin-top: 8px; font-size: 11px;"><strong>Suggestions:</strong> ' +
          data.suggestions.map(s => `<a href="javascript:void(0)" onclick="applySuggestion('${escapeHtml(s)}')" style="text-decoration: underline; margin-right: 8px; color: inherit;">"${escapeHtml(s)}"</a>`).join(' ') +
          '</div>';
      }

      showValidationFeedback(message + suggestionsHtml, feedbackType);
    }
  } catch (err) {
    console.error('Error generating SQL:', err);
    if (statusMsg) statusMsg.textContent = 'Network or API error generating SQL.';
  }
}

function onSqlEdited() {
  const astBadge = document.getElementById('astGovernanceBadge');
  const astText = document.getElementById('astBadgeText');
  if (astBadge && astText) {
    astText.textContent = 'SQL Modified &bull; Validation Pending';
    astBadge.className = 'ast-badge badge-pending';
  }
}

/**
 * Step 2: AST Governance & SQL Validation
 */
async function triggerValidateSql(showAlert = true) {
  const sql = document.getElementById('sqlEditor')?.value.trim();
  const datasetSelect = document.getElementById('datasetSelect');
  const tableName = datasetSelect ? datasetSelect.value : 'academic';
  const astBadge = document.getElementById('astGovernanceBadge');
  const astText = document.getElementById('astBadgeText');

  if (!sql) {
    showValidationFeedback('SQL query editor is empty. Please enter or generate SQL first.', 'warning');
    return false;
  }

  try {
    const res = await fetch('/api/validate-sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql, table_name: tableName })
    });

    const data = await res.json();

    if (data.valid) {
      if (astBadge && astText) {
        astBadge.className = 'ast-badge badge-valid';
        astText.textContent = 'AST Validated &bull; Read-Only SELECT &bull; Safe';
      }
      showValidationFeedback('Abstract Syntax Tree (AST) validation passed: Query is strictly a read-only SELECT statement with automatic LIMIT governance.', 'success');
      return true;
    } else {
      if (astBadge && astText) {
        astBadge.className = 'ast-badge badge-invalid';
        astText.textContent = 'AST Blocked: Policy Violation';
      }
      showValidationFeedback(`AST Security Rejection: ${data.reason}`, 'danger');
      return false;
    }
  } catch (err) {
    console.error('Validation error:', err);
    if (astBadge && astText) {
      astBadge.className = 'ast-badge badge-invalid';
      astText.textContent = 'Validation Endpoint Error';
    }
    return false;
  }
}

/**
 * Step 3: Database Execution & Result Presentation
 */
async function triggerExecuteSql() {
  const sql = document.getElementById('sqlEditor')?.value.trim();
  const question = document.getElementById('questionInput')?.value.trim();
  const datasetSelect = document.getElementById('datasetSelect');
  const tableName = datasetSelect ? datasetSelect.value : 'academic';

  if (!sql) {
    showValidationFeedback('No SQL statement to execute. Speak or generate a query first.', 'warning');
    return;
  }

  // Pre-execution AST check
  const isValid = await triggerValidateSql(false);
  if (!isValid) {
    showValidationFeedback('Execution halted: The query violates security policies or is syntactically invalid.', 'danger');
    return;
  }

  // Set running state in telemetry
  setTelemetry('Running...', '--', 'Running', 'badge-tel-running');

  try {
    const res = await fetch('/api/execute-sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sql: sql,
        question: question,
        input_mode: currentInputMode,
        table_name: tableName
      })
    });

    const data = await res.json();

    if (data.error) {
      setTelemetry(`${data.execution_ms || 0}ms`, '0', 'Error', 'badge-tel-danger');
      showValidationFeedback(`Execution Error: ${data.error}`, 'danger');
      renderResults([], [], data.error);
      return;
    }

    // Success: Update telemetry
    setTelemetry(`${data.execution_ms}ms`, `${data.row_count} rows`, 'Authorized (200 OK)', 'badge-tel-success');
    lastVerbalSummary = data.verbal_summary || '';

    // Show/hide listen button
    const ttsItem = document.getElementById('ttsItem');
    if (ttsItem) {
      ttsItem.style.display = lastVerbalSummary ? 'inline-block' : 'none';
    }

    // Render Tabular Data
    renderResults(data.columns, data.rows, null);

    // Render Chart if available
    if (data.chart) {
      renderChart(data.chart);
      document.getElementById('resultsViewTabs').style.display = 'flex';
    } else {
      document.getElementById('resultsViewTabs').style.display = 'none';
      switchResultsTab('table');
    }

    showValidationFeedback(`Successfully executed query in ${data.execution_ms}ms. Retrieved ${data.row_count} records.`, 'success');

  } catch (err) {
    console.error('Execution error:', err);
    setTelemetry('Failed', '--', 'Network Error', 'badge-tel-danger');
    showValidationFeedback(`Network error communicating with database engine: ${err.message}`, 'danger');
  }
}

function setTelemetry(latency, rows, status, badgeClass) {
  const telLatency = document.getElementById('telLatency');
  const telRows = document.getElementById('telRows');
  const telStatus = document.getElementById('telStatus');

  if (telLatency) telLatency.textContent = latency;
  if (telRows) telRows.textContent = rows;
  if (telStatus) {
    telStatus.textContent = status;
    telStatus.className = `tel-value ${badgeClass}`;
  }
}

function showValidationFeedback(message, type = 'info') {
  const box = document.getElementById('validationFeedbackBox');
  const msgEl = document.getElementById('vfbMessage');
  const iconEl = document.getElementById('vfbIcon');

  if (!box || !msgEl) return;

  box.classList.remove('hidden', 'vfb-success', 'vfb-warning', 'vfb-danger');

  if (type === 'success') {
    box.classList.add('vfb-success');
    if (iconEl) iconEl.textContent = '✅';
  } else if (type === 'warning') {
    box.classList.add('vfb-warning');
    if (iconEl) iconEl.textContent = '⚠️';
  } else if (type === 'danger') {
    box.classList.add('vfb-danger');
    if (iconEl) iconEl.textContent = '🛑';
  } else {
    if (iconEl) iconEl.textContent = 'ℹ️';
  }

  msgEl.textContent = message;
}

function renderResults(columns, rows, error) {
  const placeholder = document.getElementById('emptyStatePlaceholder');
  const table = document.getElementById('resultsTable');
  const thead = document.getElementById('resultsTableHead');
  const tbody = document.getElementById('resultsTableBody');

  if (!table || !thead || !tbody) return;

  if (error || !rows || rows.length === 0) {
    table.classList.add('hidden');
    if (placeholder) {
      placeholder.classList.remove('hidden');
      placeholder.innerHTML = error
        ? `<div class="placeholder-icon">❌</div><div class="placeholder-title">Query Execution Failed</div><p class="placeholder-text">${escapeHtml(error)}</p>`
        : `<div class="placeholder-icon">🔍</div><div class="placeholder-title">0 Matching Records Found</div><p class="placeholder-text">The query executed successfully but returned an empty result set.</p>`;
    }
    return;
  }

  if (placeholder) placeholder.classList.add('hidden');
  table.classList.remove('hidden');

  // Render Table Head
  let thHtml = '<tr><th style="width: 48px;">#</th>';
  for (const col of columns) {
    thHtml += `<th>${escapeHtml(col.replace(/_/g, ' ').toUpperCase())}</th>`;
  }
  thHtml += '</tr>';
  thead.innerHTML = thHtml;

  // Render Table Body
  let tbHtml = '';
  rows.forEach((row, idx) => {
    tbHtml += `<tr><td class="row-num">${idx + 1}</td>`;
    for (const col of columns) {
      const val = row[col];
      const displayVal = (val === null || val === undefined) ? '<span class="null-val">NULL</span>' : escapeHtml(String(val));
      tbHtml += `<td>${displayVal}</td>`;
    }
    tbHtml += '</tr>';
  });
  tbody.innerHTML = tbHtml;
}

function renderChart(chartConfig) {
  const canvas = document.getElementById('resultsChartCanvas');
  if (!canvas) return;

  if (currentChartInstance) {
    currentChartInstance.destroy();
  }

  try {
    currentChartInstance = new Chart(canvas, {
      type: chartConfig.type || 'bar',
      data: {
        labels: chartConfig.labels,
        datasets: chartConfig.datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top' }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  } catch (err) {
    console.error('Failed to instantiate Chart.js:', err);
  }
}

function switchResultsTab(tab) {
  const btnTable = document.getElementById('tabBtnTable');
  const btnChart = document.getElementById('tabBtnChart');
  const tableContainer = document.getElementById('tableContainer');
  const chartContainer = document.getElementById('chartContainer');

  if (tab === 'chart') {
    btnChart?.classList.add('active');
    btnTable?.classList.remove('active');
    chartContainer?.classList.remove('hidden');
    tableContainer?.classList.add('hidden');
  } else {
    btnTable?.classList.add('active');
    btnChart?.classList.remove('active');
    tableContainer?.classList.remove('hidden');
    chartContainer?.classList.add('hidden');
  }
}

function playResultsAudio() {
  if (!lastVerbalSummary) return;

  const readoutBtn = document.getElementById('voiceReadoutBtn');
  if (readoutBtn) readoutBtn.textContent = '🔊 Synthesizing...';

  // Call neural TTS endpoint
  const audio = new Audio(`/api/tts?text=${encodeURIComponent(lastVerbalSummary)}`);
  audio.play()
    .then(() => {
      if (readoutBtn) readoutBtn.textContent = '🔊 Playing Audio';
      audio.onended = () => {
        if (readoutBtn) readoutBtn.textContent = '🔊 Listen';
      };
    })
    .catch((err) => {
      console.warn('TTS playback error, trying client-side SpeechSynthesis fallback:', err);
      // Fallback to browser SpeechSynthesis
      if (window.speechSynthesis) {
        const utter = new SpeechSynthesisUtterance(lastVerbalSummary);
        window.speechSynthesis.speak(utter);
        utter.onend = () => {
          if (readoutBtn) readoutBtn.textContent = '🔊 Listen';
        };
      }
    });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Step 4: Query Execution Plan (EXPLAIN QUERY PLAN) Analysis
 */
async function triggerExplainSql() {
  const sql = document.getElementById('sqlEditor')?.value.trim();
  const datasetSelect = document.getElementById('datasetSelect');
  const tableName = datasetSelect ? datasetSelect.value : 'academic';
  const drawer = document.getElementById('planDrawer');
  const chipsContainer = document.getElementById('planSummaryChips');
  const listContainer = document.getElementById('planStepsList');

  if (!sql) {
    showValidationFeedback('Please enter or generate a SQL statement before explaining its execution plan.', 'warning');
    return;
  }

  showValidationFeedback('Analyzing query execution plan against DBMS query optimizer...', 'info');

  try {
    const res = await fetch('/api/explain-sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql, table_name: tableName })
    });

    const data = await res.json();

    if (data.status === 'success' && data.steps) {
      if (drawer) drawer.classList.remove('hidden');

      // Populate summary chips
      if (chipsContainer) {
        const opt = data.summary.optimization_level || 'Normal';
        const tables = (data.summary.tables_accessed || []).join(', ') || 'None';
        chipsContainer.innerHTML = `
          <span class="plan-chip plan-chip-opt">${escapeHtml(opt)}</span>
          ${data.summary.has_temp_btree ? '<span class="plan-chip plan-chip-btree">Temp B-Tree Sort</span>' : ''}
          <span class="plan-chip plan-chip-tables">Tables: ${escapeHtml(tables)}</span>
        `;
      }

      // Populate execution plan step nodes
      if (listContainer) {
        listContainer.innerHTML = data.steps.map((st) => {
          let itemClass = 'plan-step-item';
          if (st.step_type === 'INDEX_SEARCH') itemClass += ' step-search';
          else if (st.step_type === 'TEMP_BTREE_SORT') itemClass += ' step-btree';

          return `
            <div class="${itemClass}">
              <span class="plan-step-type">${escapeHtml(st.step_type)}</span>
              <span class="plan-step-detail">${escapeHtml(st.detail)}</span>
            </div>
          `;
        }).join('');
      }

      showValidationFeedback(`Query plan computed successfully: ${data.steps.length} execution tree step(s) identified.`, 'success');
    } else {
      showValidationFeedback(`Failed to explain query: ${data.error || 'Unknown error'}`, 'danger');
    }
  } catch (err) {
    console.error('Explain plan error:', err);
    showValidationFeedback(`Network error explaining plan: ${err.message}`, 'danger');
  }
}

