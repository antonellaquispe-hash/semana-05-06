from django.urls import path

from . import views

app_name = "movies"

urlpatterns = [
    path("", views.recommended_movies, name="recommendations"),
    path("<int:pk>/", views.movie_detail, name="movie_detail"),
]
