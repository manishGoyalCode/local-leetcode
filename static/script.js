/* ======================================================
   GLOBAL STATE
====================================================== */

let editor = null;
let isRunning = false;

/* ======================================================
   CONSTANTS
====================================================== */

const MONACO_CDN = "https://unpkg.com/monaco-editor@0.45.0/min/vs";

const EDITOR_CONFIG = {
  language: "python",
  theme: "vs-dark",

  /* Typography */
  fontSize: 15,
  fontFamily: "JetBrains Mono, Fira Code, monospace",
  lineHeight: 22,

  /* Layout */
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  smoothScrolling: true,
  automaticLayout: true,
  padding: { top: 12 },

  /* Editing */
  autoIndent: "full",
  formatOnPaste: true,
  formatOnType: true,
  tabSize: 4,
  insertSpaces: true,
  wordWrap: "on",

  /* Visual Guides */
  lineNumbers: "on",
  renderIndentGuides: true,
  guides: { indentation: true },

  /* Cursor & UX */
  cursorBlinking: "smooth",
  cursorSmoothCaretAnimation: true,

  /* Suggestions */
  quickSuggestions: {
    other: true,
    comments: false,
    strings: false
  },
  suggestOnTriggerCharacters: true,

  /* Reduce Noise */
  hover: { delay: 800 }
};

/* ======================================================
   DOM HELPERS
====================================================== */

function getRunButton() {
  return document.getElementById("run-btn");
}

function getOutputContainer() {
  return document.getElementById("output");
}

function getEditorContainer() {
  return document.getElementById("editor");
}

/* ======================================================
   MONACO INITIALIZATION
====================================================== */

function loadMonaco() {
  require.config({ paths: { vs: MONACO_CDN } });

  require(["vs/editor/editor.main"], () => {
    createEditor();
    focusEditor();
  });
}

function createEditor() {
  editor = monaco.editor.create(getEditorContainer(), {
    value: INITIAL_CODE,
    ...EDITOR_CONFIG
  });
}

function focusEditor() {
  /* Place cursor inside solve() */
  editor.revealLineInCenter(1);
  editor.setPosition({ lineNumber: 3, column: 5 });
  editor.focus();
}

/* ======================================================
   RUN CODE FLOW
====================================================== */

function runCode() {
  if (isRunning) return;

  isRunning = true;
  updateRunButton(true);
  showRunningState();

  formatEditorCode();

  const code = editor.getValue();
  showBeginnerWarning(code);

  executeCode(code)
    .then(renderTestResults)
    .catch(showSystemError)
    .finally(resetRunState);
}

function executeCode(code) {
  return fetch("/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code,
      problem_id: PROBLEM_ID
    })
  }).then(res => res.json());
}

/* ======================================================
   UI STATE HELPERS
====================================================== */

function updateRunButton(isLoading) {
  const btn = getRunButton();
  btn.disabled = isLoading;
  btn.innerText = isLoading ? "Running..." : "▶ Run";
}

function showRunningState() {
  const output = getOutputContainer();
  output.className = "";
  output.innerHTML = "<div class='muted'>⏳ Running test cases...</div>";
}

function resetRunState() {
  isRunning = false;
  updateRunButton(false);
}

/* ======================================================
   EDITOR HELPERS
====================================================== */

function formatEditorCode() {
  editor.getAction("editor.action.formatDocument").run();
}

function showBeginnerWarning(code) {
  if (code.includes("print(")) {
    alert("⚠️ Use return instead of print() inside solve()");
  }
}

/* ======================================================
   RESULT RENDERING
====================================================== */

function renderTestResults(data) {
  const output = getOutputContainer();
  output.innerHTML = "";
  output.className = "";

  data.details.forEach(test => {
    output.appendChild(createTestRow(test));
  });

  output.classList.add(data.passed ? "success" : "failure");
}

function createTestRow(test) {
  const row = document.createElement("div");
  row.classList.add("test-line");

  if (test.status === "passed") {
    row.classList.add("test-pass");
    row.innerText = `Test Case ${test.index} ✓ Passed`;
  }

  else if (test.status === "failed") {
    row.classList.add("test-fail");
    row.innerHTML = `
      Test Case ${test.index} ✗ Failed<br>
      <span><b>Input:</b> ${JSON.stringify(test.input)}</span><br>
      <span><b>Expected:</b> ${test.expected}</span><br>
      <span><b>Got:</b> ${test.got}</span>
    `;
  }

  else if (test.status === "error") {
    row.classList.add("test-error");
    row.innerHTML = `
      Test Case ${test.index} ⚠ Error<br>
      ${test.input ? `<span><b>Input:</b> ${JSON.stringify(test.input)}</span><br>` : ""}
      <span>${test.error}</span>
    `;
  }

  return row;
}

function showSystemError(err) {
  const output = getOutputContainer();
  output.className = "error";
  output.innerText = "❌ System Error\n\n" + err;
}

/* ======================================================
   RESET
====================================================== */

function resetCode() {
  editor.setValue(INITIAL_CODE);
  editor.focus();
}

/* ======================================================
   SHORTCUTS & EVENTS
====================================================== */

function registerShortcuts() {
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      runCode();
    }
  });
}

/* ======================================================
   BOOTSTRAP
====================================================== */

loadMonaco();
registerShortcuts();
