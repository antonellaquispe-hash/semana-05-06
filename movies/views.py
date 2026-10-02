from collections import defaultdict

from django.db.models import Avg, Count, F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Movie, Genre, Rating
from .forms import MovieSearchForm, RatingSubmitForm

# How many movies are recommended per genre.
RECOMMENDATIONS_PER_GENRE = 5


def with_rating_stats(queryset):
    """Annotate a movie queryset with the values the card template needs.

    `average_score` and `ratings_count` are what `templates/movies/
    _movie_card.html` reads to render the rating badge and the score bar.
    Computing them in a single pair of aggregates keeps that fragment
    usable from any view without one of them having to assign the values
    by hand, and without an extra query per movie.
    """
    return queryset.annotate(
        average_score=Avg("ratings__score"),
        ratings_count=Count("ratings"),
    )


def recommended_movies(request):
    """Public page listing the best rated movies within each genre.

    Movies are grouped by genre and, inside each genre, sorted by their average
    rating (highest first). Movies without any rating are kept but ranked last,
    so an unrated title never hides a rated one.
    """
    query = with_rating_stats(Movie.objects).select_related("director").prefetch_related(
        "genres"
    )

    search_form = MovieSearchForm(request.GET)
    if search_form.is_valid():
        q = search_form.cleaned_data.get("query")
        genre = search_form.cleaned_data.get("genre")
        min_score = search_form.cleaned_data.get("min_score")
        if q:
            query = query.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if genre is not None:
            query = query.filter(genres=genre)
        if min_score is not None:
            query = query.filter(ratings__score__gte=min_score).distinct()

    movies = list(query.order_by(F("average_score").desc(nulls_last=True), "title"))

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
            "search_form": search_form,
        },
    )


def movie_detail(request, pk):
    """Detail page for a single movie with its ratings and a rating form."""
    movie = get_object_or_404(
        with_rating_stats(Movie.objects).select_related("director").prefetch_related(
            "genres", "ratings"
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = RatingSubmitForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.movie = movie
            rating.save()
            messages.success(request, "¡Tu valoración se ha registrado!")
            return redirect("movies:movie_detail", pk=movie.pk)
    else:
        form = RatingSubmitForm()

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "rating_form": form,
            "average_score": movie.average_score,
        },
    )