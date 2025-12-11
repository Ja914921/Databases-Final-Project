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
        # Single-argument 
        if len(self.params) == 1:
            return self.fn(sql)

        # Keyword-style
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

        # Fallback
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

class LoginWindow(tk.Tk):
    """
    Simple login / create-account window shown before the main GUI.
    Uses app_user table for accounts.
    """

    def __init__(self):
        super().__init__()
        self.title("GameSearch Login")
        self.geometry("400x220")
        self.resizable(False, False)

        self.current_user_id = None
        self.current_username = None

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="GameSearch Login", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 10)
        )

        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky="e", pady=4)
        self.e_user = ttk.Entry(frame, width=25)
        self.e_user.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e", pady=4)
        self.e_pass = ttk.Entry(frame, width=25, show="*")
        self.e_pass.grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Email (for new account):").grid(row=3, column=0, sticky="e", pady=4)
        self.e_email = ttk.Entry(frame, width=25)
        self.e_email.grid(row=3, column=1, sticky="w", pady=4)

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, columnspan=2, pady=(12, 0))

        ttk.Button(btns, text="Login", command=self.do_login).pack(side="left", padx=6)
        ttk.Button(btns, text="Create Account", command=self.do_create).pack(side="left", padx=6)
        ttk.Button(btns, text="Quit", command=self.destroy).pack(side="left", padx=6)

    def _one(self, rows):
        """
        Helper: get first value of first row, works for list-of-tuples or list-of-dicts.
        """
        if not rows:
            return None
        r0 = rows[0]
        if isinstance(r0, dict):
            return list(r0.values())[0]
        return r0[0]

    def do_login(self):
        uname = self.e_user.get().strip()
        pw = self.e_pass.get().strip()
        if not uname or not pw:
            messagebox.showerror("Missing", "Enter username and password.")
            return

        try:
            # Look up user_id by username
            rows_uid = DBX.select("SELECT user_id FROM app_user WHERE username=%s", (uname,))
            uid = self._one(rows_uid)
            if uid is None:
                messagebox.showerror("Login failed", "No such user.")
                return

            # Look up stored password hash
            rows_hash = DBX.select("SELECT password_hash FROM app_user WHERE user_id=%s", (uid,))
            stored = self._one(rows_hash)
            if not stored or stored != sha256(pw):
                messagebox.showerror("Login failed", "Incorrect password.")
                return

            # Success
            self.current_user_id = uid
            self.current_username = uname
            self.destroy()
        except Exception as e:
            messagebox.showerror("Login error", str(e))

    def do_create(self):
        uname = self.e_user.get().strip()
        pw = self.e_pass.get().strip()
        email = self.e_email.get().strip().lower()

        if not uname or not pw or not email:
            messagebox.showerror("Missing", "Username, email, and password are required.")
            return

        try:
            # Try to insert
            DBX.exec(
                "INSERT INTO app_user (username, email, password_hash) VALUES (%s, %s, %s)",
                (uname, email, sha256(pw)),
            )

            # Get new user_id
            rows_uid = DBX.select("SELECT user_id FROM app_user WHERE username=%s", (uname,))
            uid = self._one(rows_uid)

            self.current_user_id = uid
            self.current_username = uname
            messagebox.showinfo("Account created", "Account created and logged in.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Create failed", str(e))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_result(result):
    """Normalize various possible run_query return styles into (cols, rows)."""
    if result is None:
        return ["info"], [("No result returned.",)]

    # (cols, rows) where cols is a list, rows is list-of-rows
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], (list, tuple)):
        cols = list(result[0])
        rows = [tuple(r) for r in list(result[1])]
        return cols, rows

    # Empty list
    if isinstance(result, list) and not result:
        return ["info"], [("No rows returned.",)]

    # List of dicts
    if isinstance(result, list) and result and isinstance(result[0], dict):
        cols = list(result[0].keys())
        rows = [tuple(r.get(c) for c in cols) for r in result]
        return cols, rows

    # List of lists/tuples
    if isinstance(result, list) and result and isinstance(result[0], (list, tuple)):
        rows = [tuple(r) for r in result]
        cols = [f"col{i+1}" for i in range(len(rows[0]))]
        return cols, rows

    # Fallback
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
    def __init__(self, current_user_id=None, current_username=None):
        super().__init__()
        self.current_user_id = current_user_id
        self.current_username = current_username

        self.title("GameSearch DB App (Checkpoint 2)")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        self.geometry("1200x700")
        self.minsize(1000, 600)

        # Current logged-in user 
        self.current_user_id = None
        self.current_username = None

        self.selected_game_id = None
        self.selected_user_id = None

        # Header with auth + DB check
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")

        ttk.Label(header, text="GameSearch DB App", font=("Segoe UI", 16, "bold")).pack(side="left")

        auth = ttk.Frame(header)
        auth.pack(side="right")

        self.auth_label = tk.StringVar(value="Not logged in")
        ttk.Label(auth, textvariable=self.auth_label).pack(side="right", padx=4)
        ttk.Button(auth, text="Logout", command=self.logout).pack(side="right", padx=4)
        ttk.Button(auth, text="Login", command=self.show_login_dialog).pack(side="right", padx=4)
        ttk.Button(auth, text="DB Check", command=self.db_check).pack(side="right", padx=4)

        # Status line
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", padx=12)

        # Tabs
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_search = ttk.Frame(nb, padding=10)
        self.tab_users = ttk.Frame(nb, padding=10)
        self.tab_analytics = ttk.Frame(nb, padding=10)
        self.tab_console = ttk.Frame(nb, padding=10)

        nb.add(self.tab_search, text="Search (bg_sales_game)")
        nb.add(self.tab_users, text="Users (CRUD app_user)")
        nb.add(self.tab_analytics, text="Analytics (SQL views)")
        nb.add(self.tab_console, text="SQL Console (SELECT/WITH)")

        self._build_search()
        self._build_users()
        self._build_analytics()
        self._build_console()

        self.load_users()

    def _set(self, msg: str):
        self.status.set(msg)

    # Login / access control
    def require_login(self, action_desc: str) -> bool:
        """Show an error and return False if no user is logged in."""
        if self.current_user_id is None:
            messagebox.showerror("Login required", f"You must log in to {action_desc}.")
            return False
        return True

    def show_login_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Login")
        dlg.transient(self)
        dlg.grab_set()

        ttk.Label(dlg, text="Username:").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        e_user = ttk.Entry(dlg, width=24)
        e_user.grid(row=0, column=1, sticky="w", padx=8, pady=(8, 4))

        ttk.Label(dlg, text="Password:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        e_pw = ttk.Entry(dlg, width=24, show="*")
        e_pw.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        def do_login():
            username = e_user.get().strip()
            pw = e_pw.get()
            if not username or not pw:
                messagebox.showerror("Missing", "Username and password are required.")
                return

            sql = """
            SELECT user_id, username, password_hash, is_active
            FROM app_user
            WHERE username = %s
            LIMIT 1
            """
            try:
                rows = DBX.select(sql, (username,))
            except Exception as e:
                messagebox.showerror("Login failed", str(e))
                return

            if not rows:
                messagebox.showerror("Login failed", "User not found.")
                return

            row0 = rows[0]
            if isinstance(row0, dict):
                user_id = row0.get("user_id")
                db_username = row0.get("username")
                pw_hash = row0.get("password_hash")
                is_active = row0.get("is_active")
            else:
                user_id, db_username, pw_hash, is_active = row0[0], row0[1], row0[2], row0[3]

            if not is_active:
                messagebox.showerror("Login failed", "This account is inactive.")
                return

            if sha256(pw) != pw_hash:
                messagebox.showerror("Login failed", "Incorrect password.")
                return

            self.current_user_id = user_id
            self.current_username = db_username
            self.auth_label.set(f"Logged in as: {db_username}")
            self._set(f"Logged in as {db_username}.")
            self.audit("login", "app_user", db_username, "User login from GUI")
            dlg.destroy()

        btns = ttk.Frame(dlg)
        btns.grid(row=2, column=0, columnspan=2, pady=(8, 8), padx=8, sticky="e")
        ttk.Button(btns, text="Login", command=do_login).pack(side="right", padx=4)
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="right", padx=4)

        dlg.bind("<Return>", lambda _e: do_login())

    def logout(self):
        if self.current_user_id is None:
            messagebox.showinfo("Logout", "No user is currently logged in.")
            return
        self.audit("logout", "app_user", self.current_username, "User logout from GUI")
        self.current_user_id = None
        self.current_username = None
        self.auth_label.set("Not logged in")
        self._set("Logged out.")

    def audit(self, action_type, entity_type, entity_id, details=None):
        """Write a row into app_audit_log. Swallows errors so GUI never crashes."""
        try:
            DBX.exec(
                """
                INSERT INTO app_audit_log (user_id, action_type, entity_type, entity_id, details)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    self.current_user_id,
                    action_type,
                    entity_type,
                    str(entity_id) if entity_id is not None else None,
                    details,
                ),
            )
        except Exception:
            # If audit table or FK fails, ignore silently 
            pass

    # Search tab
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

    # Users tab (CRUD)
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
            "Demo tip: Login as admin, then Create -> Update -> Delete (or deactivate) a user, "
            "then verify in SQL Console:\n"
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
        """
        Create user.
        Note: For demo simplicity this does NOT require login,
        so you can bootstrap accounts. Update/Delete do require login.
        """
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
            self.audit("create", "app_user", username, f"Created user {username}")
            self.np.delete(0, tk.END)
            self.load_users()
        except Exception as e:
            messagebox.showerror("Create failed", str(e))

    def update_user(self):
        u = SCHEMA["user"]
        if not self.selected_user_id:
            messagebox.showerror("No selection", "Select a user row first.")
            return

        if not self.require_login("update users"):
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
            self.audit("update", "app_user", username, f"Updated user_id={self.selected_user_id}")
            self.np.delete(0, tk.END)
            self.load_users()
        except Exception as e:
            messagebox.showerror("Update failed", str(e))

    def delete_user(self):
        u = SCHEMA["user"]
        if not self.selected_user_id:
            messagebox.showerror("No selection", "Select a user row first.")
            return

        if not self.require_login("delete users"):
            return

        if not messagebox.askyesno("Confirm", f"Delete user_id={self.selected_user_id}?"):
            return

        username = self.nu.get().strip() or self.selected_user_id

        try:
            DBX.exec(f"DELETE FROM {u['table']} WHERE {u['id']}=%s", (self.selected_user_id,))
            self._set("User deleted.")
            self.audit("delete", "app_user", username, f"Deleted user_id={self.selected_user_id}")
            self.clear_user_form()
            self.load_users()
            return
        except Exception:
            try:
                DBX.exec(
                    f"UPDATE {u['table']} SET {u['active']}=0 WHERE {u['id']}=%s",
                    (self.selected_user_id,),
                )
                self.active_var.set(0)
                self._set("User deactivated (FK prevented hard delete).")
                self.audit("deactivate", "app_user", username, f"Deactivated user_id={self.selected_user_id}")
                self.load_users()
            except Exception as e2:
                messagebox.showerror("Delete failed", str(e2))


    # Analytics tab
    def _build_analytics(self):
        top = ttk.LabelFrame(self.tab_analytics, text="Analytics controls", padding=10)
        top.pack(fill="x")

        # Top N global sales
        ttk.Label(top, text="Top N games by global sales:").grid(row=0, column=0, sticky="w")
        self.topn_entry = ttk.Entry(top, width=6)
        self.topn_entry.grid(row=0, column=1, sticky="w", padx=(4, 12))
        self.topn_entry.insert(0, "10")
        ttk.Button(top, text="Run", command=self.analytics_top_sales).grid(row=0, column=2, padx=4, pady=2)

        # Sales by ESRB rating
        ttk.Label(
            top,
            text="Sales by ESRB rating (joins ESRB + sales datasets):",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Button(top, text="Run", command=self.analytics_sales_by_esrb).grid(row=1, column=2, padx=4, pady=2)


        out = ttk.LabelFrame(self.tab_analytics, text="Analytics results", padding=10)
        out.pack(fill="both", expand=True, pady=(10, 0))
        self.analytics_tree = make_tree(out)

        ttk.Label(
            self.tab_analytics,
            text=(
                "These views demonstrate analytical SQL over Kaggle data + app tables.\n"
                "- Top N by SUM(sales_millions)\n"
                "- Sales grouped by ESRB rating via title match\n"
                "- Top rated games from app_game_review joined to bg_meta_game"
            ),
        ).pack(anchor="w", pady=(6, 0))

    def analytics_top_sales(self):
        n_text = self.topn_entry.get().strip()
        if not n_text:
            n_text = "10"
            self.topn_entry.insert(0, n_text)
        try:
            n = int(n_text)
            if n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Bad N", "Top N must be a positive whole number.")
            return

        sql = """
        SELECT
            g.sales_game_id,
            g.title,
            g.platform,
            SUM(r.sales_millions) AS total_sales_millions
        FROM bg_sales_game AS g
        JOIN bg_sales_record AS r
          ON g.sales_game_id = r.sales_game_id
        GROUP BY g.sales_game_id, g.title, g.platform
        ORDER BY total_sales_millions DESC
        LIMIT %s
        """
        try:
            rows = DBX.select(sql, (n,))
            render(self.analytics_tree, rows)
            self._set(f"Top {n} games by global sales: {count_rows(rows)} rows.")
        except Exception as e:
            messagebox.showerror("Analytics error", str(e))

    def analytics_sales_by_esrb(self):
        # Join ESRB and sales directly by title 
        sql = """
        SELECT
            e.esrb AS esrb_rating,
            COUNT(DISTINCT g.sales_game_id) AS num_games,
            SUM(r.sales_millions) AS total_sales_millions
        FROM bg_esrb_game AS e
        JOIN bg_sales_game AS g
          ON e.title = g.title
        JOIN bg_sales_record AS r
          ON r.sales_game_id = g.sales_game_id
        GROUP BY e.esrb
        ORDER BY total_sales_millions DESC;
        """
        try:
            rows = DBX.select(sql)
            render(self.analytics_tree, rows)
            self._set(f"Sales by ESRB rating: {count_rows(rows)} rows.")
        except Exception as e:
            messagebox.showerror("Analytics error", str(e))

    
    # Console tab
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
            "LIMIT 10;\n",
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
            "LIMIT 25;\n",
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

    # DB check helper
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
    # First show login 
    login = LoginWindow()
    login.mainloop()

    if getattr(login, "current_user_id", None):
        app = App(
            current_user_id=login.current_user_id,
            current_username=login.current_username,
        )
        app.mainloop()