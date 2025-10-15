"""
Movie Recommendation System
A command-line application for movie recommendations based on ratings and genres.
Compatible with Python 3.12+
"""

from typing import Dict, List, Tuple
from collections import defaultdict


class MovieRecommender:
    """Main class for the Movie Recommendation System."""
    
    def __init__(self):
        """Initialize the MovieRecommender with empty data structures."""
        self.movies = {}  # movie_id -> (movie_name, genre)
        self.movie_name_to_id = {}  # movie_name -> movie_id
        self.ratings = defaultdict(list)  # movie_name -> [(rating, user_id)]
        self.user_ratings = defaultdict(list)  # user_id -> [(movie_name, rating)]
        self.movies_loaded = False
        self.ratings_loaded = False


    def load_movies(self, filename: str) -> bool:
        """Load movies from a file."""
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
                    self.movies[movie_id] = (movie_name, genre)
                    self.movie_name_to_id[movie_name.lower()] = movie_id
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
        - Detects and reports duplicate (movie_name, user_id) pairs.
        - Skips malformed lines (wrong columns or non-numeric rating/user_id).
        - Prints a summary with: #movies covered, #ratings loaded, #duplicates detected, #malformed lines.
        """
        try:
            loaded_count = 0          # number of valid ratings actually stored (duplicates included)
            skipped_count = 0         # malformed lines
            duplicate_count = 0       # times we saw a (movie_name, user_id) AFTER the first time
            seen_pairs = set()        # tracks (movie_name, user_id) we've seen at least once

            with open(filename, "r", encoding="utf-8") as file:
                for raw in file:
                    line = raw.strip()
                    if not line:
                        continue

                    parts = line.split("|")
                    if len(parts) != 3:
                        skipped_count += 1
                        continue

                    movie_name = parts[0].strip().lower()
                    try:
                        rating = float(parts[1].strip())
                        user_id = int(parts[2].strip())
                    except ValueError:
                        skipped_count += 1
                        continue

                    key = (movie_name, user_id)
                    if key in seen_pairs:
                        # Count duplicate but DO NOT skip: we still keep it so averages include it
                        duplicate_count += 1
                    else:
                        seen_pairs.add(key)

                    # Store rating (duplicates included)
                    self.ratings[movie_name].append((rating, user_id))
                    self.user_ratings[user_id].append((movie_name, rating))
                    loaded_count += 1

            if loaded_count == 0:
                print("Warning: No valid rating entries found in the file.")

            # Summary output
            # Note: len(self.ratings) is number of distinct movies that received at least one rating line.
            msg = f"Successfully loaded ratings for {len(self.ratings)} movies. ({loaded_count} rating(s) loaded"
            msg += f"; {duplicate_count} duplicate rating(s) detected" if duplicate_count > 0 else ""
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
    
  
    
    def calculate_average_rating(self, movie_name: str) -> float:
        """
        Calculate the average rating for a movie.
        
        Args:
            movie_name: Name of the movie
            
        Returns:
            Average rating, or 0.0 if no ratings
        """
        movie_name = movie_name.lower()
        if movie_name not in self.ratings or not self.ratings[movie_name]:
            return 0.0
        ratings_list = [r[0] for r in self.ratings[movie_name]]
        return sum(ratings_list) / len(ratings_list)
    
    def movie_popularity(self, n: int) -> List[Tuple[str, float]]:
        """
        Get top n most popular movies based on average ratings.
        
        Args:
            n: Number of top movies to return
            
        Returns:
            List of tuples (movie_name, average_rating) sorted by rating descending
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []
        
        movie_avg_ratings = []
        for movie_name in self.ratings.keys():
            avg_rating = self.calculate_average_rating(movie_name)
            movie_avg_ratings.append((movie_name, avg_rating))
        
        # Sort by average rating (descending), then by movie name (ascending) for ties
        movie_avg_ratings.sort(key=lambda x: (-x[1], x[0]))
        
        return movie_avg_ratings[:n]
    
    def movie_popularity_in_genre(self, genre: str, n: int) -> List[Tuple[str, float]]:
        """
        Get top n most popular movies in a specific genre based on average ratings.
        
        Args:
            genre: Genre to filter by
            n: Number of top movies to return
            
        Returns:
            List of tuples (movie_name, average_rating) sorted by rating descending
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []
        
        # Get all movies in the specified genre
        genre_movies = []
        for movie_id, (movie_name, movie_genre) in self.movies.items():
            if movie_genre == genre and movie_name in self.ratings:
                avg_rating = self.calculate_average_rating(movie_name)
                genre_movies.append((movie_name, avg_rating))
        
        # Sort by average rating (descending), then by movie name (ascending) for ties
        genre_movies.sort(key=lambda x: (-x[1], x[0]))
        
        return genre_movies[:n]
    
    def genre_popularity(self, n: int) -> List[Tuple[str, float]]:
        """
        Get top n most popular genres based on average of average ratings of their movies.

        Args:
            n: Number of top genres to return

        Returns:
            List of tuples (genre, average_rating)
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []

        genre_ratings = defaultdict(list)

        # For each movie that has ratings, group its average by genre
        for movie_id, (movie_name, genre) in self.movies.items():
            if movie_name in self.ratings:
                avg_rating = self.calculate_average_rating(movie_name)
                genre_ratings[genre].append(avg_rating)

        # Compute average of averages per genre
        genre_averages = []
        for genre, ratings in genre_ratings.items():
            if ratings:
                avg_of_avg = sum(ratings) / len(ratings)
                genre_averages.append((genre, avg_of_avg))

        # Sort by descending average rating, then alphabetically
        genre_averages.sort(key=lambda x: (-x[1], x[0]))

        return genre_averages[:n]

    
    def user_preference_for_genre(self, user_id: int) -> Tuple[str, float]:
        """
        Determine which genre the user prefers most based on their average ratings.

        Args:
            user_id: ID of the user

        Returns:
            (genre, average_rating) or (None, 0.0) if user has no ratings
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return (None, 0.0)

        if user_id not in self.user_ratings or not self.user_ratings[user_id]:
            return (None, 0.0)

        genre_ratings = defaultdict(list)

        # For each movie the user rated, record their rating by genre
        for movie_name, rating in self.user_ratings[user_id]:
            movie_id = self.movie_name_to_id.get(movie_name.lower())
            if movie_id and movie_id in self.movies:
                genre = self.movies[movie_id][1]
                genre_ratings[genre].append(rating)

        if not genre_ratings:
            return (None, 0.0)

        # Compute average rating per genre
        genre_avg = {g: sum(r) / len(r) for g, r in genre_ratings.items()}

        # Find top genre by average rating (ties → alphabetical order)
        top_genre = max(genre_avg.items(), key=lambda x: (x[1], x[0]))

        return top_genre

    
    def recommend_movies(self, user_id: int) -> List[str]:
        """
        Recommend 3 most popular movies from user's top genre that they haven't rated.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of up to 3 recommended movie names
        """
        # Ensure data is loaded
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []

        # Determine user's preferred genre
        top_genre, _ = self.user_preference_for_genre(user_id)
        if not top_genre:
            # No ratings or nothing we can infer
            return []

        # Movies the user has already rated
        rated_by_user = set(m for m, _ in self.user_ratings.get(user_id, []))

        # Collect candidate movies: in user's top genre, have at least one rating, and not rated by user
        candidates: List[Tuple[str, float]] = []
        for movie_id, (movie_name, genre) in self.movies.items():
            if genre != top_genre:
               continue
            if movie_name in rated_by_user:
                continue
            if movie_name not in self.ratings or not self.ratings[movie_name]:
                # Skip unrated movies (popularity defined by average rating)
                continue
            avg_rating = self.calculate_average_rating(movie_name)
            candidates.append((movie_name, avg_rating))

        if not candidates:
            return []

        # Sort by average rating (desc), then movie name (asc) for deterministic ties
        candidates.sort(key=lambda x: (-x[1], x[0]))

        # Return only the movie names, top 3
        return [name for name, _ in candidates[:3]]



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
            genre = input("Enter genre: ").strip()
            try:
                n = int(input("Enter number of top movies to display: ").strip())
                results = recommender.movie_popularity_in_genre(genre, n)
                if results:
                    print(f"\nTop {n} Most Popular Movies in '{genre}':")
                    print("-" * 60)
                    for i, (movie_name, avg_rating) in enumerate(results, 1):
                        print(f"{i}. {movie_name} - Average Rating: {avg_rating:.2f}")
                else:
                    print(f"No movies found in genre '{genre}' or no ratings available.")
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