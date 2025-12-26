/* ======================================================
   GLOBAL STATE
   ====================================================== */

let editor = null;
let isRunning = false;
let currentUserId = null;

/* ======================================================
   SIDEBAR CONTROLS
   ====================================================== */

function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar");
  sidebar.classList.toggle("open");

  // Close when clicking a link (mobile only)
  if (window.innerWidth <= 768) {
    const links = document.querySelectorAll(".problem-link");
    links.forEach(link => {
      link.addEventListener("click", () => {
        sidebar.classList.remove("open");
      });
    });
  }
}

function toggleDesktopSidebar() {
  const sidebar = document.getElementById("sidebar");
  const showBtn = document.getElementById("show-sidebar-btn");

  // Force removal of manual width so CSS class works
  sidebar.style.width = "";

  // Toggle class
  sidebar.classList.toggle("collapsed");

  // Check current state
  const isCollapsed = sidebar.classList.contains("collapsed");

  // Update Button Visibility
  if (showBtn) {
    showBtn.style.display = isCollapsed ? "block" : "none";
  }

  // Save to LocalStorage
  localStorage.setItem("sidebar_collapsed", isCollapsed);
}

/* ======================================================
   RESIZABLE PANELS
   ====================================================== */

/* ======================================================
   OUTPUT TOGGLE
   ====================================================== */

function toggleOutputPanel() {
  const panel = document.getElementById("output-panel");
  panel.classList.toggle("collapsed");
}

function expandOutputPanel() {
  const panel = document.getElementById("output-panel");
  panel.classList.remove("collapsed");
}

function initResizers() {
  const sidebar = document.getElementById("sidebar");
  const resizerSidebar = document.getElementById("resizer-sidebar");

  const problemPanel = document.querySelector(".problem-panel");
  const resizerPanel = document.getElementById("resizer-panel");
  const editorPanel = document.querySelector(".editor-panel");

  const container = document.querySelector(".container");
  const resizerOutput = document.getElementById("resizer-output");
  const outputPanel = document.querySelector(".output-panel");

  // Default to collapsed on load to save space
  outputPanel.classList.add("collapsed");

  // 1. Sidebar Resizer
  if (resizerSidebar) {
    resizerSidebar.addEventListener("mousedown", (e) => {
      e.preventDefault();
      document.addEventListener("mousemove", resizeSidebar);
      document.addEventListener("mouseup", stopResizeSidebar);
      resizerSidebar.classList.add("resizing");
    });
  }

  function resizeSidebar(e) {
    const newWidth = e.clientX;
    if (newWidth > 150 && newWidth < 500) {
      sidebar.style.width = newWidth + "px";
    }
  }

  function stopResizeSidebar() {
    document.removeEventListener("mousemove", resizeSidebar);
    document.removeEventListener("mouseup", stopResizeSidebar);
    resizerSidebar.classList.remove("resizing");
  }

  // 2. Panel Split (Problem vs Editor)
  if (resizerPanel) {
    resizerPanel.addEventListener("mousedown", (e) => {
      e.preventDefault();
      document.addEventListener("mousemove", resizePanel);
      document.addEventListener("mouseup", stopResizePanel);
      resizerPanel.classList.add("resizing");
    });
  }

  function resizePanel(e) {
    // Calculate percentage width relative to container
    const containerWidth = container.offsetWidth;
    const x = e.clientX - sidebar.getBoundingClientRect().right;
    const newPercent = (x / containerWidth) * 100;

    if (newPercent > 20 && newPercent < 80) {
      problemPanel.style.width = `${newPercent}%`;
      editorPanel.style.width = `${100 - newPercent}%`;
    }
  }

  function stopResizePanel() {
    document.removeEventListener("mousemove", resizePanel);
    document.removeEventListener("mouseup", stopResizePanel);
    resizerPanel.classList.remove("resizing");
    if (editor) editor.layout(); // Refresh Monaco
  }

  // 3. Output Resizer (Height)
  if (resizerOutput) {
    resizerOutput.addEventListener("mousedown", (e) => {
      e.preventDefault();
      document.addEventListener("mousemove", resizeOutput);
      document.addEventListener("mouseup", stopResizeOutput);
      resizerOutput.classList.add("resizing");
    });
  }

  function resizeOutput(e) {
    const windowHeight = window.innerHeight;
    const newHeight = windowHeight - e.clientY;

    if (newHeight > 50 && newHeight < windowHeight * 0.6) {
      outputPanel.style.height = newHeight + "px";
      container.style.height = `calc(100vh - 58px - ${newHeight}px)`;
      outputPanel.classList.remove("collapsed"); // Auto-expand on manual resize
    }
  }

  function stopResizeOutput() {
    document.removeEventListener("mousemove", resizeOutput);
    document.removeEventListener("mouseup", stopResizeOutput);
    resizerOutput.classList.remove("resizing");
    if (editor) editor.layout();
  }
}

function initSidebarState() {
  const isCollapsed = localStorage.getItem("sidebar_collapsed") === "true";
  const sidebar = document.getElementById("sidebar");
  const showBtn = document.getElementById("show-sidebar-btn");

  if (isCollapsed && sidebar) {
    sidebar.classList.add("collapsed");
    if (showBtn) showBtn.style.display = "block";
  }
}

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
   USER IDENTITY
   ====================================================== */

/* ======================================================
   COMMON ACTIONS
   ====================================================== */

function switchTrack(trackId) {
  if (!trackId) return;
  fetch(`/switch_track/${trackId}`)
    .then(res => res.json())
    .then(data => {
      if (data.status === "ok") {
        window.location.reload();
      } else {
        alert("Failed to switch track");
      }
    });
}
/* ======================================================
   USER IDENTITY
   ====================================================== */

function initUser() {
  let uid = localStorage.getItem("user_id");
  if (!uid) {
    uid = "user_" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem("user_id", uid);
  }
  currentUserId = uid;
  document.cookie = `user_id=${uid}; path=/; max-age=31536000`; // 1 year
  console.log("👤 User ID:", uid);
}

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
  initUser(); // Initialize user
  initProgress(); // Initialize sidebar status
  initSidebarState(); // Restore sidebar state
  initResizers(); // Enable drag resizing
  require.config({ paths: { vs: MONACO_CDN } });

  require(["vs/editor/editor.main"], () => {
    createEditor();
    focusEditor();
  });
}

function createEditor() {
  const savedCode = localStorage.getItem(`code_${PROBLEM_ID}`);

  editor = monaco.editor.create(getEditorContainer(), {
    value: savedCode || INITIAL_CODE,
    ...EDITOR_CONFIG
  });

  if (savedCode) {
    showToast("Draft restored");
  }

  // Auto-Save Listener
  editor.onDidChangeModelContent(() => {
    const currentCode = editor.getValue();
    localStorage.setItem(`code_${PROBLEM_ID}`, currentCode);
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

  expandOutputPanel(); // Auto-show results

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

  if (data.passed) {
    if (typeof PROBLEM_ID !== 'undefined') {
      markProblemSolved(PROBLEM_ID);
    }
  }
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
  if (confirm("Reset code to default? Your changes will be lost.")) {
    editor.setValue(INITIAL_CODE);
    localStorage.removeItem(`code_${PROBLEM_ID}`);
    editor.focus();
  }
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.innerText = msg;
  toast.style.position = "fixed";
  toast.style.bottom = "20px";
  toast.style.right = "20px";
  toast.style.background = "var(--green)";
  toast.style.color = "#000";
  toast.style.padding = "8px 16px";
  toast.style.borderRadius = "4px";
  toast.style.fontWeight = "bold";
  toast.style.opacity = "0";
  toast.style.transition = "opacity 0.3s";
  toast.style.zIndex = "1000";

  document.body.appendChild(toast);

  // Fade in
  requestAnimationFrame(() => toast.style.opacity = "1");

  // Fade out
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 2000);
}

/* ======================================================
   CLIENT-SIDE PROGRESS
====================================================== */

function initProgress() {
  // Apply checks to sidebar based on localStorage
  const solved = JSON.parse(localStorage.getItem("solved_problems") || "[]");

  // Find sidebar links and add checkmark
  const links = document.querySelectorAll(".sidebar a.problem-link");
  links.forEach(link => {
    //Extract ID from href /problem/abc
    const href = link.getAttribute("href");
    const id = href.split("/").pop();

    if (solved.includes(id)) {
      // Check if already has checkmark to avoid double add
      if (!link.innerText.includes("✅")) {
        link.innerText = "✅ " + link.innerText;
      }
    }
  });
}

function markProblemSolved(id) {
  const solved = JSON.parse(localStorage.getItem("solved_problems") || "[]");

  if (!solved.includes(id)) {
    solved.push(id);
    localStorage.setItem("solved_problems", JSON.stringify(solved));

    // Log solve for stats (Dictionary: Date -> Count)
    const log = JSON.parse(localStorage.getItem("solve_log") || "{}");
    const today = new Date().toISOString().split('T')[0];
    log[today] = (log[today] || 0) + 1;
    localStorage.setItem("solve_log", JSON.stringify(log));

    showToast("🏆 Problem Solved! Progress Saved.");

    // Update Sidebar immediately
    initProgress();
  }
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
