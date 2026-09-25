from django.contrib import admin

from .models import Genre, Movie, Person, Rating


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_year", "director", "created_at")
    list_filter = ("genres", "release_year")
    search_fields = ("title", "description")
    search_help_text = "Type a title or any word from the description to search."
    # `director` is rendered on every row, so fetch it together with the movie
    # instead of issuing one extra query per row.
    list_select_related = ("director",)
    date_hierarchy = "created_at"
    ordering = ("-release_year", "title")
    list_per_page = 50
    # Skip the exact COUNT query when a full-dataset search is not filtered.
    show_full_result_count = False
    filter_horizontal = ("genres",)
    autocomplete_fields = ("director",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    search_help_text = "Type a genre name or any word from its description."
    ordering = ("name",)
    list_per_page = 50


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date", "created_at")
    search_fields = ("name", "biography")
    search_help_text = "Type a person name or any word from the biography."
    ordering = ("name",)
    list_per_page = 50


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("movie", "score", "comment", "created_at")
    list_filter = ("score",)
    # A bare `movie` is not a valid lookup here: Django would build
    # `movie__icontains`, which a ForeignKey does not support. Traverse to the
    # related field instead, so searching matches the movie title.
    search_fields = ("movie__title", "comment")
    search_help_text = "Type a movie title or any word from a comment."
    list_select_related = ("movie",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50
    show_full_result_count = False
    autocomplete_fields = ("movie",)
