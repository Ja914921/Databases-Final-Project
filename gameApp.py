import sys
from textwrap import shorten

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "Alonso04.",
    "database": "gamesearch_db",
}


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
                return cur.fetchall()
            conn.commit()
            return None
    finally:
        conn.close()


def print_table(rows, max_width=40):
    if not rows:
        print("No results.")
        return

    columns = list(rows[0].keys())
    col_widths = {}
    for col in columns:
        max_len = max(len(str(row[col])) if row[col] is not None else 0 for row in rows)
        col_widths[col] = min(max(max_len, len(col)), max_width)

    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    sep = "-+-".join("-" * col_widths[col] for col in columns)
    print(header)
    print(sep)

    for row in rows:
        line_parts = []
        for col in columns:
            val = "" if row[col] is None else str(row[col])
            val = shorten(val, width=col_widths[col], placeholder="…")
            line_parts.append(val.ljust(col_widths[col]))
        print(" | ".join(line_parts))


def _global_sales_expr():
    return """
    COALESCE(
      MAX(CASE WHEN LOWER(r.region) LIKE '%global%' THEN r.sales_millions END),
      SUM(r.sales_millions)
    )
    """


def list_top_global_sales(limit=10):
    query = f"""
    SELECT
      g.title,
      g.platform,
      g.release_year,
      g.genre,
      g.publisher,
      ROUND({_global_sales_expr()}, 3) AS global_sales_millions
    FROM bg_sales_game g
    JOIN bg_sales_record r ON r.sales_game_id = g.sales_game_id
    GROUP BY g.sales_game_id, g.title, g.platform, g.release_year, g.genre, g.publisher
    ORDER BY global_sales_millions DESC
    LIMIT %s;
    """
    rows = run_query(query, (limit,))
    print(f"\nTop {limit} games by global sales:\n")
    print_table(rows)


def search_game_by_name():
    term = input("Enter part of the game title: ").strip()
    if not term:
        print("Search term cannot be empty.")
        return

    query = f"""
    SELECT
      g.title,
      g.platform,
      g.release_year,
      g.genre,
      g.publisher,
      ROUND({_global_sales_expr()}, 3) AS global_sales_millions,
      e.esrb AS esrb
    FROM bg_sales_game g
    JOIN bg_sales_record r ON r.sales_game_id = g.sales_game_id
    LEFT JOIN bg_esrb_game e ON e.title = g.title
    WHERE g.title LIKE %s
    GROUP BY g.sales_game_id, g.title, g.platform, g.release_year, g.genre, g.publisher, e.esrb
    ORDER BY global_sales_millions DESC
    LIMIT 25;
    """
    rows = run_query(query, (f"%{term}%",))
    print(f"\nSearch results for '{term}':\n")
    print_table(rows)


def average_sales_by_esrb():
    query = f"""
    SELECT
      e.esrb AS esrb,
      COUNT(*) AS num_games,
      ROUND(AVG(global_sales_millions), 2) AS avg_global_sales_millions
    FROM (
      SELECT
        g.sales_game_id,
        COALESCE(
          MAX(CASE WHEN LOWER(r.region) LIKE '%global%' THEN r.sales_millions END),
          SUM(r.sales_millions)
        ) AS global_sales_millions
      FROM bg_sales_game g
      JOIN bg_sales_record r ON r.sales_game_id = g.sales_game_id
      GROUP BY g.sales_game_id
    ) s
    JOIN bg_sales_game g ON g.sales_game_id = s.sales_game_id
    JOIN bg_esrb_game e ON e.title = g.title
    GROUP BY e.esrb
    ORDER BY avg_global_sales_millions DESC;
    """
    rows = run_query(query)
    print("\nAverage global sales by ESRB (only games with ESRB + sales):\n")
    print_table(rows)


def list_games_by_esrb_min_sales():
    rating = input("Enter ESRB rating (e.g., E, T, M, E10+, etc.): ").strip().upper()
    if not rating:
        print("Rating cannot be empty.")
        return

    try:
        min_sales = float(input("Enter minimum global sales (millions, e.g., 1.0): ").strip() or "0")
    except ValueError:
        print("Invalid number for minimum sales.")
        return

    query = f"""
    SELECT
      g.title,
      g.platform,
      g.release_year,
      g.genre,
      ROUND({_global_sales_expr()}, 3) AS global_sales_millions,
      e.esrb AS esrb
    FROM bg_sales_game g
    JOIN bg_sales_record r ON r.sales_game_id = g.sales_game_id
    JOIN bg_esrb_game e ON e.title = g.title
    WHERE e.esrb = %s
    GROUP BY g.sales_game_id, g.title, g.platform, g.release_year, g.genre, e.esrb
    HAVING global_sales_millions >= %s
    ORDER BY global_sales_millions DESC;
    """
    rows = run_query(query, (rating, min_sales))
    print(f"\nGames rated {rating} with global sales >= {min_sales} million:\n")
    print_table(rows)


def create_user(username, email, password_hash):
    q = """
    INSERT INTO app_user (username, email, password_hash)
    VALUES (%s, %s, %s);
    """
    run_query(q, (username, email, password_hash), fetch=False)


def update_user_settings(user_id, preferred_platform=None, preferred_genre=None, show_mature=1):
    q = """
    INSERT INTO app_user_settings (user_id, preferred_platform, preferred_genre, show_mature)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      preferred_platform = VALUES(preferred_platform),
      preferred_genre = VALUES(preferred_genre),
      show_mature = VALUES(show_mature);
    """
    run_query(q, (user_id, preferred_platform, preferred_genre, int(show_mature)), fetch=False)


def delete_user(user_id):
    q = "DELETE FROM app_user WHERE user_id = %s;"
    run_query(q, (user_id,), fetch=False)


def save_filter_preset(user_id, preset_name, platform=None, genre=None, esrb=None, min_meta=None):
    q = """
    INSERT INTO app_filter_preset (user_id, preset_name, platform, genre, esrb, min_meta)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      platform = VALUES(platform),
      genre = VALUES(genre),
      esrb = VALUES(esrb),
      min_meta = VALUES(min_meta);
    """
    run_query(q, (user_id, preset_name, platform, genre, esrb, min_meta), fetch=False)


def create_favorite_list(user_id, list_name):
    q = "INSERT INTO app_favorite_list (user_id, list_name) VALUES (%s, %s);"
    run_query(q, (user_id, list_name), fetch=False)


def add_favorite_item(favorite_list_id, meta_game_id=None, sales_game_id=None, esrb_game_id=None, notes=None):
    q = """
    INSERT INTO app_favorite_item (favorite_list_id, meta_game_id, sales_game_id, esrb_game_id, notes)
    VALUES (%s, %s, %s, %s, %s);
    """
    run_query(q, (favorite_list_id, meta_game_id, sales_game_id, esrb_game_id, notes), fetch=False)


def delete_favorite_item(favorite_item_id):
    q = "DELETE FROM app_favorite_item WHERE favorite_item_id = %s;"
    run_query(q, (favorite_item_id,), fetch=False)


def create_review(user_id, rating, review_text=None, meta_game_id=None, sales_game_id=None, esrb_game_id=None):
    q = """
    INSERT INTO app_game_review (user_id, meta_game_id, sales_game_id, esrb_game_id, rating, review_text)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    run_query(q, (user_id, meta_game_id, sales_game_id, esrb_game_id, rating, review_text), fetch=False)


def update_review(review_id, rating=None, review_text=None):
    q = """
    UPDATE app_game_review
    SET
      rating = COALESCE(%s, rating),
      review_text = COALESCE(%s, review_text)
    WHERE review_id = %s;
    """
    run_query(q, (rating, review_text, review_id), fetch=False)


def delete_review(review_id):
    q = "DELETE FROM app_game_review WHERE review_id = %s;"
    run_query(q, (review_id,), fetch=False)


def print_menu():
    print("\n=== Video Game Database App (CLI) ===")
    print("READ/FILTER:")
    print("1) List top games by global sales")
    print("2) Search games by title (sales + ESRB)")
    print("3) Average global sales by ESRB")
    print("4) Filter games by ESRB + min sales")
    print("\nWRITE/UPDATE/DELETE (App tables):")
    print("5) Create user")
    print("6) Update user settings")
    print("7) Delete user")
    print("8) Create favorite list")
    print("9) Add favorite item")
    print("10) Delete favorite item")
    print("11) Create review")
    print("12) Update review")
    print("13) Delete review")
    print("14) Save filter preset")
    print("\n0) Exit")


def main():
    print("Connecting using configuration:")
    print(f"  host={DB_CONFIG['host']}, database={DB_CONFIG['database']}\n")

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                try:
                    n = int(input("How many top games? (default 10): ").strip() or "10")
                except ValueError:
                    n = 10
                list_top_global_sales(limit=n)

            elif choice == "2":
                search_game_by_name()

            elif choice == "3":
                average_sales_by_esrb()

            elif choice == "4":
                list_games_by_esrb_min_sales()

            elif choice == "5":
                username = input("username: ").strip()
                email = input("email: ").strip()
                pw = input("password_hash (for demo, type anything): ").strip()
                create_user(username, email, pw)
                print("User created.")

            elif choice == "6":
                user_id = int(input("user_id: ").strip())
                plat = input("preferred_platform (blank ok): ").strip() or None
                genre = input("preferred_genre (blank ok): ").strip() or None
                show = input("show_mature (1/0, default 1): ").strip()
                show_mature = 1 if show == "" else int(show)
                update_user_settings(user_id, plat, genre, show_mature)
                print("Settings saved.")

            elif choice == "7":
                user_id = int(input("user_id to delete: ").strip())
                delete_user(user_id)
                print("User deleted.")

            elif choice == "8":
                user_id = int(input("user_id: ").strip())
                name = input("list_name: ").strip()
                create_favorite_list(user_id, name)
                print("Favorite list created.")

            elif choice == "9":
                fav_list_id = int(input("favorite_list_id: ").strip())
                meta = input("meta_game_id (blank ok): ").strip() or None
                sales = input("sales_game_id (blank ok): ").strip() or None
                esrb = input("esrb_game_id (blank ok): ").strip() or None
                notes = input("notes (blank ok): ").strip() or None
                add_favorite_item(
                    fav_list_id,
                    int(meta) if meta else None,
                    int(sales) if sales else None,
                    int(esrb) if esrb else None,
                    notes,
                )
                print("Favorite item added.")

            elif choice == "10":
                item_id = int(input("favorite_item_id to delete: ").strip())
                delete_favorite_item(item_id)
                print("Favorite item deleted.")

            elif choice == "11":
                user_id = int(input("user_id: ").strip())
                rating = int(input("rating (1-10): ").strip())
                text = input("review_text (blank ok): ").strip() or None
                meta = input("meta_game_id (blank ok): ").strip() or None
                sales = input("sales_game_id (blank ok): ").strip() or None
                esrb = input("esrb_game_id (blank ok): ").strip() or None
                create_review(
                    user_id=user_id,
                    rating=rating,
                    review_text=text,
                    meta_game_id=int(meta) if meta else None,
                    sales_game_id=int(sales) if sales else None,
                    esrb_game_id=int(esrb) if esrb else None,
                )
                print("Review created.")

            elif choice == "12":
                review_id = int(input("review_id: ").strip())
                rating_in = input("new rating (blank to keep): ").strip()
                text_in = input("new review_text (blank to keep): ").strip()
                rating = int(rating_in) if rating_in else None
                text = text_in if text_in else None
                update_review(review_id, rating=rating, review_text=text)
                print("Review updated.")

            elif choice == "13":
                review_id = int(input("review_id to delete: ").strip())
                delete_review(review_id)
                print("Review deleted.")

            elif choice == "14":
                user_id = int(input("user_id: ").strip())
                preset = input("preset_name: ").strip()
                plat = input("platform (blank ok): ").strip() or None
                genre = input("genre (blank ok): ").strip() or None
                esrb = input("esrb (blank ok): ").strip() or None
                min_meta_in = input("min_meta (blank ok): ").strip()
                min_meta = int(min_meta_in) if min_meta_in else None
                save_filter_preset(user_id, preset, plat, genre, esrb, min_meta)
                print("Preset saved.")

            elif choice == "0":
                print("Goodbye!")
                break

            else:
                print("Invalid choice, please try again.")

        except Error as e:
            print(f"[DB ERROR] {e}")
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    main() 