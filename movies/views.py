from collections import defaultdict

from django.db.models import Avg, Count, F
from django.shortcuts import render

from .models import Movie

# How many movies are recommended per genre.
RECOMMENDATIONS_PER_GENRE = 5


def recommended_movies(request):
    """Public page listing the best rated movies within each genre.

    Movies are grouped by genre and, inside each genre, sorted by their average
    rating (highest first). Movies without any rating are kept but ranked last,
    so an unrated title never hides a rated one.
    """
    movies = list(
        Movie.objects.annotate(
            average_score=Avg("ratings__score"),
            ratings_count=Count("ratings"),
        )
        # The template renders the director for every movie, and `genres` is
        # walked for every movie too, so fetch both up front.
        .select_related("director")
        .prefetch_related("genres")
        .order_by(F("average_score").desc(nulls_last=True), "title")
    )

    # Build the genre -> movies mapping in a single pass, so the page costs a
    # fixed number of queries instead of one per genre.
    movies_by_genre = defaultdict(list)
    for movie in movies:
        for genre in movie.genres.all():
            movies_by_genre[genre].append(movie)

    recommendations = [
        {
            "genre": genre,
            "movies": movies_by_genre[genre][:RECOMMENDATIONS_PER_GENRE],
        }
        for genre in sorted(movies_by_genre, key=lambda item: item.name)
    ]

    return render(
        request,
        "movies/recommendations.html",
        {
            "recommendations": recommendations,
            "movie_count": len(movies),
        },
    )
