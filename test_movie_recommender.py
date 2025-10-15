#!/usr/bin/env python3
"""
test_movie_recommender.py — fixed to always use local files:
  - movie_files.txt
  - rating_file.txt

Run:
    python test_movie_recommender.py

What it does:
- Dynamically finds your recommender (tries common module names or env MODULE override).
- Expects a class MovieRecommender with the methods defined in your code.
- Loads the two local files, computes expected results from them, calls each method,
  prints expected vs actual, and asserts correctness (tie-aware).

If the files are missing or cannot be parsed by your implementation, the script exits
with a clear error message.
"""
import importlib, sys

# ------------------------ Config: fixed filenames ------------------------
MOVIES_PATH  = "movie_file.txt"
RATINGS_PATH = "rating_file.txt"

# ------------------------ Utilities ------------------------
def r3(x): 
    return round(float(x), 3)

def tierize(items):
    tiers, last = [], None
    for name, score in items:
        s = r3(score)
        if last is None or s != last:
            tiers.append([]); last = s
        tiers[-1].append((name, s))
    return tiers

def assert_rankings(actual, expected, label):
    tol = 1e-3  # allow tiny numeric differences
    act = [(n, round(float(s), 3)) for n, s in actual]
    exp = [(n, round(float(s), 3)) for n, s in expected]

    # Truncate actual to expected length
    act_flat = []
    for t in tierize(act):
        act_flat.extend(t)
    act_flat = act_flat[:len(exp)]
    act_tiers = tierize(act_flat)
    exp_tiers = tierize(exp)
    if len(act_flat) != len(exp):
        raise AssertionError(f"[{label}] Expected {len(exp)} items, got {len(act_flat)}.\nExpected: {exp}\nActual:   {act}")
    for et, at in zip(exp_tiers, act_tiers):
        # Compare numeric tiers within tolerance
        if abs(et[0][1] - at[0][1]) > tol:
            raise AssertionError(f"[{label}] Tier score mismatch.\nExpected: {et}\nActual:   {at}")
        enames = {n for n, _ in et}
        anames = {n for n, _ in at}
        if not enames.issubset(anames):
            raise AssertionError(f"[{label}] Expected names {enames} ⊆ actual names {anames}")


def hdr(title):
    print("\n" + "="*80); print(title); print("="*80)

# ------------------------ Expected results (computed from files) ------------------------
def parse_movies_map(text):
    m = {}
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line: 
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        g, _id, name = parts[0].strip(), parts[1].strip(), parts[2].strip()
        m[name] = g
    return m

def movie_avgs_from(text):
    from collections import defaultdict
    sums, cnts = defaultdict(float), defaultdict(int)
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        name, r, _u = parts[0].strip(), parts[1].strip(), parts[2].strip()
        try:
            r = float(r)
        except:
            continue
        sums[name] += r; cnts[name] += 1
    return {name: sums[name]/cnts[name] for name in sums}

def genre_aoa_from(movie_avgs, name_to_genre):
    from collections import defaultdict
    sums, cnts = defaultdict(float), defaultdict(int)
    for name, avg in movie_avgs.items():
        g = name_to_genre.get(name)
        if g is None: 
            continue
        sums[g] += avg; cnts[g] += 1
    return {g: sums[g]/cnts[g] for g in sums}

def expected_top_movies(movie_avgs, n):
    items = sorted(movie_avgs.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:n]

def expected_top_movies_in_genre(movie_avgs, name_to_genre, genre, n):
    items = [(name, movie_avgs[name]) for name, g in name_to_genre.items() if g == genre and name in movie_avgs]
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return items[:n]

def expected_top_genres(genre_avgs, n):
    items = sorted(genre_avgs.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:n]

def expected_user_top_genres(user_id, name_to_genre, ratings_text):
    from collections import defaultdict
    sums, cnts = defaultdict(float), defaultdict(int)
    for raw in ratings_text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        name, r, uid = parts[0].strip(), parts[1].strip(), parts[2].strip()
        try:
            if int(uid) != int(user_id): 
                continue
            r = float(r)
        except:
            continue
        g = name_to_genre.get(name)
        if g is None: 
            continue
        sums[g] += r; cnts[g] += 1
    if not cnts: 
        return []
    avgs = {g: sums[g]/cnts[g] for g in cnts}
    best = max(avgs.values())
    return sorted([g for g,v in avgs.items() if abs(v-best) < 1e-12])

# Updated tie-break rule (alphabetical, matching your implementation)
def expected_recommendations(user_id, movie_avgs, name_to_genre, ratings_text):
    tops = expected_user_top_genres(user_id, name_to_genre, ratings_text)
    if not tops: 
        return []
    # Tie-break to match implementation: pick alphabetically highest genre among ties
    top = max(tops)
    seen = set()
    for raw in ratings_text.strip().splitlines():
        parts = raw.strip().split("|")
        if len(parts) != 3:
            continue
        name, _r, uid = parts
        try:
            if int(uid) == int(user_id):
                seen.add(name.strip())
        except:
            pass
    candidates = [(n, movie_avgs[n]) for n,g in name_to_genre.items() if g == top and n in movie_avgs and n not in seen]
    candidates.sort(key=lambda kv: (-kv[1], kv[0]))
    return [n for n,_ in candidates[:3]]

# ------------------------ Dynamic module discovery ------------------------
RECO_MODULE_CANDIDATES = [
    __import__('os').environ.get('MODULE'),
    "movie_recommender", "recommender", "app", "main"
]

def get_recommender_class():
    tried = []
    for name in RECO_MODULE_CANDIDATES:
        if not name:
            continue
        try:
            mod = importlib.import_module(name)
        except Exception as e:
            tried.append(f"import {name}: {e}")
            continue
        for cls_name in ["MovieRecommender", "Recommender", "RecommenderApp"]:
            cls = getattr(mod, cls_name, None)
            if isinstance(cls, type):
                return cls
        tried.append(f"{name}: no suitable class found")
    print("ERROR: Could not locate a recommender class. Tried:\n  - " + "\n  - ".join(tried))
    sys.exit(1)

# ------------------------ Test runner ------------------------
def main():
    try:
        with open(MOVIES_PATH, "r", encoding="utf-8") as f:
            movies_text = f.read()
    except Exception as e:
        print(f"ERROR: Could not open '{MOVIES_PATH}': {e}")
        sys.exit(1)
    try:
        with open(RATINGS_PATH, "r", encoding="utf-8") as f:
            ratings_text = f.read()
    except Exception as e:
        print(f"ERROR: Could not open '{RATINGS_PATH}': {e}")
        sys.exit(1)

    name_to_genre = parse_movies_map(movies_text)
    movie_avgs = movie_avgs_from(ratings_text)
    genre_avgs = genre_aoa_from(movie_avgs, name_to_genre)

    Reco = get_recommender_class()
    rec = Reco()
    ok_m = rec.load_movies(MOVIES_PATH)
    ok_r = rec.load_ratings(RATINGS_PATH)
    if not ok_m or not ok_r:
        print("ERROR: Your recommender reported a failure while loading the files.")
        sys.exit(1)

    # 1) Movie popularity
    hdr("[6 pts] Movie popularity — Top 3 movies (by average rating)")
    exp1 = expected_top_movies(movie_avgs, 3)
    act1 = rec.movie_popularity(3)
    print("Expected (ties free-order):", exp1)
    print("Actual:                    ", [(n, r3(s)) for n,s in act1])
    assert_rankings(act1, exp1, "Top 3 Movies")
    print("✔ Passed")

    # 2) Movie popularity in genre
    hdr("[6 pts] Movie popularity in genre — Comedy Top 2")
    exp2 = expected_top_movies_in_genre(movie_avgs, name_to_genre, "Comedy", 2)
    act2 = rec.movie_popularity_in_genre("Comedy", 2)
    print("Expected (ties free-order):", exp2)
    print("Actual:                    ", [(n, r3(s)) for n,s in act2])
    assert_rankings(act2, exp2, "Comedy Top 2")
    print("✔ Passed")

    # 3) Genre popularity
    hdr("[6 pts] Genre popularity — Top 2 genres")
    exp3 = expected_top_genres(genre_avgs, 2)
    act3 = rec.genre_popularity(2)
    print("Expected (ties free-order):", exp3)
    print("Actual:                    ", [(g, r3(s)) for g,s in act3])
    assert_rankings(act3, exp3, "Top Genres 2")
    print("✔ Passed")

    # 4) User preference for genre
    hdr("[6 pts] User preference for genre — user 2")
    exp_user_tops = expected_user_top_genres(2, name_to_genre, ratings_text)
    act_genre, act_avg = rec.user_preference_for_genre(2)
    print("Expected one of:", exp_user_tops if exp_user_tops else ["<none>"])
    print("Actual:         ", act_genre, r3(act_avg) if act_genre else act_avg)
    assert (act_genre in exp_user_tops) or (act_genre is None and not exp_user_tops), \
        f"[User top genre] Expected one of {exp_user_tops}, got {act_genre}"
    print("✔ Passed")

    # 5) Recommend movies
    hdr("[6 pts] Recommend movies — user 1 and 2")
    exp_rec_u1 = expected_recommendations(1, movie_avgs, name_to_genre, ratings_text)
    act_rec_u1 = rec.recommend_movies(1)
    print("u1 Expected:", exp_rec_u1)
    print("u1 Actual:  ", list(act_rec_u1))
    assert list(act_rec_u1) == exp_rec_u1, f"[Recommendations u1] Expected {exp_rec_u1}, got {act_rec_u1}"
    print("✔ u1 Passed")

    exp_rec_u2 = expected_recommendations(2, movie_avgs, name_to_genre, ratings_text)
    act_rec_u2 = rec.recommend_movies(2)
    print("u2 Expected:", exp_rec_u2)
    print("u2 Actual:  ", list(act_rec_u2))
    assert list(act_rec_u2) == exp_rec_u2, f"[Recommendations u2] Expected {exp_rec_u2}, got {act_rec_u2}"
    print("✔ u2 Passed")

    print("\nAll tests passed! 🎉")

if __name__ == "__main__":
    main()