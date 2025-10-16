#!/usr/bin/env python3
"""
test_movie_recommender.py — uses local files:
  - MOVIES_PATH
  - RATINGS_PATH

Main tests use your provided files.
Edge cases are DERIVED FROM your provided movies/ratings files (no hardcoded titles).
"""
import importlib, sys, io, contextlib

# ------------------------ Config: fixed filenames ------------------------
MOVIES_PATH  = "movie_file_8.txt"
RATINGS_PATH = "rating_file_8.txt"

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
        raise AssertionError(
            f"[{label}] Expected {len(exp)} items, got {len(act_flat)}.\n"
            f"Expected: {exp}\nActual:   {act}"
        )
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

def subhdr(title):
    print("\n" + "-"*80); print(title); print("-"*80)

@contextlib.contextmanager
def quiet_stdout():
    """Silence noisy loader prints inside edge-case setup."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield

# ------------------------ Expected results (computed from files) ------------------------
def parse_movies_map(text):
    """
    Returns:
      name_to_genre: {display_name -> genre}
      canon_to_display: {name.casefold() -> display_name}
      valid_movie_rows: list of raw valid movie rows (genre|id|name)
    """
    name_to_genre = {}
    canon_to_display = {}
    valid_movie_rows = []
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) != 3:
            continue
        g, _id, name = parts[0].strip(), parts[1].strip(), parts[2].strip()
        # Ensure id is int-ish
        try:
            int(_id)
        except:
            continue
        name_to_genre[name] = g
        canon_to_display[name.casefold()] = name
        valid_movie_rows.append((g, _id, name))
    return name_to_genre, canon_to_display, valid_movie_rows

def movie_avgs_from(text, canon_to_display):
    """Build {display_name -> avg_rating} using movies' display names for case-robustness."""
    from collections import defaultdict
    sums, cnts = defaultdict(float), defaultdict(int)
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        raw_name, r, _u = parts[0].strip(), parts[1].strip(), parts[2].strip()
        try:
            r = float(r)
        except:
            continue
        name = canon_to_display.get(raw_name.casefold(), raw_name)
        sums[name] += r; cnts[name] += 1
    return {name: (sums[name] / cnts[name]) for name in sums}

def genre_aoa_from(movie_avgs, name_to_genre):
    from collections import defaultdict
    sums, cnts = defaultdict(float), defaultdict(int)
    for name, avg in movie_avgs.items():
        g = name_to_genre.get(name)
        if g is None:
            continue
        sums[g] += avg; cnts[g] += 1
    return {g: (sums[g] / cnts[g]) for g in sums}

def expected_top_movies(movie_avgs, n):
    items = sorted(movie_avgs.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:n]

def expected_top_movies_in_genre(movie_avgs, name_to_genre, genre, n):
    items = [(name, movie_avgs[name]) for name, g in name_to_genre.items()
             if g == genre and name in movie_avgs]
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return items[:n]

def expected_top_genres(genre_avgs, n):
    items = sorted(genre_avgs.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:n]

def expected_user_top_genres(user_id, name_to_genre, ratings_text, canon_to_display):
    """Return a list of genre names that tie for the user's top average (case-robust)."""
    from collections import defaultdict
    sums, cnts = defaultdict(float), defaultdict(int)
    for raw in ratings_text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        raw_name, r, uid = parts[0].strip(), parts[1].strip(), parts[2].strip()
        try:
            if int(uid) != int(user_id):
                continue
            r = float(r)
        except:
            continue
        name = canon_to_display.get(raw_name.casefold(), raw_name)
        g = name_to_genre.get(name)
        if g is None:
            continue
        sums[g] += r; cnts[g] += 1
    if not cnts:
        return []
    avgs = {g: (sums[g] / cnts[g]) for g in cnts}
    best = max(avgs.values())
    return sorted([g for g, v in avgs.items() if abs(v - best) < 1e-12])

# Updated tie-break rule (alphabetical, matching your implementation)
def expected_recommendations(user_id, movie_avgs, name_to_genre, ratings_text, canon_to_display):
    tops = expected_user_top_genres(user_id, name_to_genre, ratings_text, canon_to_display)
    if not tops:
        return []
    # Tie-break to match implementation: pick alphabetically highest genre among ties
    top = max(tops)

    # Movies the user has already rated (normalize names to display)
    seen = set()
    for raw in ratings_text.strip().splitlines():
        parts = raw.strip().split("|")
        if len(parts) != 3:
            continue
        raw_name, _r, uid = parts[0].strip(), parts[1].strip(), parts[2].strip()
        try:
            if int(uid) == int(user_id):
                name = canon_to_display.get(raw_name.casefold(), raw_name)
                seen.add(name)
        except:
            pass

    # Candidates in user's top genre that the user hasn't rated
    candidates = [(n, movie_avgs[n]) for n, g in name_to_genre.items()
                  if g == top and n in movie_avgs and n not in seen]
    candidates.sort(key=lambda kv: (-kv[1], kv[0]))
    return [n for n, _ in candidates[:3]]

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

    # Build maps (case-robust expected calculations)
    name_to_genre, canon_to_display, valid_movie_rows = parse_movies_map(movies_text)
    movie_avgs = movie_avgs_from(ratings_text, canon_to_display)
    genre_avgs = genre_aoa_from(movie_avgs, name_to_genre)

    # Fallbacks for sampling
    if not valid_movie_rows:
        print("ERROR: No valid movie rows found in your movies file.")
        sys.exit(1)

    # Choose sample movies from your provided file for EC-2..EC-4
    sample_movie_1 = valid_movie_rows[0]  # (genre, id, name)
    sample_movie_2 = valid_movie_rows[1] if len(valid_movie_rows) > 1 else valid_movie_rows[0]

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
    print("Actual:                    ", [(n, r3(s)) for n, s in act1])
    assert_rankings(act1, exp1, "Top 3 Movies")
    print("✔ Passed")

    # 2) Movie popularity in genre
    hdr("[6 pts] Movie popularity in genre — Comedy Top 2")
    exp2 = expected_top_movies_in_genre(movie_avgs, name_to_genre, "Comedy", 2)
    act2 = rec.movie_popularity_in_genre("Comedy", 2)
    print("Expected (ties free-order):", exp2)
    print("Actual:                    ", [(n, r3(s)) for n, s in act2])
    assert_rankings(act2, exp2, "Comedy Top 2")
    print("✔ Passed")

    # 3) Genre popularity
    hdr("[6 pts] Genre popularity — Top 2 genres")
    exp3 = expected_top_genres(genre_avgs, 2)
    act3 = rec.genre_popularity(2)
    print("Expected (ties free-order):", exp3)
    print("Actual:                    ", [(g, r3(s)) for g, s in act3])
    assert_rankings(act3, exp3, "Top Genres 2")
    print("✔ Passed")

    # 4) User preference for genre
    hdr("[6 pts] User preference for genre — user 2")
    exp_user_tops = expected_user_top_genres(2, name_to_genre, ratings_text, canon_to_display)
    act_genre, act_avg = rec.user_preference_for_genre(2)
    print("Expected one of:", exp_user_tops if exp_user_tops else ["<none>"])
    print("Actual:         ", act_genre, r3(act_avg) if act_genre else act_avg)
    assert (act_genre in exp_user_tops) or (act_genre is None and not exp_user_tops), \
        f"[User top genre] Expected one of {exp_user_tops}, got {act_genre}"
    print("✔ Passed")

    # 5) Recommend movies
    hdr("[6 pts] Recommend movies — user 1 and 2")
    exp_rec_u1 = expected_recommendations(1, movie_avgs, name_to_genre, ratings_text, canon_to_display)
    act_rec_u1 = rec.recommend_movies(1)
    print("u1 Expected:", exp_rec_u1)
    print("u1 Actual:  ", list(act_rec_u1))
    assert list(act_rec_u1) == exp_rec_u1, f"[Recommendations u1] Expected {exp_rec_u1}, got {act_rec_u1}"
    print("✔ u1 Passed")

    exp_rec_u2 = expected_recommendations(2, movie_avgs, name_to_genre, ratings_text, canon_to_display)
    act_rec_u2 = rec.recommend_movies(2)
    print("u2 Expected:", exp_rec_u2)
    print("u2 Actual:  ", list(act_rec_u2))
    assert list(act_rec_u2) == exp_rec_u2, f"[Recommendations u2] Expected {exp_rec_u2}, got {act_rec_u2}"
    print("✔ u2 Passed")

    # 6) Edge-case & Negative Tests — concise verdicts (derived from your files)
    hdr("[5 pts] Edge-case & Negative Tests — concise verdicts (derived)")

    import tempfile, os, shutil

    tmpdir = tempfile.mkdtemp()
    try:
        # EC-1: Empty files (still synthetic but independent of your data)
        subhdr("EC-1: Empty files")
        empty_movies = os.path.join(tmpdir, "empty_movies.txt")
        empty_ratings = os.path.join(tmpdir, "empty_ratings.txt")
        open(empty_movies, "w").close()
        open(empty_ratings, "w").close()

        with quiet_stdout():
            rec2 = Reco()
            ok_m2 = rec2.load_movies(empty_movies)
            ok_r2 = rec2.load_ratings(empty_ratings)

        if not ok_m2 or not ok_r2:
            print("Result: loaders indicated empty input -> PASS")
        else:
            pop = rec2.movie_popularity(3)
            pop_comedy = rec2.movie_popularity_in_genre("Comedy", 2)
            genres = rec2.genre_popularity(2)
            pref = rec2.user_preference_for_genre(1)
            recs = rec2.recommend_movies(1)
            assert pop == [] and pop_comedy == [] and genres == [] and pref == (None, 0.0) and recs == []
            print("Result: empty inputs handled with empty outputs -> PASS")

        # EC-2: Malformed movie lines (mix bad + a valid row from your MOVIES_PATH)
        subhdr("EC-2: Malformed movie lines")
        # Build a small movies file using one valid row sampled from your file
        g1, id1, name1 = sample_movie_1
        bad_movies = os.path.join(tmpdir, "bad_movies.txt")
        with open(bad_movies, "w", encoding="utf-8") as f:
            f.write("BrokenLineWithoutPipes\n")          # malformed
            f.write(f"{g1}|{id1}|{name1}\n")            # valid (from your file)
            f.write("Action|abc|BadID\n")               # malformed numeric id
            f.write("Horror|2|Valid Two|EXTRA\n")       # extra field -> malformed
            f.write("\n")                               # blank

        with quiet_stdout():
            rec3 = Reco()
            rec3.load_movies(bad_movies)

        # We expect the sampled valid movie to be present
        handled = any(name1 == t[0] for t in rec3.movies.values())
        assert handled
        print("Result: malformed movie rows skipped; valid retained -> PASS")

        # EC-3: Malformed ratings & duplicates (use a real movie title from your file)
        subhdr("EC-3: Malformed ratings & duplicates")
        # Use the sampled movie name from your MOVIES_PATH
        title = name1  # e.g., "Some Movie (Year)"

        bad_ratings = os.path.join(tmpdir, "bad_ratings.txt")
        with open(bad_ratings, "w", encoding="utf-8") as f:
            f.write(f"{title}|notanumber|5\n")  # non-numeric rating -> skip
            f.write(f"{title}|4.0\n")           # missing user id -> skip
            f.write(f"{title}|4.0|5\n")         # first rating for (movie,user)
            f.write(f"{title}|4.5|5\n")         # duplicate for (movie,user)

        # Load YOUR full movies file to stay faithful to your request
        with quiet_stdout():
            rec4 = Reco()
            rec4.load_movies(MOVIES_PATH)
            rec4.load_ratings(bad_ratings)

        # Verify we stored exactly two rating lines overall for this tiny set
        total_stored = sum(len(v) for v in rec4.ratings.values())
        assert total_stored == 2, f"Expected 2 stored ratings, found {total_stored}"

        # Verify popularity math via public API
        top = rec4.movie_popularity(1)
        assert top and top[0][0].casefold() == title.casefold(), f"Top movie should be {title}"
        assert abs(top[0][1] - 4.25) < 1e-9, f"Expected avg 4.25, got {top[0][1]}"
        print("Result: malformed skipped; duplicate kept & averaged (avg=4.25) -> PASS")

        # EC-4: Tie behavior — pick two real titles from your file and force a tie
        subhdr("EC-4: Tie behavior")
        gA, idA, nameA = sample_movie_1
        gB, idB, nameB = sample_movie_2
        # Build a tiny movies file preserving their genres
        tie_movies = os.path.join(tmpdir, "tie_movies.txt")
        with open(tie_movies, "w", encoding="utf-8") as f:
            f.write(f"{gA}|1|{nameA}\n")
            f.write(f"{gB}|2|{nameB}\n")
        # Ratings force an average tie at 4.0
        tie_ratings = os.path.join(tmpdir, "tie_ratings.txt")
        with open(tie_ratings, "w", encoding="utf-8") as f:
            f.write(f"{nameA}|4.0|1\n")
            f.write(f"{nameB}|4.0|2\n")

        with quiet_stdout():
            rec5 = Reco()
            rec5.load_movies(tie_movies)
            rec5.load_ratings(tie_ratings)

        top2 = rec5.movie_popularity(2)
        assert abs(top2[0][1] - top2[1][1]) < 1e-9  # identical scores
        assert [n for n, _ in top2] == sorted([n for n, _ in top2])  # alphabetical tiebreak
        print("Result: equal averages with alphabetical tiebreak -> PASS")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\nAll edge-case and negative tests passed! ✅")
    print("\nAll tests passed! 🎉")

if __name__ == "__main__":
    main()
