from django import forms
from django.core.exceptions import ValidationError

from .models import Movie, Genre, Person, Rating


class MovieForm(forms.ModelForm):
    """Formulario personalizado para la película."""

    class Meta:
        model = Movie
        fields = [
            "title",
            "description",
            "release_year",
            "duration",
            "poster",
            "genres",
            "director",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Título de la película", "class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Descripción breve de la película",
                    "rows": 3,
                    "class": "form-control",
                }
            ),
            "release_year": forms.NumberInput(
                attrs={
                    "placeholder": "Año de estreno",
                    "min": 1888,
                    "class": "form-control",
                }
            ),
            "duration": forms.NumberInput(
                attrs={"placeholder": "Duración en minutos", "min": 1, "class": "form-control"}
            ),
            "poster": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
            "genres": forms.CheckboxSelectMultiple(),
            "director": forms.Select(attrs={"class": "form-control"}),
        }
        help_texts = {
            "release_year": "Año del primer estreno (entre 1888 y el año actual + 1).",
            "duration": "Duración en minutos.",
            "title": "Nombre completo de la película.",
        }

    def clean_release_year(self):
        year = self.cleaned_data.get("release_year")
        if year is not None:
            if year < 1888:
                raise ValidationError("El año de estreno no puede ser anterior a 1888.")
            from datetime import date

            if year > date.today().year + 1:
                raise ValidationError(
                    f"El año de estreno no puede ser posterior a {date.today().year + 1}."
                )
        return year


class GenreForm(forms.ModelForm):
    """Formulario personalizado para el género."""

    class Meta:
        model = Genre
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Nombre del género", "class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Descripción del género",
                    "rows": 2,
                    "class": "form-control",
                }
            ),
        }
        help_texts = {
            "name": "Nombre único del género.",
            "description": "Descripción opcional del género.",
        }


class PersonForm(forms.ModelForm):
    """Formulario personalizado para la persona (director)."""

    class Meta:
        model = Person
        fields = ["name", "biography", "birth_date"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Nombre completo", "class": "form-control"}
            ),
            "biography": forms.Textarea(
                attrs={
                    "placeholder": "Biografía de la persona",
                    "rows": 3,
                    "class": "form-control",
                }
            ),
            "birth_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
        }
        help_texts = {
            "birth_date": "Fecha de nacimiento. No puede ser una fecha futura.",
        }


class RatingForm(forms.ModelForm):
    """Formulario personalizado para la valoración."""

    class Meta:
        model = Rating
        fields = ["movie", "score", "comment"]
        widgets = {
            "movie": forms.Select(attrs={"class": "form-control"}),
            "score": forms.Select(
                attrs={"class": "form-control"},
                choices=[(i, f"{i}/10") for i in range(1, 11)],
            ),
            "comment": forms.Textarea(
                attrs={
                    "placeholder": "Comentario opcional",
                    "rows": 2,
                    "class": "form-control",
                }
            ),
        }
        help_texts = {
            "score": "Puntuación del 1 al 10.",
            "comment": "Comentario opcional sobre la película.",
        }


class MovieSearchForm(forms.Form):
    """Formulario de búsqueda y filtrado de películas."""

    query = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar por título o descripción...",
                "class": "form-control",
            }
        ),
    )
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        empty_label="Todos los géneros",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    min_score = forms.TypedChoiceField(
        required=False,
        coerce=int,
        empty_value=None,
        label="Puntuación mínima",
        widget=forms.Select(attrs={"class": "form-control"}),
        choices=[("", None)] + [(i, f"{i} o más") for i in range(1, 11)],
    )


class RatingSubmitForm(forms.ModelForm):
    """Formulario para que un usuario valore una película desde la página pública."""

    class Meta:
        model = Rating
        fields = ["score", "comment"]
        widgets = {
            "score": forms.Select(
                choices=[(i, f"{i}/10") for i in range(1, 11)],
                attrs={"class": "form-control"},
            ),
            "comment": forms.Textarea(
                attrs={
                    "placeholder": "Tu comentario (opcional)",
                    "rows": 2,
                    "class": "form-control",
                }
            ),
        }
        help_texts = {
            "score": "Puntuación del 1 al 10.",
            "comment": "Escribe tu opinión sobre esta película.",
        }


class RatingInlineForm(forms.ModelForm):
    """Formulario simplificado para la valoración dentro del formulario de película."""

    class Meta:
        model = Rating
        fields = ["score", "comment"]
        widgets = {
            "score": forms.Select(
                choices=[(i, f"{i}/10") for i in range(1, 11)],
                attrs={"class": "form-control"},
            ),
            "comment": forms.Textarea(
                attrs={
                    "placeholder": "Comentario (opcional)",
                    "rows": 1,
                    "class": "form-control",
                }
            ),
        }
        help_texts = {
            "score": "Puntuación del 1 al 10.",
        }
