from django.urls import path

from . import views

app_name = "movies"

urlpatterns = [
    path("", views.recommended_movies, name="recommendations"),
    path("<int:pk>/", views.movie_detail, name="movie_detail"),
    # The `genre/` prefix is required: a bare `<int:genre_pk>/` would be
    # indistinguishable from `<int:pk>/` above and Django would send every
    # `/movies/<n>/` URL to whichever route was declared first.
    path("genre/<int:genre_pk>/", views.genre_detail, name="genre_detail"),
]
