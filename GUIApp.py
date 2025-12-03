import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import inspect

from gameApp import run_query


SCHEMA = {

    "games": {
        "table": "bg_sales_game",
        "id": "sales_game_id",
        "title": "title",
        "platform": "platform",
        "genre": "genre",
        "publisher": "publisher",
        "developer": "developer",
        "release_year": "release_year",
        "source": "source",
    },
    "user": {
        "table": "app_user",
        "id": "user_id",
        "username": "username",
        "email": "email",
        "pw": "password_hash",
        "active": "is_active",
        "created": "created_at",
        "updated": "updated_at",
    },
}


class DB:
    def __init__(self, fn):
        self.fn = fn
        self.sig = inspect.signature(fn)
        self.params = list(self.sig.parameters.keys())
        self.has_fetch = "fetch" in self.sig.parameters
        self.has_commit = "commit" in self.sig.parameters

    def _call_once(self, sql: str, params=(), fetch=True):
        if len(self.params) == 1:
            return self.fn(sql)

        if self.has_fetch or self.has_commit:
            kwargs = {}
            if self.has_fetch:
                kwargs["fetch"] = fetch
            if self.has_commit:
                kwargs["commit"] = (not fetch)
            return self.fn(sql, params, **kwargs)

        if len(self.params) >= 3:
            try:
                return self.fn(sql, params, fetch)
            except TypeError:
                pass

        return self.fn(sql, params)

    def call(self, sql: str, params=(), fetch=True):
        sql = (sql or "").strip()
        if params is None:
            params = ()

        try:
            return self._call_once(sql, params=params, fetch=fetch)
        except Exception as e1:
            if "%s" in sql:
                try:
                    return self._call_once(sql.replace("%s", "?"), params=params, fetch=fetch)
                except Exception:
                    raise e1
            raise

    def select(self, sql: str, params=()):
        return self.call(sql, params=params, fetch=True) or []

    def exec(self, sql: str, params=()):
        return self.call(sql, params=params, fetch=False)


DBX = DB(run_query)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_result(result):
    if result is None:
        return ["info"], [("No result returned.",)]

    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], (list, tuple)):
        cols = list(result[0])
        rows = [tuple(r) for r in list(result[1])]
        return cols, rows

    if isinstance(result, list) and not result:
        return ["info"], [("No rows returned.",)]

    if isinstance(result, list) and result and isinstance(result[0], dict):
        cols = list(result[0].keys())
        rows = [tuple(r.get(c) for c in cols) for r in result]
        return cols, rows

    if isinstance(result, list) and result and isinstance(result[0], (list, tuple)):
        rows = [tuple(r) for r in result]
        cols = [f"col{i+1}" for i in range(len(rows[0]))]
        return cols, rows

    return ["info"], [(str(result),)]


def render(tree: ttk.Treeview, result):
    tree.delete(*tree.get_children())
    cols, rows = _normalize_result(result)

    tree["columns"] = cols
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=170, anchor="w")

    for r in rows:
        tree.insert("", "end", values=r)


def make_tree(parent):
    wrap = ttk.Frame(parent)
    wrap.pack(fill="both", expand=True)

    tree = ttk.Treeview(wrap, show="headings")
    vsb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    wrap.rowconfigure(0, weight=1)
    wrap.columnconfigure(0, weight=1)
    return tree


def count_rows(result) -> int:
    if result is None:
        return 0
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], (list, tuple)):
        return len(result[1])
    if isinstance(result, list):
        return len(result)
    return 1


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GameSearch DB App (Checkpoint 2)")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        self.selected_game_id = None
        self.selected_user_id = None

        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text="GameSearch DB App", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(header, text="DB Check", command=self.db_check).pack(side="right")

        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", padx=12)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_search = ttk.Frame(nb, padding=10)
        self.tab_users = ttk.Frame(nb, padding=10)
        self.tab_console = ttk.Frame(nb, padding=10)

        nb.add(self.tab_search, text="Search (bg_sales_game)")
        nb.add(self.tab_users, text="Users (CRUD app_user)")
        nb.add(self.tab_console, text="SQL Console (SELECT/WITH)")

        self._build_search()
        self._build_users()
        self._build_console()

        self.load_users()

    def _set(self, msg: str):
        self.status.set(msg)


    def _build_search(self):
        g = SCHEMA["games"]

        box = ttk.LabelFrame(self.tab_search, text="Filters", padding=10)
        box.pack(fill="x")

        ttk.Label(box, text="Title contains:").grid(row=0, column=0, sticky="w")
        self.f_title = ttk.Entry(box, width=34)
        self.f_title.grid(row=0, column=1, padx=8, pady=2, sticky="w")

        ttk.Label(box, text="Platform:").grid(row=0, column=2, sticky="w")
        self.f_platform = ttk.Entry(box, width=22)
        self.f_platform.grid(row=0, column=3, padx=8, pady=2, sticky="w")

        ttk.Label(box, text="Genre:").grid(row=0, column=4, sticky="w")
        self.f_genre = ttk.Entry(box, width=22)
        self.f_genre.grid(row=0, column=5, padx=8, pady=2, sticky="w")

        ttk.Label(box, text="Release year:").grid(row=0, column=6, sticky="w")
        self.f_year = ttk.Entry(box, width=10)
        self.f_year.grid(row=0, column=7, padx=8, pady=2, sticky="w")

        ttk.Button(box, text="Search", command=self.search).grid(row=0, column=8, padx=8)
        ttk.Button(box, text="Clear", command=self.clear_search).grid(row=0, column=9, padx=(0, 8))

        out = ttk.LabelFrame(self.tab_search, text="Results (click a row to select game)", padding=10)
        out.pack(fill="both", expand=True, pady=(10, 0))

        self.search_tree = make_tree(out)
        self.search_tree.bind("<<TreeviewSelect>>", self._pick_game)

        self.selected_game_lbl = tk.StringVar(value="Selected game_id: (none)")
        ttk.Label(self.tab_search, textvariable=self.selected_game_lbl).pack(anchor="w", pady=(8, 0))

        self._set(f"Tip: Searching from {g['table']}")

    def clear_search(self):
        self.f_title.delete(0, tk.END)
        self.f_platform.delete(0, tk.END)
        self.f_genre.delete(0, tk.END)
        self.f_year.delete(0, tk.END)
        self.selected_game_id = None
        self.selected_game_lbl.set("Selected game_id: (none)")
        render(self.search_tree, [])
        self._set("Cleared search.")

    def search(self):
        g = SCHEMA["games"]
        where = [f"{g['title']} IS NOT NULL"]
        params = []

        title = self.f_title.get().strip()
        if title:
            where.append(f"{g['title']} LIKE %s")
            params.append(f"%{title}%")

        plat = self.f_platform.get().strip()
        if plat:
            where.append(f"{g['platform']} = %s")
            params.append(plat)

        genre = self.f_genre.get().strip()
        if genre:
            where.append(f"{g['genre']} = %s")
            params.append(genre)

        year = self.f_year.get().strip()
        if year:
            try:
                year_int = int(year)
                where.append(f"{g['release_year']} = %s")
                params.append(year_int)
            except ValueError:
                messagebox.showerror("Bad year", "Release year must be a whole number (e.g., 2011).")
                return

        sql = f"""
        SELECT
            {g['id']} AS game_id,
            {g['title']} AS title,
            {g['platform']} AS platform,
            {g['genre']} AS genre,
            {g['publisher']} AS publisher,
            {g['developer']} AS developer,
            {g['release_year']} AS release_year,
            {g['source']} AS source
        FROM {g['table']}
        WHERE {" AND ".join(where)}
        ORDER BY {g['title']} ASC
        LIMIT 200
        """
        try:
            self._set("Searching...")
            rows = DBX.select(sql, tuple(params))
            render(self.search_tree, rows)
            self._set(f"Search complete: {count_rows(rows)} rows.")
        except Exception as e:
            self._set("Search failed.")
            messagebox.showerror("Search failed", f"{e}\n\nSQL:\n{sql}\n\nParams:\n{params}")

    def _pick_game(self, _=None):
        sel = self.search_tree.selection()
        if not sel:
            self.selected_game_id = None
            self.selected_game_lbl.set("Selected game_id: (none)")
            return
        vals = self.search_tree.item(sel[0]).get("values") or []
        self.selected_game_id = vals[0] if vals else None
        self.selected_game_lbl.set(f"Selected game_id: {self.selected_game_id}")
        self._set(f"Selected game_id={self.selected_game_id}")

    def _build_users(self):
        u = SCHEMA["user"]

        form = ttk.LabelFrame(self.tab_users, text="User Form (Create / Update / Delete)", padding=10)
        form.pack(fill="x")

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="w")
        self.nu = ttk.Entry(form, width=24)
        self.nu.grid(row=0, column=1, padx=8, pady=2, sticky="w")

        ttk.Label(form, text="Email:").grid(row=0, column=2, sticky="w")
        self.ne = ttk.Entry(form, width=30)
        self.ne.grid(row=0, column=3, padx=8, pady=2, sticky="w")

        ttk.Label(form, text="Password (blank keeps current on update):").grid(row=1, column=0, sticky="w")
        self.np = ttk.Entry(form, width=24, show="*")
        self.np.grid(row=1, column=1, padx=8, pady=2, sticky="w")

        self.active_var = tk.IntVar(value=1)
        ttk.Checkbutton(form, text="Active", variable=self.active_var).grid(row=1, column=3, sticky="w")

        btns = ttk.Frame(form)
        btns.grid(row=2, column=0, columnspan=4, sticky="e", pady=(8, 0))
        ttk.Button(btns, text="Create", command=self.create_user).pack(side="left", padx=6)
        ttk.Button(btns, text="Update (selected)", command=self.update_user).pack(side="left", padx=6)
        ttk.Button(btns, text="Delete (selected)", command=self.delete_user).pack(side="left", padx=6)
        ttk.Button(btns, text="Refresh", command=self.load_users).pack(side="left", padx=6)
        ttk.Button(btns, text="Clear", command=self.clear_user_form).pack(side="left", padx=6)

        meta = ttk.Frame(self.tab_users)
        meta.pack(fill="x", pady=(10, 6))
        self.selected_user_lbl = tk.StringVar(value="Selected user_id: (none)")
        ttk.Label(meta, textvariable=self.selected_user_lbl).pack(side="right")

        out = ttk.LabelFrame(self.tab_users, text="Users (click a row to load into form)", padding=10)
        out.pack(fill="both", expand=True)

        self.user_tree = make_tree(out)
        self.user_tree.bind("<<TreeviewSelect>>", self._pick_user)

        hint = (
            "Demo tip: Create -> Update -> Delete (or deactivate) a user, then verify in SQL Console:\n"
            "SELECT user_id, username, email, is_active FROM app_user ORDER BY user_id DESC LIMIT 10;"
        )
        ttk.Label(self.tab_users, text=hint).pack(anchor="w", pady=(8, 0))

    def clear_user_form(self):
        self.selected_user_id = None
        self.selected_user_lbl.set("Selected user_id: (none)")
        self.nu.delete(0, tk.END)
        self.ne.delete(0, tk.END)
        self.np.delete(0, tk.END)
        self.active_var.set(1)
        self._set("Cleared user form.")

    def load_users(self):
        u = SCHEMA["user"]
        sql = f"""
        SELECT
            {u['id']} AS user_id,
            {u['username']} AS username,
            {u['email']} AS email,
            {u['active']} AS is_active,
            {u['created']} AS created_at,
            {u['updated']} AS updated_at
        FROM {u['table']}
        ORDER BY {u['id']} DESC
        LIMIT 300
        """
        try:
            rows = DBX.select(sql)
            render(self.user_tree, rows)
            self._set("Users loaded.")
        except Exception as e:
            messagebox.showerror("Load users failed", str(e))

    def _pick_user(self, _=None):
        sel = self.user_tree.selection()
        if not sel:
            return
        vals = self.user_tree.item(sel[0]).get("values") or []
        if len(vals) < 4:
            return

        self.selected_user_id = vals[0]
        self.selected_user_lbl.set(f"Selected user_id: {self.selected_user_id}")

        self.nu.delete(0, tk.END)
        self.nu.insert(0, str(vals[1] or ""))

        self.ne.delete(0, tk.END)
        self.ne.insert(0, str(vals[2] or ""))

        self.np.delete(0, tk.END)
        self.active_var.set(int(vals[3] or 0))
        self._set("Loaded user into form.")

    def create_user(self):
        u = SCHEMA["user"]
        username = self.nu.get().strip()
        email = self.ne.get().strip().lower()
        pw = self.np.get()

        if not username or not email or not pw:
            messagebox.showerror("Missing", "Username, email, and password are required.")
            return

        sql = f"INSERT INTO {u['table']} ({u['username']}, {u['email']}, {u['pw']}) VALUES (%s, %s, %s)"
        try:
            DBX.exec(sql, (username, email, sha256(pw)))
            self._set("User created.")
            self.np.delete(0, tk.END)
            self.load_users()
        except Exception as e:
            messagebox.showerror("Create failed", str(e))

    def update_user(self):
        u = SCHEMA["user"]
        if not self.selected_user_id:
            messagebox.showerror("No selection", "Select a user row first.")
            return

        username = self.nu.get().strip()
        email = self.ne.get().strip().lower()
        pw = self.np.get().strip()
        is_active = int(self.active_var.get())

        if not username or not email:
            messagebox.showerror("Missing", "Username and email are required.")
            return

        try:
            if pw:
                sql = f"""
                UPDATE {u['table']}
                SET {u['username']}=%s, {u['email']}=%s, {u['pw']}=%s, {u['active']}=%s
                WHERE {u['id']}=%s
                """
                params = (username, email, sha256(pw), is_active, self.selected_user_id)
            else:
                sql = f"""
                UPDATE {u['table']}
                SET {u['username']}=%s, {u['email']}=%s, {u['active']}=%s
                WHERE {u['id']}=%s
                """
                params = (username, email, is_active, self.selected_user_id)

            DBX.exec(sql, params)
            self._set("User updated.")
            self.np.delete(0, tk.END)
            self.load_users()
        except Exception as e:
            messagebox.showerror("Update failed", str(e))

    def delete_user(self):
        u = SCHEMA["user"]
        if not self.selected_user_id:
            messagebox.showerror("No selection", "Select a user row first.")
            return

        if not messagebox.askyesno("Confirm", f"Delete user_id={self.selected_user_id}?"):
            return

        try:
            DBX.exec(f"DELETE FROM {u['table']} WHERE {u['id']}=%s", (self.selected_user_id,))
            self._set("User deleted.")
            self.clear_user_form()
            self.load_users()
            return
        except Exception:
            try:
                DBX.exec(f"UPDATE {u['table']} SET {u['active']}=0 WHERE {u['id']}=%s", (self.selected_user_id,))
                self.active_var.set(0)
                self._set("User deactivated (FK prevented hard delete).")
                self.load_users()
            except Exception as e2:
                messagebox.showerror("Delete failed", str(e2))

    def _build_console(self):
        ttk.Label(self.tab_console, text="Console (SELECT/WITH only)", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        self.sql_text = tk.Text(self.tab_console, height=8, wrap="none")
        self.sql_text.pack(fill="x", pady=(8, 8))
        self.sql_text.insert(
            "1.0",
            "SELECT sales_game_id, title, platform, genre, publisher, release_year\n"
            "FROM bg_sales_game\n"
            "WHERE title IS NOT NULL\n"
            "ORDER BY title\n"
            "LIMIT 10;\n"
        )

        btns = ttk.Frame(self.tab_console)
        btns.pack(fill="x")

        ttk.Button(btns, text="Run SELECT", command=self.run_select).pack(side="right")
        ttk.Button(btns, text="Load Users Verify", command=self.load_verify_users_query).pack(side="left")

        out = ttk.LabelFrame(self.tab_console, text="Results", padding=10)
        out.pack(fill="both", expand=True, pady=(10, 0))
        self.console_tree = make_tree(out)

    def load_verify_users_query(self):
        self.sql_text.delete("1.0", tk.END)
        self.sql_text.insert(
            "1.0",
            "SELECT user_id, username, email, is_active, created_at, updated_at\n"
            "FROM app_user\n"
            "ORDER BY user_id DESC\n"
            "LIMIT 25;\n"
        )

    def run_select(self):
        sql = (self.sql_text.get("1.0", "end") or "").strip()
        if not sql:
            messagebox.showerror("Missing", "Enter a SELECT query.")
            return

        first = sql.lstrip().split(None, 1)[0].lower() if sql.strip() else ""
        if first not in ("select", "with"):
            messagebox.showerror("Blocked", "Console only allows SELECT/WITH queries.")
            return

        try:
            rows = DBX.select(sql)
            render(self.console_tree, rows)
            self._set(f"Console ran: {count_rows(rows)} rows.")
        except Exception as e:
            messagebox.showerror("SQL error", str(e))


    def db_check(self):
        try:
            db = DBX.select("SELECT DATABASE() AS db")
            n_users = DBX.select("SELECT COUNT(*) AS n FROM app_user")
            n_games = DBX.select("SELECT COUNT(*) AS n FROM bg_sales_game")

            def one(rows):
                if not rows:
                    return None
                r0 = rows[0]
                if isinstance(r0, dict):
                    return list(r0.values())[0]
                return r0[0]

            msg = (
                f"DATABASE(): {one(db)}\n"
                f"app_user rows: {one(n_users)}\n"
                f"bg_sales_game rows: {one(n_games)}\n\n"
                f"run_query supports fetch kw: {DBX.has_fetch}\n"
                f"run_query supports commit kw: {DBX.has_commit}\n"
            )
            messagebox.showinfo("DB Check", msg)
        except Exception as e:
            messagebox.showerror("DB Check failed", str(e))


if __name__ == "__main__":
    App().mainloop()