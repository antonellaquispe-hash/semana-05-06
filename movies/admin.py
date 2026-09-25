from django.contrib import admin

from .models import Genre, Movie, Person, Rating


class AuditedModelAdmin(admin.ModelAdmin):
    """Base admin exposing the audit timestamps as visible but read-only.

    `created_at` and `updated_at` use `auto_now_add` / `auto_now`, so Django
    already refuses to accept them as form input. Listing them in
    `readonly_fields` is what makes them show up on the change form at all.
    """

    readonly_fields = ("created_at", "updated_at")


class RatingInline(admin.TabularInline):
    """Edit a movie's ratings from the movie change form."""

    model = Rating
    fields = ("score", "comment", "created_at")
    # `created_at` is auto-generated, so it can only ever be displayed.
    readonly_fields = ("created_at",)
    extra = 2


@admin.register(Movie)
class MovieAdmin(AuditedModelAdmin):
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
    inlines = (RatingInline,)


@admin.register(Genre)
class GenreAdmin(AuditedModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    search_help_text = "Type a genre name or any word from its description."
    ordering = ("name",)
    list_per_page = 50


@admin.register(Person)
class PersonAdmin(AuditedModelAdmin):
    list_display = ("name", "birth_date", "created_at")
    search_fields = ("name", "biography")
    search_help_text = "Type a person name or any word from the biography."
    ordering = ("name",)
    list_per_page = 50


@admin.register(Rating)
class RatingAdmin(AuditedModelAdmin):
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
