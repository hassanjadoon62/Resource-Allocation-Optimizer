import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class Project:
    name: str
    requested_budget: float
    expected_payoff: float
    risk_level: str = "Medium"

    def funded_fraction(self, allocated_amount: float) -> float:
        if self.requested_budget <= 0:
            return 0.0
        fraction = allocated_amount / self.requested_budget
        return min(max(fraction, 0.0), 1.0)


class MinimaxOptimizer:

    RISK_SCENARIO_MULTIPLIERS: Dict[str, Dict[str, float]] = {
        "Low":    {"Best Case": 1.05, "Expected Case": 1.00, "Worst Case": 0.90},
        "Medium": {"Best Case": 1.15, "Expected Case": 1.00, "Worst Case": 0.70},
        "High":   {"Best Case": 1.30, "Expected Case": 1.00, "Worst Case": 0.45},
    }

    SCENARIOS: Tuple[str, str, str] = ("Best Case", "Expected Case", "Worst Case")

    def __init__(self, projects: List[Project], total_budget: float):
        self.projects = projects
        self.total_budget = total_budget

        self.strategies: Dict[str, Dict[str, float]] = {}
        self.payoff_matrix: Dict[str, Dict[str, float]] = {}
        self.worst_case_payoff: Dict[str, float] = {}
        self.selected_strategy: str = ""

    def _allocate_in_order(self, ordered_projects: List[Project]) -> Dict[str, float]:
        allocation: Dict[str, float] = {}
        remaining_budget = self.total_budget

        for project in ordered_projects:
            if remaining_budget <= 0:
                allocation[project.name] = 0.0
                continue
            amount_to_give = min(project.requested_budget, remaining_budget)
            allocation[project.name] = amount_to_give
            remaining_budget -= amount_to_give

        return allocation

    def _allocate_proportionally(self, weights: Dict[str, float]) -> Dict[str, float]:
        allocation: Dict[str, float] = {p.name: 0.0 for p in self.projects}
        total_weight = sum(weights.values())

        if total_weight <= 0:
            return allocation

        remaining_budget = self.total_budget
        project_lookup = {p.name: p for p in self.projects}

        for name, weight in weights.items():
            share = self.total_budget * (weight / total_weight)
            capped_share = min(share, project_lookup[name].requested_budget)
            allocation[name] = capped_share
            remaining_budget -= capped_share

        still_open = [
            name for name in allocation
            if allocation[name] < project_lookup[name].requested_budget
        ]
        while remaining_budget > 0.01 and still_open:
            share_each = remaining_budget / len(still_open)
            progress_made = False
            for name in list(still_open):
                room_left = project_lookup[name].requested_budget - allocation[name]
                extra = min(share_each, room_left)
                if extra > 0:
                    allocation[name] += extra
                    remaining_budget -= extra
                    progress_made = True
                if allocation[name] >= project_lookup[name].requested_budget - 1e-9:
                    still_open.remove(name)
            if not progress_made:
                break

        return allocation

    def generate_strategies(self) -> Dict[str, Dict[str, float]]:
        strategies: Dict[str, Dict[str, float]] = {}

        by_payoff = sorted(self.projects, key=lambda p: p.expected_payoff, reverse=True)
        strategies["Max Payoff First"] = self._allocate_in_order(by_payoff)

        risk_rank = {"Low": 0, "Medium": 1, "High": 2}
        by_risk = sorted(
            self.projects,
            key=lambda p: (risk_rank.get(p.risk_level, 1), -p.expected_payoff)
        )
        strategies["Min Risk First"] = self._allocate_in_order(by_risk)

        risk_factor = {"Low": 1.2, "Medium": 1.0, "High": 0.8}
        score_weights = {}
        for p in self.projects:
            cost_effectiveness = (p.expected_payoff / p.requested_budget) if p.requested_budget > 0 else 0
            score_weights[p.name] = cost_effectiveness * risk_factor.get(p.risk_level, 1.0)
        strategies["Balanced (Score-Weighted)"] = self._allocate_proportionally(score_weights)

        equal_weights = {p.name: 1.0 for p in self.projects}
        strategies["Equal Distribution"] = self._allocate_proportionally(equal_weights)

        self.strategies = strategies
        return strategies

    def _compute_payoff_for_scenario(self, allocation: Dict[str, float], scenario: str) -> float:
        total_payoff = 0.0
        for project in self.projects:
            allocated_amount = allocation.get(project.name, 0.0)
            fraction_funded = project.funded_fraction(allocated_amount)
            multiplier = self.RISK_SCENARIO_MULTIPLIERS.get(
                project.risk_level, self.RISK_SCENARIO_MULTIPLIERS["Medium"]
            )[scenario]
            total_payoff += fraction_funded * project.expected_payoff * multiplier
        return total_payoff

    def build_payoff_matrix(self) -> Dict[str, Dict[str, float]]:
        payoff_matrix: Dict[str, Dict[str, float]] = {}
        for strategy_name, allocation in self.strategies.items():
            payoff_matrix[strategy_name] = {}
            for scenario in self.SCENARIOS:
                payoff_matrix[strategy_name][scenario] = self._compute_payoff_for_scenario(
                    allocation, scenario
                )
        self.payoff_matrix = payoff_matrix
        return payoff_matrix

    def apply_minimax(self) -> Tuple[Dict[str, float], str]:
        worst_case_payoff: Dict[str, float] = {}
        for strategy_name, scenario_payoffs in self.payoff_matrix.items():
            worst_case_payoff[strategy_name] = min(scenario_payoffs.values())

        selected_strategy = max(worst_case_payoff, key=worst_case_payoff.get)

        self.worst_case_payoff = worst_case_payoff
        self.selected_strategy = selected_strategy
        return worst_case_payoff, selected_strategy

    def run(self) -> dict:
        if not self.projects:
            raise ValueError("Cannot optimize an empty project list.")
        if self.total_budget <= 0:
            raise ValueError("Total budget must be a positive number.")

        self.generate_strategies()
        self.build_payoff_matrix()
        worst_case_payoff, selected_strategy = self.apply_minimax()

        recommended_allocation = self.strategies[selected_strategy]
        total_allocated = sum(recommended_allocation.values())
        leftover_budget = self.total_budget - total_allocated

        return {
            "strategies": self.strategies,
            "payoff_matrix": self.payoff_matrix,
            "worst_case_payoff": worst_case_payoff,
            "selected_strategy": selected_strategy,
            "recommended_allocation": recommended_allocation,
            "total_allocated": total_allocated,
            "leftover_budget": leftover_budget,
        }


class ToolTip:

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip_window, text=self.text, justify="left",
            background="#FFFFE0", relief="solid", borderwidth=1,
            font=("Segoe UI", 9), padx=6, pady=3
        )
        label.pack()

    def _hide(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ResourceAllocationApp:

    COLOR_BG = "#F4F6F8"
    COLOR_PRIMARY = "#1F3A5F"
    COLOR_ACCENT = "#2E86AB"
    COLOR_SUCCESS = "#2E7D32"
    COLOR_DANGER = "#C62828"
    COLOR_WHITE = "#FFFFFF"
    FONT_TITLE = ("Segoe UI", 18, "bold")
    FONT_HEADING = ("Segoe UI", 11, "bold")
    FONT_NORMAL = ("Segoe UI", 10)
    FONT_MONO = ("Consolas", 10)

    RISK_LEVELS = ("Low", "Medium", "High")

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Resource Allocation Optimizer - Minimax with Payoff")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 650)
        self.root.configure(bg=self.COLOR_BG)

        self.projects: List[Project] = []

        self._build_style()
        self._build_header()
        self._build_company_frame()
        self._build_project_entry_frame()
        self._build_table_frame()
        self._build_results_frame()
        self._build_action_buttons()
        self._build_status_bar()

        self._set_status("Ready. Enter company info and add projects to begin.")

    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Treeview", font=self.FONT_NORMAL, rowheight=26)
        style.configure("Treeview.Heading", font=self.FONT_HEADING)
        style.configure("TButton", font=self.FONT_NORMAL, padding=6)
        style.configure("TLabel", background=self.COLOR_BG, font=self.FONT_NORMAL)
        style.configure("TFrame", background=self.COLOR_BG)
        style.configure("TLabelframe", background=self.COLOR_BG, font=self.FONT_HEADING)
        style.configure("TLabelframe.Label", background=self.COLOR_BG, font=self.FONT_HEADING)

    def _build_header(self):
        header = tk.Frame(self.root, bg=self.COLOR_PRIMARY, height=64)
        header.pack(fill="x", side="top")

        title_label = tk.Label(
            header,
            text="Resource Allocation Optimizer  |  Minimax with Payoff",
            bg=self.COLOR_PRIMARY, fg=self.COLOR_WHITE, font=self.FONT_TITLE
        )
        title_label.pack(side="left", padx=20, pady=10)

        subtitle_label = tk.Label(
            header,
            text="by Hassan Muavia Jadoon",
            bg=self.COLOR_PRIMARY, fg="#D0D8E4", font=("Segoe UI", 10, "italic")
        )
        subtitle_label.pack(side="right", padx=20)

    def _build_company_frame(self):
        frame = ttk.LabelFrame(self.root, text="Company Information")
        frame.pack(fill="x", padx=14, pady=(10, 6))

        ttk.Label(frame, text="Company Name:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.entry_company_name = ttk.Entry(frame, width=28)
        self.entry_company_name.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(frame, text="Total Budget ($):").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.entry_total_budget = ttk.Entry(frame, width=18)
        self.entry_total_budget.grid(row=0, column=3, padx=8, pady=8, sticky="w")
        ToolTip(self.entry_total_budget, "Enter the total funds available, e.g. 500000")

        ttk.Label(frame, text="Number of Projects (planned):").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        self.entry_num_projects = ttk.Entry(frame, width=10)
        self.entry_num_projects.grid(row=0, column=5, padx=8, pady=8, sticky="w")
        ToolTip(self.entry_num_projects, "How many projects you intend to add in total")

    def _build_project_entry_frame(self):
        frame = ttk.LabelFrame(self.root, text="Add a Project")
        frame.pack(fill="x", padx=14, pady=6)

        ttk.Label(frame, text="Project Name:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.entry_project_name = ttk.Entry(frame, width=22)
        self.entry_project_name.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(frame, text="Requested Budget ($):").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.entry_requested_budget = ttk.Entry(frame, width=16)
        self.entry_requested_budget.grid(row=0, column=3, padx=8, pady=8, sticky="w")

        ttk.Label(frame, text="Expected Payoff ($):").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        self.entry_expected_payoff = ttk.Entry(frame, width=16)
        self.entry_expected_payoff.grid(row=0, column=5, padx=8, pady=8, sticky="w")
        ToolTip(self.entry_expected_payoff, "Expected monetary return/benefit if fully funded")

        ttk.Label(frame, text="Risk Level (optional):").grid(row=0, column=6, padx=8, pady=8, sticky="w")
        self.combo_risk_level = ttk.Combobox(
            frame, values=self.RISK_LEVELS, width=10, state="readonly"
        )
        self.combo_risk_level.set("Medium")
        self.combo_risk_level.grid(row=0, column=7, padx=8, pady=8, sticky="w")

        add_button = ttk.Button(frame, text="➕ Add Project", command=self._on_add_project)
        add_button.grid(row=0, column=8, padx=12, pady=8)
        ToolTip(add_button, "Add this project to the list below")

    def _build_table_frame(self):
        frame = ttk.LabelFrame(self.root, text="Entered Projects")
        frame.pack(fill="both", expand=False, padx=14, pady=6)

        columns: Tuple[str, ...] = ("name", "budget", "payoff", "risk")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        self.tree.heading("name", text="Project Name")
        self.tree.heading("budget", text="Requested Budget")
        self.tree.heading("payoff", text="Expected Payoff")
        self.tree.heading("risk", text="Risk Level")
        self.tree.column("name", width=250, anchor="w")
        self.tree.column("budget", width=170, anchor="center")
        self.tree.column("payoff", width=170, anchor="center")
        self.tree.column("risk", width=120, anchor="center")

        v_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        v_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

    def _build_results_frame(self):
        frame = ttk.LabelFrame(self.root, text="Results: Payoff Matrix, Minimax Selection & Recommended Allocation")
        frame.pack(fill="both", expand=True, padx=14, pady=6)

        self.results_text = scrolledtext.ScrolledText(
            frame, wrap="word", font=self.FONT_MONO, height=14,
            bg=self.COLOR_WHITE, fg="#111111"
        )
        self.results_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.results_text.insert("1.0", "Results will appear here after clicking 'Calculate Allocation'.")
        self.results_text.configure(state="disabled")

    def _build_action_buttons(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=14, pady=(0, 6))

        calc_button = tk.Button(
            frame, text="🧮 Calculate Allocation", command=self._on_calculate,
            bg=self.COLOR_ACCENT, fg=self.COLOR_WHITE, font=self.FONT_HEADING,
            relief="flat", padx=14, pady=8, cursor="hand2"
        )
        calc_button.pack(side="left", padx=6)

        reset_button = tk.Button(
            frame, text="🔄 Reset", command=self._on_reset,
            bg="#607D8B", fg=self.COLOR_WHITE, font=self.FONT_HEADING,
            relief="flat", padx=14, pady=8, cursor="hand2"
        )
        reset_button.pack(side="left", padx=6)

        exit_button = tk.Button(
            frame, text="🚪 Exit", command=self._on_exit,
            bg=self.COLOR_DANGER, fg=self.COLOR_WHITE, font=self.FONT_HEADING,
            relief="flat", padx=14, pady=8, cursor="hand2"
        )
        exit_button.pack(side="left", padx=6)

    def _build_status_bar(self):
        self.status_var = tk.StringVar()
        status_label = tk.Label(
            self.root, textvariable=self.status_var, bd=1, relief="sunken",
            anchor="w", bg="#E0E0E0", font=("Segoe UI", 9)
        )
        status_label.pack(fill="x", side="bottom")

    def _set_status(self, message: str):
        self.status_var.set(f"  {message}")

    @staticmethod
    def format_currency(value: float) -> str:
        return f"${value:,.2f}"

    @staticmethod
    def _validate_positive_float(raw_text: str, field_label: str) -> float:
        cleaned_text = raw_text.strip().replace(",", "").replace("$", "")
        if cleaned_text == "":
            raise ValueError(f"{field_label} cannot be empty.")
        try:
            value = float(cleaned_text)
        except ValueError:
            raise ValueError(f"{field_label} must be a valid number.")
        if value <= 0:
            raise ValueError(f"{field_label} must be greater than zero.")
        return value

    @staticmethod
    def _validate_non_empty_text(raw_text: str, field_label: str) -> str:
        cleaned_text = raw_text.strip()
        if cleaned_text == "":
            raise ValueError(f"{field_label} cannot be empty.")
        return cleaned_text

    def _on_add_project(self):
        try:
            planned_count_text = self.entry_num_projects.get().strip()
            if planned_count_text:
                try:
                    planned_count = int(planned_count_text)
                except ValueError:
                    raise ValueError("Number of Projects must be a whole number.")
                if planned_count <= 0:
                    raise ValueError("Number of Projects must be greater than zero.")
                if len(self.projects) >= planned_count:
                    raise ValueError(
                        f"You planned for only {planned_count} project(s). "
                        f"Increase that number to add more."
                    )

            project_name = self._validate_non_empty_text(
                self.entry_project_name.get(), "Project Name"
            )
            requested_budget = self._validate_positive_float(
                self.entry_requested_budget.get(), "Requested Budget"
            )
            expected_payoff = self._validate_positive_float(
                self.entry_expected_payoff.get(), "Expected Payoff"
            )
            risk_level = self.combo_risk_level.get().strip() or "Medium"
            if risk_level not in self.RISK_LEVELS:
                raise ValueError("Risk Level must be Low, Medium, or High.")

            existing_names = [p.name.lower() for p in self.projects]
            if project_name.lower() in existing_names:
                raise ValueError(f"A project named '{project_name}' already exists.")

            new_project = Project(
                name=project_name,
                requested_budget=requested_budget,
                expected_payoff=expected_payoff,
                risk_level=risk_level,
            )
            self.projects.append(new_project)
            self._refresh_project_table()
            self._clear_project_entry_fields()

            self._set_status(f"Project '{project_name}' added successfully.")

        except ValueError as validation_error:
            messagebox.showerror("Invalid Input", str(validation_error))
            self._set_status(f"Error: {validation_error}")
        except Exception as unexpected_error:
            messagebox.showerror("Unexpected Error", f"Something went wrong: {unexpected_error}")
            self._set_status("An unexpected error occurred while adding the project.")

    def _clear_project_entry_fields(self):
        self.entry_project_name.delete(0, tk.END)
        self.entry_requested_budget.delete(0, tk.END)
        self.entry_expected_payoff.delete(0, tk.END)
        self.combo_risk_level.set("Medium")

    def _refresh_project_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for project in self.projects:
            self.tree.insert(
                "", "end",
                values=(
                    project.name,
                    self.format_currency(project.requested_budget),
                    self.format_currency(project.expected_payoff),
                    project.risk_level,
                )
            )

    def _on_calculate(self):
        try:
            if not self.projects:
                raise ValueError("Please add at least one project before calculating.")

            total_budget = self._validate_positive_float(
                self.entry_total_budget.get(), "Total Budget"
            )

            optimizer = MinimaxOptimizer(self.projects, total_budget)
            result = optimizer.run()

            self._display_results(result, total_budget)
            self._set_status(
                f"Calculation complete. Recommended strategy: '{result['selected_strategy']}'."
            )
            messagebox.showinfo(
                "Calculation Complete",
                f"Minimax strategy selected:\n\n{result['selected_strategy']}\n\n"
                f"Guaranteed worst-case payoff: "
                f"{self.format_currency(result['worst_case_payoff'][result['selected_strategy']])}"
            )

        except ValueError as validation_error:
            messagebox.showerror("Invalid Input", str(validation_error))
            self._set_status(f"Error: {validation_error}")
        except Exception as unexpected_error:
            messagebox.showerror("Unexpected Error", f"Calculation failed: {unexpected_error}")
            self._set_status("An unexpected error occurred during calculation.")

    def _display_results(self, result: dict, total_budget: float):
        lines: List[str] = []
        company_name = self.entry_company_name.get().strip() or "N/A"

        lines.append("=" * 88)
        lines.append(f" COMPANY: {company_name}    |    TOTAL BUDGET: {self.format_currency(total_budget)}")
        lines.append("=" * 88)

        lines.append("\nPAYOFF MATRIX  (rows = strategies, columns = scenarios)\n")
        scenarios = MinimaxOptimizer.SCENARIOS
        header = f"{'Strategy':32}" + "".join(f"{s:>18}" for s in scenarios)
        lines.append(header)
        lines.append("-" * len(header))
        for strategy_name, scenario_payoffs in result["payoff_matrix"].items():
            row = f"{strategy_name:32}"
            for scenario in scenarios:
                row += f"{self.format_currency(scenario_payoffs[scenario]):>18}"
            lines.append(row)

        lines.append("\nWORST-CASE PAYOFF PER STRATEGY (Minimax criterion)\n")
        for strategy_name, worst_value in result["worst_case_payoff"].items():
            marker = "  <-- SELECTED (best worst-case)" if strategy_name == result["selected_strategy"] else ""
            lines.append(f"  {strategy_name:32}{self.format_currency(worst_value):>18}{marker}")

        lines.append(f"\nSELECTED MINIMAX STRATEGY: {result['selected_strategy']}")

        lines.append("\nRECOMMENDED BUDGET ALLOCATION\n")
        lookup = {p.name: p for p in self.projects}
        alloc_header = f"{'Project':30}{'Allocated':>16}{'Requested':>16}{'% Funded':>12}"
        lines.append(alloc_header)
        lines.append("-" * len(alloc_header))
        for project_name, allocated_amount in result["recommended_allocation"].items():
            requested = lookup[project_name].requested_budget
            percent_funded = (allocated_amount / requested * 100) if requested > 0 else 0
            lines.append(
                f"{project_name:30}"
                f"{self.format_currency(allocated_amount):>16}"
                f"{self.format_currency(requested):>16}"
                f"{percent_funded:>11.1f}%"
            )

        lines.append("\nFINAL OPTIMIZED DECISION\n")
        lines.append(f"  Strategy chosen        : {result['selected_strategy']}")
        lines.append(f"  Guaranteed worst payoff : {self.format_currency(result['worst_case_payoff'][result['selected_strategy']])}")
        lines.append(f"  Total budget allocated  : {self.format_currency(result['total_allocated'])}")
        lines.append(f"  Budget left unallocated : {self.format_currency(result['leftover_budget'])}")
        lines.append("=" * 88)

        final_text = "\n".join(lines)
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", final_text)
        self.results_text.configure(state="disabled")

    def _on_reset(self):
        confirmed = messagebox.askyesno(
            "Confirm Reset", "This will clear all entered data. Continue?"
        )
        if not confirmed:
            return

        self.projects.clear()
        self._refresh_project_table()

        self.entry_company_name.delete(0, tk.END)
        self.entry_total_budget.delete(0, tk.END)
        self.entry_num_projects.delete(0, tk.END)
        self._clear_project_entry_fields()

        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", "Results will appear here after clicking 'Calculate Allocation'.")
        self.results_text.configure(state="disabled")

        self._set_status("Application reset. Ready for new input.")

    def _on_exit(self):
        confirmed = messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?")
        if confirmed:
            self.root.destroy()


def main():
    try:
        root = tk.Tk()
        app = ResourceAllocationApp(root)
        root.mainloop()
    except Exception as fatal_error:
        print(f"Fatal error while starting the application: {fatal_error}")


if __name__ == "__main__":
    main()
