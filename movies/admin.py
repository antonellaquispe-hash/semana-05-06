from django.contrib import admin
from django.db.models import Avg

from .forms import (
    GenreForm,
    MovieForm,
    PersonForm,
    RatingForm,
    RatingInlineForm,
)
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
    form = RatingInlineForm
    fields = ("score", "comment", "created_at")
    # `created_at` is auto-generated, so it can only ever be displayed.
    readonly_fields = ("created_at",)
    extra = 2
    show_change_link = True


@admin.register(Movie)
class MovieAdmin(AuditedModelAdmin):
    form = MovieForm
    list_display = ("title", "release_year", "director", "created_at", "average_score")
    list_filter = ("genres", "release_year")
    search_fields = ("title", "description")
    search_help_text = "Escribe un título o cualquier palabra de la descripción para buscar."
    list_select_related = ("director",)
    date_hierarchy = "created_at"
    ordering = ("-release_year", "title")
    list_per_page = 50
    show_full_result_count = False
    filter_horizontal = ("genres",)
    autocomplete_fields = ("director",)
    inlines = (RatingInline,)
    fieldsets = (
        (None, {
            "fields": (
                ("title", "release_year"),
                ("duration", "poster"),
                ("director", "genres"),
                "description",
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(avg_score=Avg("ratings__score"))

    def average_score(self, obj):
        if obj.avg_score is not None:
            return round(obj.avg_score, 1)
        return "-"
    average_score.short_description = "Punt. media"
    average_score.admin_order_field = "avg_score"


@admin.register(Genre)
class GenreAdmin(AuditedModelAdmin):
    form = GenreForm
    list_display = ("name", "description", "created_at", "movie_count")
    search_fields = ("name", "description")
    search_help_text = "Escribe el nombre de un género o cualquier palabra de su descripción."
    ordering = ("name",)
    list_per_page = 50
    fieldsets = (
        (None, {
            "fields": ("name", "description"),
        }),
    )

    def movie_count(self, obj):
        return obj.movies.count()
    movie_count.short_description = "# películas"


@admin.register(Person)
class PersonAdmin(AuditedModelAdmin):
    form = PersonForm
    list_display = ("name", "birth_date", "created_at", "movie_count")
    search_fields = ("name", "biography")
    search_help_text = "Escribe el nombre de una persona o cualquier palabra de su biografía."
    ordering = ("name",)
    list_per_page = 50
    fieldsets = (
        (None, {
            "fields": (
                ("name", "birth_date"),
                "biography",
            )
        }),
    )

    def movie_count(self, obj):
        return obj.directed_movies.count()
    movie_count.short_description = "# películas dirigidas"


@admin.register(Rating)
class RatingAdmin(AuditedModelAdmin):
    form = RatingForm
    list_display = ("movie", "score", "comment", "created_at")
    list_filter = ("score",)
    # A bare `movie` is not a valid lookup here: Django would build
    # `movie__icontains`, which a ForeignKey does not support. Traverse to the
    # related field instead, so searching matches the movie title.
    search_fields = ("movie__title", "comment")
    search_help_text = (
        "Escribe el título de una película o cualquier palabra de un comentario."
    )
    list_select_related = ("movie",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50
    show_full_result_count = False
    autocomplete_fields = ("movie",)
    fieldsets = (
        (None, {
            "fields": ("movie", "score", "comment"),
        }),
    )