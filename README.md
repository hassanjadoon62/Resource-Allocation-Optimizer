# Resource Allocation Optimizer Using Minimax with Payoff

**Student Name:** Hassan Muavia Jadoon
**Project Title:** Resource Allocation Optimizer Using Minimax with Payoff
**Programming Language:** Python 3
**GUI Framework:** Tkinter
**Difficulty Level:** Advanced

---

## 1. Project Description

A company has a limited budget and multiple projects competing for that
funding. This desktop application helps a decision-maker allocate the
available budget intelligently by applying the **Minimax with Payoff**
decision-making algorithm.

The user enters company information and a list of candidate projects, each
with a requested budget, an expected payoff, and an optional risk level. The
application then:

1. Builds **four candidate allocation strategies** (different budgeting
   philosophies).
2. Evaluates every strategy under **three possible future scenarios**
   (Best Case, Expected Case, Worst Case) to produce a **Payoff Matrix**.
3. Applies the **Minimax (maximin) decision rule** to that matrix to find
   the strategy that **guarantees the best possible worst-case payoff** —
   i.e. the option that minimizes the company's maximum possible loss.
4. Displays the payoff matrix, worst-case payoff per strategy, the selected
   strategy, the recommended budget allocation, and the final decision.

---

## 2. Algorithm Explanation — Minimax with Payoff

The **Minimax with Payoff** rule (also known as Wald's maximin criterion in
decision theory) is used when a decision-maker must choose between several
options ("strategies") without knowing for certain which future condition
("scenario" / state of nature) will actually occur. The rule is
pessimistic: it assumes the worst-case scenario could always happen, and
therefore picks the strategy that performs best under *its own* worst case.

### How it is applied in this project

**Step 1 — Generate Strategies.** Four allocation strategies are built from
the entered projects:

| Strategy | Idea |
|---|---|
| Max Payoff First | Fully fund the highest expected-payoff projects first, in descending order, until the budget runs out. |
| Min Risk First | Fully fund the lowest-risk projects first (Low → Medium → High), then by payoff as a tiebreaker. |
| Balanced (Score-Weighted) | Distribute the budget proportionally to each project's payoff-per-dollar, weighted by its risk factor. |
| Equal Distribution | Split the budget equally across all projects, capped at each project's own request. |

**Step 2 — Generate Scenarios.** Three states of nature are considered,
each of which scales a project's expected payoff depending on its risk
level (higher-risk projects swing further in both directions):

| Risk Level | Best Case | Expected Case | Worst Case |
|---|---|---|---|
| Low | ×1.05 | ×1.00 | ×0.90 |
| Medium | ×1.15 | ×1.00 | ×0.70 |
| High | ×1.30 | ×1.00 | ×0.45 |

**Step 3 — Build the Payoff Matrix.** For every (strategy, scenario) pair,
the total realised payoff is computed as:

```
payoff(strategy, scenario) = Σ over all projects of
    ( allocated_amount / requested_budget ) × expected_payoff × scenario_multiplier(risk)
```

This produces a matrix such as:

```
Strategy                          Best Case    Expected Case    Worst Case
Max Payoff First                  168,750.00     135,000.00      72,000.00
Min Risk First                     147,916.67     131,666.67      99,166.67
Balanced (Score-Weighted)          160,215.72     138,078.78      95,446.61
Equal Distribution                 160,216.67     137,666.67      94,366.67
```

**Step 4 — Apply Minimax.** For each strategy (row), find its minimum value
across all scenarios (columns) — this is its *worst-case payoff*. Then pick
the strategy whose worst-case payoff is the **largest**:

```
worst_case(strategy) = min( payoff(strategy, scenario) for every scenario )
selected_strategy     = argmax( worst_case(strategy) for every strategy )
```

In the example above, "Min Risk First" has the highest worst-case payoff
(99,166.67), so it is selected — even though "Max Payoff First" has a
higher best-case ceiling, it also has a much worse floor (72,000.00), which
the minimax rule rejects in favor of guaranteed safety.

### Complexity Analysis

Let **N** = number of projects, **S** = number of strategies (fixed at 4),
**C** = number of scenarios (fixed at 3).

- **Time Complexity:** Building each strategy's allocation takes O(N log N)
  (for the sorting-based strategies) or O(N) (for proportional ones).
  Building the payoff matrix takes O(S × C × N). Applying minimax takes
  O(S × C). Since S and C are small constants, the overall complexity is
  **O(N log N)**, dominated by the sorting step.
- **Space Complexity:** The payoff matrix requires O(S × C) storage, and
  the project list and allocations require O(N). Overall: **O(N)**.

---

## 3. Folder Structure

```
ResourceAllocationOptimizer/
│
├── main.py          # Complete application source code (GUI + algorithm)
└── README.md        # This documentation file
```

The project is intentionally kept as a single, well-commented Python file
(`main.py`) so it can be opened and run directly with no missing imports
or external file dependencies, using only the Python standard library.

---

## 4. Requirements

- **Python Version:** Python 3.8 or newer (developed and tested on Python 3.12).
- **Libraries:** Only Python's built-in standard library is used:
  - `tkinter` (GUI toolkit — ships with standard Python installations)
  - `tkinter.ttk`, `tkinter.messagebox`, `tkinter.scrolledtext`
  - `dataclasses`
  - `typing`

  **No `pip install` is required.**

> **Note:** On some minimal Linux distributions, Tkinter is packaged
> separately from Python. If you see `ModuleNotFoundError: No module named
> 'tkinter'`, install it with:
> ```bash
> sudo apt-get install python3-tk      # Debian/Ubuntu
> sudo dnf install python3-tkinter     # Fedora
> ```
> Windows and macOS installers from python.org include Tkinter by default.

---

## 5. Installation & Running Instructions

1. Make sure Python 3.8+ is installed:
   ```bash
   python3 --version
   ```
2. Open the project folder in VS Code (or any editor/terminal).
3. Run the application:
   ```bash
   python3 main.py
   ```
   (On Windows, `python main.py` may be used instead.)
4. The GUI window will open — no further setup is required.

---

## 6. User Guide

1. **Enter Company Information:** Fill in the company name, total budget,
   and (optionally) how many projects you plan to add.
2. **Add Projects:** For each project, enter its name, requested budget,
   expected payoff, and an optional risk level (Low / Medium / High,
   defaults to Medium). Click **➕ Add Project**. The project appears in
   the scrollable table above the results panel.
3. Repeat step 2 for every competing project.
4. Click **🧮 Calculate Allocation**. The application will:
   - Validate the total budget and project data.
   - Build the payoff matrix.
   - Apply the Minimax with Payoff rule.
   - Display the full results (payoff matrix, worst-case payoffs, selected
     strategy, recommended allocation, and final decision) in the results
     panel, plus a summary pop-up message.
5. Click **🔄 Reset** at any time to clear all entered data and start over
   (a confirmation prompt will appear).
6. Click **🚪 Exit** to close the application (a confirmation prompt will
   appear).

Hover over several fields/buttons to see small tooltips with extra guidance.
The status bar at the bottom of the window always shows the result of the
last action (success or error).

---

## 7. Sample Input

| Company Name | Total Budget |
|---|---|
| Bright Future Technologies | 80,000 |

| Project Name | Requested Budget | Expected Payoff | Risk Level |
|---|---|---|---|
| Website Revamp | 20,000 | 35,000 | Low |
| AI Chatbot | 50,000 | 90,000 | High |
| Mobile App | 30,000 | 55,000 | Medium |
| Data Center Upgrade | 40,000 | 60,000 | Medium |

## 8. Sample Output (abridged)

```
PAYOFF MATRIX (rows = strategies, columns = scenarios)
Strategy                          Best Case    Expected Case    Worst Case
Max Payoff First                 $168,750.00     $135,000.00     $72,000.00
Min Risk First                   $147,916.67     $131,666.67     $99,166.67
Balanced (Score-Weighted)        $160,215.72     $138,078.78     $95,446.61
Equal Distribution               $160,216.67     $137,666.67     $94,366.67

WORST-CASE PAYOFF PER STRATEGY (Minimax criterion)
  Max Payoff First                            $72,000.00
  Min Risk First                              $99,166.67  <-- SELECTED (best worst-case)
  Balanced (Score-Weighted)                   $95,446.61
  Equal Distribution                          $94,366.67

SELECTED MINIMAX STRATEGY: Min Risk First

RECOMMENDED BUDGET ALLOCATION
Project                        Allocated       Requested    % Funded
Website Revamp                  $20,000.00      $20,000.00     100.0%
Data Center Upgrade             $40,000.00      $40,000.00     100.0%
Mobile App                      $20,000.00      $30,000.00      66.7%
AI Chatbot                           $0.00      $50,000.00       0.0%

FINAL OPTIMIZED DECISION
  Strategy chosen        : Min Risk First
  Guaranteed worst payoff: $99,166.67
  Total budget allocated : $80,000.00
  Budget left unallocated: $0.00
```

---

## 9. Python Concepts Demonstrated

- **Variables & Data Types:** strings, floats, ints, booleans throughout.
- **Strings:** formatting (`f"{value:,.2f}"`), `.strip()`, `.lower()`, string building for the results report.
- **Lists:** `self.projects`, sorted project orderings, report line lists.
- **Dictionaries:** strategies, payoff matrix, worst-case payoffs, scenario multipliers.
- **Tuples:** `SCENARIOS`, Treeview `columns` tuple, function return tuples.
- **Loops:** `for` loops over projects/strategies/scenarios; `while` loop in leftover-budget redistribution.
- **If-Else Statements:** input validation, budget checks, risk-level checks.
- **Functions:** small, single-purpose helper functions throughout (`format_currency`, `_validate_positive_float`, etc.).
- **Classes & OOP:** `Project`, `MinimaxOptimizer`, `ToolTip`, `ResourceAllocationApp` — encapsulation, single-responsibility methods.
- **Error Handling:** `try/except` blocks around all user-triggered actions, with specific `ValueError` handling plus a generic safety-net `except Exception`.
- **Modular Programming:** the algorithm (`MinimaxOptimizer`) is fully decoupled from the GUI (`ResourceAllocationApp`) and can be reused/tested independently.
- **Tkinter Widgets & Event Handling:** `Entry`, `Combobox`, `Treeview` with scrollbar, `ScrolledText`, `Button` with `command=`, `messagebox`, tooltips via `<Enter>`/`<Leave>` bindings.

---

## 10. Notes on Design Choices

- All monetary inputs are validated to be positive numbers; text inputs
  must be non-empty; risk level is restricted to Low/Medium/High via a
  read-only combobox to avoid typos.
- The project table and results panel are both scrollable to comfortably
  handle many projects and long reports.
- The window is resizable with a sensible minimum size, so the layout
  remains usable at different screen resolutions.
