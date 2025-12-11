import pandas as pd


ESRB_IN  = "Video_games_esrb_rating.csv"
META_IN  = "Games.csv"
SALES_IN = "video_games_sales.csv"

def pick_col(df, options):
    """Return first matching column name from options (case-insensitive)."""
    lower = {c.lower(): c for c in df.columns}
    for opt in options:
        if opt.lower() in lower:
            return lower[opt.lower()]
    return None


esrb = pd.read_csv(ESRB_IN)

title_c = pick_col(esrb, ["title", "name", "game", "game_title"])
esrb_c  = pick_col(esrb, ["esrb", "rating", "esrb_rating"])
dev_c   = pick_col(esrb, ["developer", "dev"])
pub_c   = pick_col(esrb, ["publisher", "pub"])
date_c  = pick_col(esrb, ["release_date", "released", "release", "date"])

out_esrb = pd.DataFrame({
    "esrb_game_id": range(1, len(esrb) + 1),
    "title": esrb[title_c] if title_c else None,
    "esrb": esrb[esrb_c] if esrb_c else None,
    "developer": esrb[dev_c] if dev_c else None,
    "publisher": esrb[pub_c] if pub_c else None,
    "release_date": esrb[date_c] if date_c else None,
    "source": "kaggle:imohtn/video-games-rating-by-esrb"
})
out_esrb.to_csv("bg_esrb_game.csv", index=False)


meta = pd.read_csv(META_IN)

title_c = pick_col(meta, ["title", "name", "game", "game_title"])
plat_c  = pick_col(meta, ["platform", "platforms"])
ms_c    = pick_col(meta, ["meta_score", "metascore", "metacritic", "critic_score"])
us_c    = pick_col(meta, ["user_score", "userscore"])
date_c  = pick_col(meta, ["release_date", "released", "release", "date"])
dev_c   = pick_col(meta, ["developer", "dev"])
pub_c   = pick_col(meta, ["publisher", "pub"])
gen_c   = pick_col(meta, ["genre", "genres"])

out_meta = pd.DataFrame({
    "meta_game_id": range(1, len(meta) + 1),
    "title": meta[title_c] if title_c else None,
    "platform": meta[plat_c] if plat_c else None,
    "meta_score": pd.to_numeric(meta[ms_c], errors="coerce") if ms_c else None,
    "user_score": pd.to_numeric(meta[us_c], errors="coerce") if us_c else None,
    "release_date": meta[date_c] if date_c else None,
    "developer": meta[dev_c] if dev_c else None,
    "publisher": meta[pub_c] if pub_c else None,
    "genre": meta[gen_c] if gen_c else None,
    "source": "kaggle:mohamedhanyyy/video-games"
})
out_meta.to_csv("bg_meta_game.csv", index=False)


sales = pd.read_csv(SALES_IN)

title_c = pick_col(sales, ["name", "title", "game", "game_title"])
plat_c  = pick_col(sales, ["platform"])
gen_c   = pick_col(sales, ["genre"])
pub_c   = pick_col(sales, ["publisher"])
dev_c   = pick_col(sales, ["developer"])
year_c  = pick_col(sales, ["year", "release_year"])


region_cols = [c for c in sales.columns if c.lower() in {
    "na_sales","eu_sales","jp_sales","other_sales","global_sales",
    "north_america","europe","japan","other","global"
}]


out_sales_game = pd.DataFrame({
    "sales_game_id": range(1, len(sales) + 1),
    "title": sales[title_c] if title_c else None,
    "platform": sales[plat_c] if plat_c else None,
    "genre": sales[gen_c] if gen_c else None,
    "publisher": sales[pub_c] if pub_c else None,
    "developer": sales[dev_c] if dev_c else None,
    "release_year": pd.to_numeric(sales[year_c], errors="coerce") if year_c else None,
    "source": "kaggle:ulrikthygepedersen/video-games-sales"
})
out_sales_game.to_csv("bg_sales_game.csv", index=False)


records = []
sales_id = 1
for i in range(len(sales)):
    game_id = i + 1
    for col in region_cols:
        val = sales.at[i, col]
        if pd.isna(val):
            continue
      
        records.append([sales_id, game_id, col, float(val), "kaggle:ulrikthygepedersen/video-games-sales"])
        sales_id += 1

out_sales_record = pd.DataFrame(records, columns=[
    "sales_id", "sales_game_id", "region", "sales_millions", "source"
])
out_sales_record.to_csv("bg_sales_record.csv", index=False)

print("Wrote: bg_esrb_game.csv, bg_meta_game.csv, bg_sales_game.csv, bg_sales_record.csv")
print("Region columns used:", region_cols)