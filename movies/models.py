from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Year of the first motion picture ever released, used as the lower bound for
# a movie release year.
FIRST_RELEASE_YEAR = 1888

# Ratings are expressed on a 1 to 10 scale.
MIN_SCORE = 1
MAX_SCORE = 10

# Upper bound for a release year: the current year plus one, so that announced
# titles for next year can still be recorded.
LAST_RELEASE_YEAR = date.today().year + 1


def validate_not_in_future(value):
    """Reject a date that lies in the future."""
    if value > date.today():
        raise ValidationError("This date cannot be in the future.")


def validate_release_year(value):
    """Reject a release year outside the plausible range for a movie.

    The bounds are read at validation time rather than baked into a
    MinValueValidator/MaxValueValidator, so that the upper limit keeps
    tracking the current year without generating a new migration every time
    the calendar year changes.
    """
    if value < FIRST_RELEASE_YEAR:
        raise ValidationError(
            f"Release year cannot be earlier than {FIRST_RELEASE_YEAR}."
        )
    if value > LAST_RELEASE_YEAR:
        raise ValidationError(f"Release year cannot be later than {LAST_RELEASE_YEAR}.")


class Genre(models.Model):
    """A thematic category used to classify movies."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "genre"
        verbose_name_plural = "genres"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(models.Model):
    """Someone involved in the production of a movie, such as its director."""

    name = models.CharField(max_length=200)
    biography = models.TextField(blank=True)
    birth_date = models.DateField(
        null=True,
        blank=True,
        validators=[validate_not_in_future],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "people"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Movie(models.Model):
    """A movie together with its metadata, genres and director."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    release_year = models.PositiveSmallIntegerField(
        validators=[validate_release_year],
        help_text="Year of the first release.",
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Runtime in minutes.",
    )
    poster = models.ImageField(upload_to="posters/%Y/%m/", blank=True)
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    director = models.ForeignKey(
        Person,
        # Deleting a person who directed movies must not silently delete them.
        on_delete=models.PROTECT,
        related_name="directed_movies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "movie"
        verbose_name_plural = "movies"
        ordering = ["-release_year", "title"]

    def __str__(self):
        return f"{self.title} ({self.release_year})"


class Rating(models.Model):
    """A score and an optional comment left for a movie."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    score = models.SmallIntegerField(
        validators=[
            MinValueValidator(MIN_SCORE),
            MaxValueValidator(MAX_SCORE),
        ],
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "rating"
        verbose_name_plural = "ratings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movie} - {self.score}/{MAX_SCORE}"
