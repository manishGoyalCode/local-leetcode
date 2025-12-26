# 🚀 DynoCode — Python Practice System (80/20 Focus)

A **local LeetCode-style coding practice platform** built with **Python + Flask**, designed to teach **core Python concepts practically** through **repetition and test-driven problem solving**.

> ✨ Clone → Run → Code → See test results → Track progress
> No accounts. No internet. No distractions.

---

## 🚀 Why This Project?

Most beginners struggle because:

* Too much theory
* No structure
* No feedback loop

This project solves that by:

* Focusing on **20% Python concepts used 80–90% of the time**
* Enforcing **return-based coding (no print hacks)**
* Showing **exact test failure details**
* Providing a **LeetCode-like coding UI locally**

---

## 🎯 Features

### ✅ Core

* 🧑‍💻 VS Code–like **Monaco Editor**
* ▶️ Run code with **real test cases**
* ❌ Clear failure output (input, expected, got)
* ✅ Per-test pass/fail breakdown
* 📁 Problem navigation sidebar
* 🧠 Auto-format before run
* ⌨️ Keyboard shortcut: `Ctrl / Cmd + Enter`
* 🔁 Reset code anytime

### 📈 Learning

* 7-Day structured Python curriculum
* 80/20 concept coverage
* Repetition-based practice
* Beginner-friendly guardrails

### 📊 Progress

* Solved problems tracked locally (`progress.json`)
* Solved problems highlighted in sidebar

---

## 📚 Curriculum (7 Days)

### 🗓️ Day 1 — Variables & Data Types

* Input/output
* Arithmetic
* Type conversion

### 🗓️ Day 2 — Conditions

* if / elif / else
* Comparisons
* Decision making

### 🗓️ Day 3 — Loops

* for / while
* Counting, iteration
* Mathematical logic

### 🗓️ Day 4 — Strings & Lists

* Indexing & slicing
* String manipulation
* List operations

### 🗓️ Day 5 — Dictionaries & Tuples

* Key-value data
* Frequency counting
* Merging & searching

### 🗓️ Day 6 — Functions

* Reusable logic
* Return values
* Problem decomposition

### 🗓️ Day 7 — Integrated Scenarios

* Signal Filtering
* ATM Logic
* Data Deduplication
* Student Management Systems

### 🗓️ Day 8 — Classic Algorithms

* Valid Anagram
* Missing Number
* Valid Parentheses
* Stock Trading Logic

### 🗓️ Day 9 — Modern Python 🆕

* List Comprehensions
* Lambda Functions
* Error Handling (Try/Except)
* Generators (Yield)

---

## 🛠️ Tech Stack

* **Python 3.9+**
* **Flask**
* **Monaco Editor**
* **Docker** (Optional containerization)
* HTML / CSS / JavaScript
* JSON-based problem engine

No database. No auth. Fully local.

---

## 📂 Project Structure

```
local-leetcode/
├── app.py
├── runner/
│   └── code_runner.py
├── problems/             # Generated JSON problem files
├── static/               # CSS and JS assets
├── templates/            # HTML templates
├── questions_config.json # Master curriculum configuration
├── generate_problems.py  # Script to compile config -> problem files
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Container orchestration
├── progress.json         # Local tracking of solved problems
└── README.md
```

---

## ⚙️ Setup Instructions

### Option 1: Docker (Recommended)

The easiest way to run the app without installing dependencies locally.

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/local-leetcode.git
   cd local-leetcode
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Open Browser**
   Go to `http://localhost:5001`

### Option 2: Local Python Setup

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate problem files**
   ```bash
   python generate_problems.py
   ```

4. **Run the app**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000`

---

## � Real-World Engineering Mindset

We have moved beyond abstract "toy problems." The curriculum is now designed to simulate **real engineering tasks**:

*   **Logic** becomes *Smart Switch Controllers* or *Secure Access Gates*.
*   **Loops** become *Network Packet Generators*.
*   **Strings** become *DNA Sequencers*.
*   **Dictionaries** become *Database Record Creators*.

### New Features 🚀
*   **Metadata**: Problems are tagged with topics (e.g., `#cryptography`, `#networking`).
*   **Difficulty Levels**: **Easy** and **Medium** badges help track progression.
*   **Hints System**: Stuck? Reveal actionable tips without giving away the answer.

---

## 🧪 How Problems Work

Each problem contextually places you in a developer's shoes:

*   **Context**: "Build a module to validate user passwords..."
*   **Input**: `username` (str), `password` (str)
*   **Output**: Boolean `True`/`False`

Example failure output:
```
Test Case 2 ✗ Failed
Input: "admin", "wrongpass"
Expected: False
Got: True
```

---

## 🏆 Who Is This For?

*   **Aspiring Engineers**: Learn Python through the lens of system design.
*   **Interview Preppers**: Practice standard algorithms (Day 8) in a distraction-free environment.
*   **Teachers**: A structured, self-contained lab for students.

---

## 🚀 Roadmap (Future Enhancements)

* [ ] **Day 9**: Modern Python (List Comprehensions, Lambda)
* [ ] **Day 10**: Data Hygiene & Validation
* [ ] Dark Mode toggle
* [ ] Export progress as PDF certificate

---

## 🤝 Contributing

PRs welcome for:

* New problems
* Bug fixes
* UI improvements
* Performance optimizations

---

## 📜 License

MIT License — free to use, modify, and share.

---

## ⭐ Final Note

If you’re serious about **learning by doing**, this system will take you from:

> *“I know Python syntax”*
> to
> *“I can solve problems confidently”*

Happy coding 🚀
