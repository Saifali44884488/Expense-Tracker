# expense_tracker_simple_fixed.py
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from datetime import datetime
from pathlib import Path
import csv
import json

# Files
BASE = Path(__file__).parent
CSV_FILE = BASE / "expenses.csv"
BUDGET_FILE = BASE / "budgets.json"
DATE_FMT = "%Y-%m-%d"

# Ensure files exist
if not CSV_FILE.exists():
    with CSV_FILE.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "category", "amount", "description"])
        writer.writeheader()
if not BUDGET_FILE.exists():
    BUDGET_FILE.write_text("{}")

# Helpers
def read_expenses():
    rows = []
    with CSV_FILE.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                r["amount"] = float(r["amount"])
                r["date"] = datetime.strptime(r["date"], DATE_FMT)
            except Exception:
                continue
            rows.append(r)
    return rows

def append_expense(date_str, category, amount, description):
    with CSV_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "category", "amount", "description"])
        writer.writerow({
            "date": date_str,
            "category": category,
            "amount": f"{amount:.2f}",
            "description": description
        })

def load_budgets():
    try:
        return json.loads(BUDGET_FILE.read_text())
    except Exception:
        return {}

def save_budgets(b):
    BUDGET_FILE.write_text(json.dumps(b, indent=2))

def total_for_category_month(category, year, month):
    total = 0.0
    for r in read_expenses():
        if r["category"].lower() == category.lower() and r["date"].year == year and r["date"].month == month:
            total += r["amount"]
    return total

# GUI app (simple, quiz-like style) - layout improved
class ExpenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        # slightly larger to prevent clipping and provide breathing room
        self.root.geometry("820x600")
        self.root.resizable(False, False)
        self.bg = "#0f1724"
        self.fg = "#ffffff"
        self.accent = "#2e86de"

        root.configure(bg=self.bg)

        # Title
        title = tk.Label(root, text="💸 Expense Tracker", font=("Arial", 18, "bold"),
                         bg=self.bg, fg="#f1c40f")
        title.pack(pady=(12, 6))

        # Input frame: two rows (labels row + inputs row) with 5 columns (date, category, amount, description, button)
        frm = tk.Frame(root, bg=self.bg)
        frm.pack(pady=6, fill="x", padx=12)

        # Configure 5 columns equally
        for c in range(5):
            frm.grid_columnconfigure(c, weight=1, uniform='a')

        # Labels (row 0)
        tk.Label(frm, text="Date (YYYY-MM-DD)", bg=self.bg, fg=self.fg).grid(row=0, column=0, sticky="w", padx=6)
        tk.Label(frm, text="Category", bg=self.bg, fg=self.fg).grid(row=0, column=1, sticky="w", padx=6)
        tk.Label(frm, text="Amount", bg=self.bg, fg=self.fg).grid(row=0, column=2, sticky="w", padx=6)
        tk.Label(frm, text="Description", bg=self.bg, fg=self.fg).grid(row=0, column=3, sticky="w", padx=6)

        # Inputs (row 1)
        self.date_var = tk.StringVar(value=datetime.today().strftime(DATE_FMT))
        tk.Entry(frm, textvariable=self.date_var, width=14).grid(row=1, column=0, padx=6, pady=4, sticky="we")

        self.cat_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.cat_var, width=18).grid(row=1, column=1, padx=6, pady=4, sticky="we")

        self.amt_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.amt_var, width=12).grid(row=1, column=2, padx=6, pady=4, sticky="we")

        self.desc_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.desc_var, width=28).grid(row=1, column=3, padx=6, pady=4, sticky="we")

        # Add button placed in its own column but vertically centered (span two rows visually)
        btn_add = tk.Button(frm, text="Add Expense", bg=self.accent, fg="white", width=14, command=self.add_expense)
        btn_add.grid(row=1, column=4, padx=8, pady=4, sticky="e")

        # Filter frame (same approach with equal columns)
        f2 = tk.Frame(root, bg=self.bg)
        f2.pack(pady=8, fill="x", padx=12)
        for c in range(6):
            f2.grid_columnconfigure(c, weight=1, uniform='b')

        tk.Label(f2, text="Filter start (YYYY-MM-DD)", bg=self.bg, fg=self.fg).grid(row=0, column=0, sticky="w", padx=6)
        tk.Label(f2, text="Filter end (YYYY-MM-DD)", bg=self.bg, fg=self.fg).grid(row=0, column=1, sticky="w", padx=6)
        tk.Label(f2, text="Category contains", bg=self.bg, fg=self.fg).grid(row=0, column=2, sticky="w", padx=6)

        self.start_var = tk.StringVar()
        tk.Entry(f2, textvariable=self.start_var, width=14).grid(row=1, column=0, padx=6, sticky="we")
        self.end_var = tk.StringVar()
        tk.Entry(f2, textvariable=self.end_var, width=14).grid(row=1, column=1, padx=6, sticky="we")
        self.filter_cat = tk.StringVar()
        tk.Entry(f2, textvariable=self.filter_cat, width=18).grid(row=1, column=2, padx=6, sticky="we")

        tk.Button(f2, text="Apply Filter", command=self.refresh_list).grid(row=1, column=3, padx=6, sticky="w")
        tk.Button(f2, text="Clear Filter", command=self.clear_filter).grid(row=1, column=4, padx=6, sticky="w")
        tk.Button(f2, text="Set Budgets", command=self.set_budgets).grid(row=1, column=5, padx=6, sticky="e")

        # Listbox for expenses (scrollable)
        list_frame = tk.Frame(root, bg=self.bg)
        list_frame.pack(padx=12, pady=(4,10), fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, font=("Consolas", 11), width=100, height=16)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Bottom buttons - well spaced and centered
        bottom = tk.Frame(root, bg=self.bg)
        bottom.pack(pady=(4,12))
        tk.Button(bottom, text="Export CSV...", command=self.export_csv).pack(side="left", padx=10)
        tk.Button(bottom, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=10)
        tk.Button(bottom, text="Quit", command=root.quit).pack(side="left", padx=10)

        self.refresh_list()

    def add_expense(self):
        date_s = self.date_var.get().strip()
        cat = self.cat_var.get().strip() or "Other"
        amt_s = self.amt_var.get().strip()
        desc = self.desc_var.get().strip()
        # validate
        try:
            dt = datetime.strptime(date_s, DATE_FMT)
        except Exception:
            messagebox.showerror("Invalid date", f"Date must be {DATE_FMT}")
            return
        try:
            amt = float(amt_s)
        except Exception:
            messagebox.showerror("Invalid amount", "Amount must be a number (e.g. 123.45)")
            return
        append_expense(date_s, cat, amt, desc)

        # load budgets and check for violation on the same month/category
        budgets = load_budgets()
        if cat in budgets:
            now = dt
            used = total_for_category_month(cat, now.year, now.month)
            if used > float(budgets[cat]):
                messagebox.showwarning("Budget exceeded",
                                       f"Category '{cat}' exceeded budget for {now.year}-{now.month:02d}:\n"
                                       f"Used {used:.2f} > Budget {float(budgets[cat]):.2f}")

        # clear small fields and refresh
        self.amt_var.set("")
        self.desc_var.set("")
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        rows = read_expenses()
        # filters
        s = self.start_var.get().strip()
        e = self.end_var.get().strip()
        fc = self.filter_cat.get().strip().lower()
        try:
            if s:
                s_dt = datetime.strptime(s, DATE_FMT)
            else:
                s_dt = None
            if e:
                e_dt = datetime.strptime(e, DATE_FMT)
            else:
                e_dt = None
        except Exception:
            messagebox.showerror("Invalid date", f"Filters must be {DATE_FMT}")
            return
        for r in sorted(rows, key=lambda x: x["date"], reverse=True):
            if s_dt and r["date"] < s_dt:
                continue
            if e_dt and r["date"] > e_dt:
                continue
            if fc and fc not in r["category"].lower():
                continue
            # Format line: date | category | amount | description
            line = f"{r['date'].strftime(DATE_FMT)}  |  {r['category'][:18]:18s}  |  {r['amount']:8.2f}  |  {r['description']}"
            self.listbox.insert(tk.END, line)

    def clear_filter(self):
        self.start_var.set("")
        self.end_var.set("")
        self.filter_cat.set("")
        self.refresh_list()

    def set_budgets(self):
        budgets = load_budgets()
        prompt = "Enter budgets as comma separated pairs, e.g.\nfood:2000, rent:8000\n\nExisting:\n" + \
                 ", ".join(f"{k}:{v}" for k, v in budgets.items())
        resp = simpledialog.askstring("Set Budgets", prompt, parent=self.root)
        if resp is None:
            return
        new = {}
        for part in resp.split(","):
            part = part.strip()
            if not part:
                continue
            if ":" not in part:
                messagebox.showerror("Invalid format", "Use category:amount pairs separated by commas.")
                return
            k, v = part.split(":", 1)
            k = k.strip()
            try:
                new[k] = float(v.strip())
            except Exception:
                messagebox.showerror("Invalid amount", f"Budget for {k} must be a number.")
                return
        save_budgets(new)
        messagebox.showinfo("Saved", "Budgets saved.")
        self.refresh_list()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path:
            return
        with open(path, "w", newline="") as out:
            with CSV_FILE.open("r", newline="") as src:
                out.write(src.read())
        messagebox.showinfo("Exported", f"Exported to {path}")

    def delete_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("No selection", "Select a row to delete.")
            return
        idx = sel[0]
        # find the corresponding row in the filtered list by re-building the same list
        filtered = []
        rows = read_expenses()
        s = self.start_var.get().strip()
        e = self.end_var.get().strip()
        fc = self.filter_cat.get().strip().lower()
        s_dt = None
        e_dt = None
        try:
            if s:
                s_dt = datetime.strptime(s, DATE_FMT)
            if e:
                e_dt = datetime.strptime(e, DATE_FMT)
        except Exception:
            messagebox.showerror("Invalid date", f"Filters must be {DATE_FMT}")
            return
        for r in sorted(rows, key=lambda x: x["date"], reverse=True):
            if s_dt and r["date"] < s_dt:
                continue
            if e_dt and r["date"] > e_dt:
                continue
            if fc and fc not in r["category"].lower():
                continue
            filtered.append(r)
        if idx >= len(filtered):
            messagebox.showerror("Error", "Selection out of range.")
            return
        # confirm delete
        to_del = filtered[idx]
        if not messagebox.askyesno("Confirm", f"Delete expense: {to_del['date'].strftime(DATE_FMT)} | {to_del['category']} | {to_del['amount']:.2f}?"):
            return
        # remove by rewriting CSV excluding that exact row (date, category, amount, desc match)
        kept = []
        for r in read_expenses():
            if not (r["date"] == to_del["date"] and r["category"] == to_del["category"] and abs(r["amount"] - to_del["amount"]) < 1e-6 and r["description"] == to_del["description"]):
                kept.append(r)
        with CSV_FILE.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "category", "amount", "description"])
            writer.writeheader()
            for r in kept:
                writer.writerow({
                    "date": r["date"].strftime(DATE_FMT),
                    "category": r["category"],
                    "amount": f"{r['amount']:.2f}",
                    "description": r["description"]
                })
        self.refresh_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseApp(root)
    root.mainloop()
