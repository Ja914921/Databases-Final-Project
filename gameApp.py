import sys
from textwrap import shorten

import mysql.connector
from mysql.connector import Error

# configuration for mySQL
DB_CONFIG = {
    "host": "127.0.0.1",          
    "port": 3306,               
    "user": "root",              
    "password": "Alonso04.", 
    "database": "gamesearch_db"  
}


# DB HELPER FUNCTIONS

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if not conn.is_connected():
            raise RuntimeError("Failed to connect to MySQL (is the server running?)")
        return conn
    except Error as e:
        print(f"[ERROR] Could not connect to MySQL: {e}")
        sys.exit(1)


def run_query(query, params=None, fetch=True):

    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(query, params or ())
            if fetch:
                rows = cur.fetchall()
            else:
                conn.commit()
                rows = None
        return rows
    finally:
        conn.close()


def print_table(rows, max_width=40):

    if not rows:
        print("No results.")
        return

    # Column names from keys of first row
    columns = list(rows[0].keys())

    # Compute column widths
    col_widths = {}
    for col in columns:
        max_len = max(len(str(row[col])) if row[col] is not None else 0 for row in rows)
        col_widths[col] = min(max(max_len, len(col)), max_width)

    # Header
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    sep = "-+-".join("-" * col_widths[col] for col in columns)
    print(header)
    print(sep)

    # Rows
    for row in rows:
        line_parts = []
        for col in columns:
            val = "" if row[col] is None else str(row[col])
            val = shorten(val, width=col_widths[col], placeholder="…")
            line_parts.append(val.ljust(col_widths[col]))
        print(" | ".join(line_parts))


# FEATURES / QUERIES

def list_top_global_sales(limit=10):
    """
    List the top N games by global sales.
    """
    query = """
        SELECT
            name,
            platform,
            year,
            genre,
            publisher,
            global_sales
        FROM bg_sales_game
        ORDER BY global_sales DESC
        LIMIT %s;
    """
    rows = run_query(query, (limit,))
    print(f"\nTop {limit} games by global sales:\n")
    print_table(rows)


def search_game_by_name():
    """
    Search for a game by a partial name and show both sales and ESRB info.
    """
    term = input("Enter part of the game name: ").strip()
    if not term:
        print("Search term cannot be empty.")
        return

    # Join on title/name using LIKE
    query = """
        SELECT
            s.name,
            s.platform,
            s.year,
            s.genre,
            s.publisher,
            s.global_sales,
            e.esrb_rating
        FROM bg_sales_game AS s
        LEFT JOIN bg_esrb_game AS e
            ON e.title = s.name
        WHERE s.name LIKE %s
        ORDER BY s.global_sales DESC
        LIMIT 25;
    """
    rows = run_query(query, (f"%{term}%",))
    print(f"\nSearch results for '{term}':\n")
    print_table(rows)


def average_sales_by_rating():
    """
    Show average global sales grouped by ESRB rating
    (only for games that exist in both tables).
    """
    query = """
        SELECT
            e.esrb_rating,
            COUNT(*) AS num_games,
            ROUND(AVG(s.global_sales), 2) AS avg_global_sales
        FROM bg_esrb_game AS e
        JOIN bg_sales_game AS s
            ON e.title = s.name
        GROUP BY e.esrb_rating
        ORDER BY avg_global_sales DESC;
    """
    rows = run_query(query)
    print("\nAverage global sales by ESRB rating (only games with both info):\n")
    print_table(rows)


def list_games_by_rating_min_sales():
    """
    Ask the user for an ESRB rating and a minimum global sales threshold,
    then show games that match.
    """
    rating = input("Enter ESRB rating (e.g., E, T, M, E10, etc.): ").strip().upper()
    if not rating:
        print("Rating cannot be empty.")
        return

    try:
        min_sales = float(input("Enter minimum global sales (in millions, e.g., 1.0): ").strip())
    except ValueError:
        print("Invalid number for minimum sales.")
        return

    query = """
        SELECT
            s.name,
            s.platform,
            s.year,
            s.genre,
            s.global_sales,
            e.esrb_rating
        FROM bg_esrb_game AS e
        JOIN bg_sales_game AS s
            ON e.title = s.name
        WHERE e.esrb_rating = %s
          AND s.global_sales >= %s
        ORDER BY s.global_sales DESC;
    """
    rows = run_query(query, (rating, min_sales))
    print(f"\nGames rated {rating} with global sales >= {min_sales} million:\n")
    print_table(rows)



def print_menu():
    print("\n=== Video Game Database App ===")
    print("1) List top games by global sales")
    print("2) Search for a game by name (sales + ESRB)")
    print("3) Average global sales by ESRB rating")
    print("4) Games by ESRB rating and minimum sales")
    print("0) Exit")


def main():
    print("Connecting using configuration:")
    print(f"  host={DB_CONFIG['host']}, database={DB_CONFIG['database']}\n")

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            try:
                n = int(input("How many top games? (default 10): ").strip() or "10")
            except ValueError:
                n = 10
            list_top_global_sales(limit=n)
        elif choice == "2":
            search_game_by_name()
        elif choice == "3":
            average_sales_by_rating()
        elif choice == "4":
            list_games_by_rating_min_sales()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()