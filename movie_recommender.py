"""
Movie Recommendation System
A command-line application for movie recommendations based on ratings and genres.
Compatible with Python 3.12+
"""

from typing import List, Tuple
from collections import defaultdict


class MovieRecommender:
    """Main class for the Movie Recommendation System."""

    def __init__(self):
        """Initialize the MovieRecommender with empty data structures."""
        # movie_id -> (movie_name (display), genre (as given))
        self.movies = {}
        # canonical movie name -> movie_id  (canonical = casefolded)
        self.movie_name_to_id = {}
        # canonical movie name -> original display movie_name
        self.name_display = {}
        # canonical genre -> original display genre (first seen)
        self.genre_display = {}
        # ratings stored under DISPLAY movie_name: movie_name(display) -> [(rating, user_id)]
        self.ratings = defaultdict(list)
        # user_id -> [(movie_name(display), rating)]
        self.user_ratings = defaultdict(list)
        self.movies_loaded = False
        self.ratings_loaded = False

    # ---------- helpers ----------

    def _canon(self, s: str) -> str:
        """Canonicalize for matching (case-insensitive, whitespace-trim)."""
        return s.strip().casefold() if isinstance(s, str) else s

    def _display_name(self, movie_name_raw: str) -> str:
        """Return the display/canonical movie name we should use for storage/output."""
        c = self._canon(movie_name_raw)
        return self.name_display.get(c, movie_name_raw.strip())

    def _display_genre(self, genre_raw: str) -> str:
        """Return a nice display version for a genre (fallback to input)."""
        cg = self._canon(genre_raw)
        return self.genre_display.get(cg, genre_raw.strip())

    # ---------- loaders ----------

    def load_movies(self, filename: str) -> bool:
        """Load movies from a file: genre|movie_id|movie_name"""
        try:
            loaded_count = 0
            skipped_count = 0
            with open(filename, "r", encoding="utf-8") as file:
                for line in file:
                    if not line.strip():
                        continue
                    parts = line.strip().split("|")
                    if len(parts) != 3:
                        skipped_count += 1
                        continue
                    try:
                        genre = parts[0].strip()
                        movie_id = int(parts[1].strip())
                        movie_name = parts[2].strip()
                    except ValueError:
                        skipped_count += 1
                        continue

                    # store original display name in movies
                    self.movies[movie_id] = (movie_name, genre)

                    # map canonical -> id and canonical -> display name
                    c = self._canon(movie_name)
                    self.movie_name_to_id[c] = movie_id
                    self.name_display[c] = movie_name

                    # remember a display form for this genre (first seen)
                    gc = self._canon(genre)
                    if gc and gc not in self.genre_display:
                        self.genre_display[gc] = genre

                    loaded_count += 1

            if loaded_count == 0:
                print("Warning: No valid movie entries found in the file.")
            if skipped_count > 0:
                print(f"Skipped {skipped_count} malformed movie line(s).")

            self.movies_loaded = True
            print(f"Successfully loaded {len(self.movies)} movies.")
            return True
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return False
        except Exception:
            print("Error loading movies file.")
            return False

    def load_ratings(self, filename: str) -> bool:
        """
        Load ratings from a file.

        File format: movie_name|rating|user_id
        - Keeps ALL valid ratings (including duplicates) so averages include them.
        - Detects and reports duplicate (movie_name, user_id) pairs (case-insensitive match).
        - Skips malformed lines (wrong columns or non-numeric rating/user_id).
        - Prints a summary with: #movies covered, #ratings loaded, #duplicates detected, #malformed lines.
        """
        try:
            loaded_count = 0          # valid ratings stored (duplicates included)
            skipped_count = 0         # malformed lines
            duplicate_count = 0       # (movie_name, user_id) seen AFTER first time
            seen_pairs = set()        # tracks (canon_movie, user_id) we've seen at least once

            with open(filename, "r", encoding="utf-8") as file:
                for raw in file:
                    line = raw.strip()
                    if not line:
                        continue

                    parts = line.split("|")
                    if len(parts) != 3:
                        skipped_count += 1
                        continue

                    movie_name_raw = parts[0].strip()
                    try:
                        rating = float(parts[1].strip())
                        user_id = int(parts[2].strip())
                    except ValueError:
                        skipped_count += 1
                        continue

                    # canonical key for matching/duplicate tracking
                    c = self._canon(movie_name_raw)
                    key = (c, user_id)
                    if key in seen_pairs:
                        duplicate_count += 1
                    else:
                        seen_pairs.add(key)

                    # store ratings under the DISPLAY name (from movies, if known)
                    display = self._display_name(movie_name_raw)
                    self.ratings[display].append((rating, user_id))
                    self.user_ratings[user_id].append((display, rating))
                    loaded_count += 1

            if loaded_count == 0:
                print("Warning: No valid rating entries found in the file.")

            msg = (
                f"Successfully loaded ratings for {len(self.ratings)} movies. "
                f"({loaded_count} rating(s) loaded"
            )
            if duplicate_count > 0:
                msg += f"; {duplicate_count} duplicate rating(s) detected"
            msg += ")"
            print(msg)

            if skipped_count > 0:
                print(f"Skipped {skipped_count} malformed rating line(s).")

            self.ratings_loaded = True
            return True

        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return False
        except Exception:
            print("Error loading ratings file.")
            return False

    # ---------- computations ----------

    def calculate_average_rating(self, movie_name: str) -> float:
        """
        Calculate the average rating for a movie by display name or any cased variant.
        """
        if not movie_name:
            return 0.0
        # normalize to display key if known
        display = self._display_name(movie_name)
        if display not in self.ratings or not self.ratings[display]:
            return 0.0
        ratings_list = [r for (r, _u) in self.ratings[display]]
        return sum(ratings_list) / len(ratings_list)

    def movie_popularity(self, n: int) -> List[Tuple[str, float]]:
        """
        Top n movies by average rating (desc), breaking ties by movie name asc.
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []

        movie_avg_ratings = []
        # iterate over what has ratings (keys are display names)
        for display_name in self.ratings.keys():
            avg_rating = self.calculate_average_rating(display_name)
            movie_avg_ratings.append((display_name, avg_rating))

        movie_avg_ratings.sort(key=lambda x: (-x[1], x[0]))
        return movie_avg_ratings[:n]

    def movie_popularity_in_genre(self, genre: str, n: int) -> List[Tuple[str, float]]:
        """
        Top n movies in a genre by average rating (desc), ties by name asc.
        Case-insensitive genre matching.
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []

        genre_canon = self._canon(genre)
        genre_movies = []
        for movie_id, (movie_name_display, movie_genre) in self.movies.items():
            if self._canon(movie_genre) != genre_canon:
                continue
            # only include if we actually have ratings for it (by display name)
            if movie_name_display in self.ratings:
                avg_rating = self.calculate_average_rating(movie_name_display)
                genre_movies.append((movie_name_display, avg_rating))

        genre_movies.sort(key=lambda x: (-x[1], x[0]))
        return genre_movies[:n]

    def genre_popularity(self, n: int) -> List[Tuple[str, float]]:
        """
        Top n genres ranked by the average of average ratings of movies in the genre.
        Case-insensitive grouping with pretty display names.
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []

        genre_ratings = defaultdict(list)

        # For each movie that has ratings, group its average by canonical genre
        for movie_id, (movie_name_display, genre) in self.movies.items():
            if movie_name_display in self.ratings:
                avg_rating = self.calculate_average_rating(movie_name_display)
                cgenre = self._canon(genre)
                genre_ratings[cgenre].append(avg_rating)

        # Compute average of averages per canonical genre; display with nice casing
        genre_averages = []
        for cgenre, ratings in genre_ratings.items():
            if ratings:
                avg_of_avg = sum(ratings) / len(ratings)
                display = self.genre_display.get(cgenre, cgenre)
                genre_averages.append((display, avg_of_avg))

        # Sort by descending average rating, then alphabetically
        genre_averages.sort(key=lambda x: (-x[1], x[0]))
        return genre_averages[:n]

    def user_preference_for_genre(self, user_id: int) -> Tuple[str, float]:
        """Return the user's most preferred genre based on their average ratings.
        Case-insensitive aggregation with pretty display name.
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return (None, 0.0)

        from collections import defaultdict
        genre_ratings = defaultdict(list)

        # Collect this user's ratings by canonical genre
        for movie_name, rating in self.user_ratings.get(user_id, []):
            c = self._canon(movie_name)
            movie_id = self.movie_name_to_id.get(c)
            if movie_id and movie_id in self.movies:
                raw_genre = self.movies[movie_id][1]
                cgenre = self._canon(raw_genre)
                genre_ratings[cgenre].append(rating)

        if not genre_ratings:
            return (None, 0.0)

        # Compute average rating per canonical genre
        genre_averages = {
            cgenre: sum(ratings) / len(ratings)
            for cgenre, ratings in genre_ratings.items()
        }

        # Helper to get a pretty display string
        def disp(cg: str) -> str:
            return self.genre_display.get(cg, cg)

        # Select the top-rated genre (tie-break by display string alphabetically)
        top_cgenre, top_avg = max(
            genre_averages.items(),
            key=lambda x: (x[1], disp(x[0]))
        )

        return (disp(top_cgenre), top_avg)

    def recommend_movies(self, user_id: int) -> List[str]:
        """
        Recommend 3 most popular movies from user's top genre that they haven't rated.
        Genre comparisons are case-insensitive.
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []

        top_genre, _ = self.user_preference_for_genre(user_id)
        if not top_genre:
            return []

        # Movies already rated by the user (display names)
        rated_by_user = set(m for m, _ in self.user_ratings.get(user_id, []))

        # Compare by canonical genre
        target_cg = self._canon(top_genre)

        # Candidates in the genre, rated by someone, and unseen by this user
        candidates: List[Tuple[str, float]] = []
        for movie_id, (movie_name_display, genre) in self.movies.items():
            if self._canon(genre) != target_cg:
                continue
            if movie_name_display in rated_by_user:
                continue
            if movie_name_display not in self.ratings or not self.ratings[movie_name_display]:
                continue
            avg_rating = self.calculate_average_rating(movie_name_display)
            candidates.append((movie_name_display, avg_rating))

        if not candidates:
            return []

        candidates.sort(key=lambda x: (-x[1], x[0]))
        return [name for name, _ in candidates[:3]]


# ---------------- CLI below (unchanged except nicer genre display) ----------------

def print_menu():
    """Print the main menu."""
    print("\n" + "="*60)
    print("MOVIE RECOMMENDATION SYSTEM")
    print("="*60)
    print("1. Load Movies File")
    print("2. Load Ratings File")
    print("3. Movie Popularity (Top N Movies)")
    print("4. Movie Popularity in Genre (Top N in Genre)")
    print("5. Genre Popularity (Top N Genres)")
    print("6. User Preference for Genre")
    print("7. Recommend Movies for User")
    print("8. Exit")
    print("="*60)


def main():
    """Main function to run the CLI."""
    recommender = MovieRecommender()

    while True:
        print_menu()
        choice = input("Enter your choice (1-8): ").strip()

        if choice == '1':
            filename = input("Enter movies filename: ").strip()
            recommender.load_movies(filename)

        elif choice == '2':
            filename = input("Enter ratings filename: ").strip()
            recommender.load_ratings(filename)

        elif choice == '3':
            if not recommender.movies_loaded or not recommender.ratings_loaded:
                print("Please load both movies and ratings files first.")
                continue
            try:
                n = int(input("Enter number of top movies to display: ").strip())
                results = recommender.movie_popularity(n)
                print(f"\nTop {n} Most Popular Movies:")
                print("-" * 60)
                for i, (movie_name, avg_rating) in enumerate(results, 1):
                    print(f"{i}. {movie_name} - Average Rating: {avg_rating:.2f}")
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == '4':
            if not recommender.movies_loaded or not recommender.ratings_loaded:
                print("Please load both movies and ratings files first.")
                continue
            genre_input = input("Enter genre: ").strip()
            try:
                n = int(input("Enter number of top movies to display: ").strip())
                results = recommender.movie_popularity_in_genre(genre_input, n)
                if results:
                    # Pretty display of the genre name
                    genre_canon = recommender._canon(genre_input)
                    nice_genre = recommender.genre_display.get(genre_canon, genre_input)
                    print(f"\nTop {n} Most Popular Movies in '{nice_genre}':")
                    print("-" * 60)
                    for i, (movie_name, avg_rating) in enumerate(results, 1):
                        print(f"{i}. {movie_name} - Average Rating: {avg_rating:.2f}")
                else:
                    print(f"No movies found in genre '{genre_input}' or no ratings available.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == '5':
            if not recommender.movies_loaded or not recommender.ratings_loaded:
                print("Please load both movies and ratings files first.")
                continue
            try:
                n = int(input("Enter number of top genres to display: ").strip())
                results = recommender.genre_popularity(n)
                print(f"\nTop {n} Most Popular Genres:")
                print("-" * 60)
                for i, (genre, avg_rating) in enumerate(results, 1):
                    print(f"{i}. {genre} - Average Rating: {avg_rating:.2f}")
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == '6':
            if not recommender.movies_loaded or not recommender.ratings_loaded:
                print("Please load both movies and ratings files first.")
                continue
            try:
                user_id = int(input("Enter user ID: ").strip())
                genre, avg_rating = recommender.user_preference_for_genre(user_id)
                if genre:
                    print(f"\nUser {user_id}'s Preferred Genre:")
                    print("-" * 60)
                    print(f"{genre} - Average Rating: {avg_rating:.2f}")
                else:
                    print(f"No preference found for user {user_id}.")
            except ValueError:
                print("Invalid input. Please enter a valid user ID.")

        elif choice == '7':
            if not recommender.movies_loaded or not recommender.ratings_loaded:
                print("Please load both movies and ratings files first.")
                continue
            try:
                user_id = int(input("Enter user ID: ").strip())
                recommendations = recommender.recommend_movies(user_id)
                if recommendations:
                    print(f"\nRecommended Movies for User {user_id}:")
                    print("-" * 60)
                    for i, movie_name in enumerate(recommendations, 1):
                        print(f"{i}. {movie_name}")
                else:
                    print(f"No recommendations available for user {user_id}.")
            except ValueError:
                print("Invalid input. Please enter a valid user ID.")

        elif choice == '8':
            print("\nThank you for using the Movie Recommendation System!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 8.")


if __name__ == "__main__":
    main()
