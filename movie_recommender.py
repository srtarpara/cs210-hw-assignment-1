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
                        genre = parts[0]
                        movie_id = int(parts[1])
                        movie_name = parts[2]
                    except ValueError:
                        skipped_count += 1
                        continue
                    self.movies[movie_id] = (movie_name, genre)
                    self.movie_name_to_id[movie_name] = movie_id
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
        
        Args:
            filename: Path to the ratings file
            
        Returns:
            True if successful, False otherwise
            
        File format: movie_name|rating|user_id
        """
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
                        movie_name = parts[0]
                        rating = float(parts[1])
                        user_id = int(parts[2])
                    except ValueError:
                        skipped_count += 1
                        continue
                    self.ratings[movie_name].append((rating, user_id))
                    self.user_ratings[user_id].append((movie_name, rating))
                    loaded_count += 1

            if loaded_count == 0:
                print("Warning: No valid rating entries found in the file.")
            if skipped_count > 0:
                print(f"Skipped {skipped_count} malformed rating line(s).")

            self.ratings_loaded = True
            print(f"Successfully loaded ratings for {len(self.ratings)} movies.")
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
        Get top n most popular genres based on average of average ratings.
        
        Args:
            n: Number of top genres to return
            
        Returns:
            List of tuples (genre, average_of_averages) sorted by rating descending
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []
        
        # TODO: Implement this function
        # Steps:
        # 1. Calculate average rating for each genre
        # 2. Calculate average of averages for each genre
        # 3. Sort by average rating (descending), then by genre name (ascending)
        # 4. Return top n genres
        
        print("Function not yet implemented.")
        return []
    
    def user_preference_for_genre(self, user_id: int) -> Tuple[str, float]:
        """
        Find the genre most preferred by a user based on average ratings.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple of (genre, average_rating) or (None, 0.0) if user has no ratings
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return (None, 0.0)
        
        # TODO: Implement this function
        # Steps:
        # 1. Get all movies rated by the user
        # 2. Group ratings by genre
        # 3. Calculate average rating per genre
        # 4. Return the genre with highest average rating
        
        print("Function not yet implemented.")
        return (None, 0.0)
    
    def recommend_movies(self, user_id: int) -> List[str]:
        """
        Recommend 3 most popular movies from user's top genre that they haven't rated.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of up to 3 recommended movie names
        """
        if not self.movies_loaded or not self.ratings_loaded:
            print("Error: Please load both movies and ratings files first.")
            return []
        
        # TODO: Implement this function
        # Steps:
        # 1. Get user's top genre using user_preference_for_genre()
        # 2. Get all movies in that genre that user hasn't rated
        # 3. Sort by average rating (descending)
        # 4. Return top 3 movies
        
        print("Function not yet implemented.")
        return []


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