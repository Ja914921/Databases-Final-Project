import tkinter as tk
from tkinter import ttk, messagebox 

from gameApp import run_query

class GameAppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Game database App")
        self.geometry("1050x650")

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Game Search", font=("Segoe UI", 14, "bold")).pack(anchor="w")

        controls = ttk.Frame(top)
        controls.pack(fill="x", pady=(10, 0))

        #Controls for search
        ttk.Label(controls, text="Name contains:").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(controls, width=30)
        self.name_entry.grid(row=0, column=1, padx=8)

        ttk.Button(controls, text="Search (Sales + ESRB)", command=self.search_by_name)\
            .grid(row=0, column=2, padx=8)
        
        ttk.Label(controls, text="Top N: ").grid(row=0, column=3, sticky="w")
        self.topn_entry = ttk.Entry(controls, width=10)
        self.topn_entry.insert(0, "10")
        self.topn_entry.grid(row=0, column=4, padx=8) 

        ttk.Button(controls, text="Top by Global Sales", command=self.list_top_sales)\
            .grid(row=0, column=5, padx=8)
        
        ttk.Label(controls, text="Rating:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.rating_entry = ttk.Entry(controls, width=10)
        self.rating_entry.grid(row=1, column=1, sticky="w", padx=8, pady=(10, 0))

        ttk.Label(controls, text="Min Sales (M):").grid(row=1, column=2, sticky="e", pady=(10, 0))
        self.minsales_entry = ttk.Entry(controls, width=10)
        self.minsales_entry.insert(0, "1.0")
        self.minsales_entry.grid(row=1, column=3, sticky="w", padx=8, pady=(10, 0))

        ttk.Button(controls, text="Filter", command=self.filter_by_rating_sales)\
            .grid(row=1, column=4, padx=8, pady=(10, 0), sticky="w")

        ttk.Button(controls, text="Avg Sales by Rating", command=self.avg_sales_by_rating)\
            .grid(row=1, column=5, padx=8, pady=(10, 0), sticky="w")
        
        table_frame = ttk.Frame(self, padding=10)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.status = ttk.Label(self, text="Ready", anchor="w", padding=10)
        self.status.pack(fill="x")

    def set_results(self, rows):
        self.tree.delete(*self.tree.get_children())

        if not rows:
            self.tree["columns"] = ("message",)
            self.tree.heading("message", text="Message")
            self.tree.insert("", "end", values=("No results.",))
            self.status.config(text="No results.")
            return

        cols = list(rows[0].keys())
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150, anchor="w")

        for r in rows:
            self.tree.insert("", "end", values=[r.get(c, "") for c in cols])

        self.status.config(text=f"Returned {len(rows)} row(s).")

    def list_top_sales(self):
        try:
            n = int(self.topn_entry.get().strip() or "10")
        except ValueError:
            messagebox.showerror("Invalid Input", "Top N must be an integer.")
            return

        query = """
            SELECT name, platform, year, genre, publisher, global_sales
            FROM bg_sales_game
            ORDER BY global_sales DESC
            LIMIT %s;
        """
        self.set_results(run_query(query, (n,)))

    def search_by_name(self):
        term = self.name_entry.get().strip()
        if not term:
            messagebox.showwarning("Missing Input", "Enter part of the game name.")
            return

        query = """
            SELECT s.name, s.platform, s.year, s.genre, s.publisher, s.global_sales, e.esrb_rating
            FROM bg_sales_game AS s
            LEFT JOIN bg_esrb_game AS e
                ON e.title = s.name
            WHERE s.name LIKE %s
            ORDER BY s.global_sales DESC
            LIMIT 25;
        """
        self.set_results(run_query(query, (f"%{term}%",)))

    def avg_sales_by_rating(self):
        query = """
            SELECT e.esrb_rating,
                   COUNT(*) AS num_games,
                   ROUND(AVG(s.global_sales), 2) AS avg_global_sales
            FROM bg_esrb_game AS e
            JOIN bg_sales_game AS s
                ON e.title = s.name
            GROUP BY e.esrb_rating
            ORDER BY avg_global_sales DESC;
        """
        self.set_results(run_query(query))

    def filter_by_rating_sales(self):
        rating = self.rating_entry.get().strip().upper()
        if not rating:
            messagebox.showwarning("Missing Input", "Enter an ESRB rating (E, T, M, etc.).")
            return

        try:
            min_sales = float(self.minsales_entry.get().strip() or "0")
        except ValueError:
            messagebox.showerror("Invalid Input", "Min Sales must be a number.")
            return

        query = """
            SELECT s.name, s.platform, s.year, s.genre, s.global_sales, e.esrb_rating
            FROM bg_esrb_game AS e
            JOIN bg_sales_game AS s
                ON e.title = s.name
            WHERE e.esrb_rating = %s
              AND s.global_sales >= %s
            ORDER BY s.global_sales DESC;
        """
        self.set_results(run_query(query, (rating, min_sales)))


if __name__ == "__main__":
    GameAppGUI().mainloop()