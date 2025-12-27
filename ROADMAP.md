# 🚀 DynoCode Roadmap: Building the Ultimate Coding Platform

Goal: Become the single destination for coding practice by offering unique, real-world, and visually engaging experiences that competitors lack.

---

## 🏗 Phase 1: Foundation & Persistence (Immediate)
*Focus: Robustness and allowing users to practice from any device.*

1.  **Database-Backed Progress** (Critical 🚨)
    *   **Current State:** Progress is stored in browser `localStorage`. If a user switches laptops, progress is lost.
    *   **Action:** Create a `Submissions` table. Store every successful/failed run linked to the `User`.
    *   **Result:** "Resume where you left off" from any device.

2.  **Structured Curriculums (Tracks)**
    *   **Current State:** Flat list of problems based on efficiency.
    *   **Action:** Add `Track` and `Module` tables (e.g., "Python Basics", "Blind 75", "Data Structures 101").
    *   **Result:** Users follow a guided path rather than a random list.

3.  **Multi-Language Runners**
    *   **Action:** Dockerize the runner to safely support **Java, C++, JavaScript, and Go**.
    *   **Result:** Capture a much wider audience beyond Python devs.

---

## ✨ Phase 2: Differentiation (The "Wow" Factor)
*Focus: Features that make DynoCode unique compared to LeetCode.*

4.  **🌈 Algorithm Visualizer (Unique Value)**
    *   **Concept:** Don't just show `Passed/Failed`. Show the array sorting in real-time or the tree nodes moving.
    *   **Action:** Integrate a library like `pythontutor` or build a React-based visualizer for standard data structures.
    *   **Result:** Appeals heavily to visual learners and beginners.

5.  **🤖 AI "Socratic" Mentor**
    *   **Concept:** Instead of giving the answer, the AI asks guiding questions based on the user's current code error.
    *   **Action:** dedicated "Get Hint" button powered by LLM (Gemini/GPT) that sees your code/error and gives a *nudge*, not a solution.

6.  **Real-World "Micro-Projects"**
    *   **Concept:** Most sites do "Invert Binary Tree". We will do "Build a Rate Limiter" or "Write a JSON Parser".
    *   **Action:** multi-file problem support where users build mini-systems.

---

## 🎮 Phase 3: Gamification & Community
*Focus: Retention and Addiction.*

7.  **Streaks & Heatmaps**
    *   Github-style contribution graph on the profile.
    *   "7-day Streak" badges.

8.  **Leaderboards & Leagues**
    *   Weekly leagues (Bronze, Silver, Gold).
    *   Friends leaderboard (add friends by username).

9.  **Live 1v1 Battles**
    *   Real-time multiplayer where two users race to solve the same problem.
    *   Spectator mode.

---

## 🛠 Phase 4: Professional & Monetization
*Focus: Career growth.*

10. **Mock Interviews**
    *   Peer-to-peer integrated video call mock interviews.
    *   Rubrics for grading each other.

11. **System Design Sandbox**
    *   Interactive whiteboard to draw system architectures (Load Balancers, DBs) and "simulate" traffic.

---

## 📅 Suggested Next Step:
**Implement Database Progress tracking.** Without this, users cannot safely rely on DynoCode as their "single place" because clearing browser cookies wipes their data.
