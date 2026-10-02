"""Pruebas de regresión del catálogo público de películas.

Estas pruebas fijan el comportamiento actual del proyecto antes de la
refactorización del Laboratorio #6 (motor de plantillas). Su objetivo es
que cualquier cambio posterior en plantillas, vistas o URLs pueda
verificarse de inmediato: si una prueba falla, el cambio rompió algo que
antes funcionaba.

Se prueba comportamiento observable (códigos de respuesta, contenido
renderizado y efectos en la base de datos) y no detalles internos.
"""

from datetime import date

from django.contrib.messages import get_messages
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse

from .models import Genre, Movie, Person, Rating

# Contenido HTML usado para comprobar el escapado automático de Django.
HTML_SNIPPET = "<script>alert('xss')</script>"


class MovieTestData(TestCase):
    """Datos mínimos y válidos, compartidos por las clases hijas.

    La película de ejemplo está enlazada a dos géneros y a un director,
    de modo que las relaciones Movie-Genre y Movie-Person puedan
    verificarse tal como las usa el sitio público.
    """

    @classmethod
    def setUpTestData(cls):
        cls.accion = Genre.objects.create(
            name="Acción",
            description="Películas de acción y aventuras.",
        )
        cls.drama = Genre.objects.create(name="Drama")

        cls.director = Person.objects.create(
            name="Ada Director",
            biography="Directora ficticia usada en las pruebas.",
            birth_date=date(1970, 5, 4),
        )

        cls.movie = Movie.objects.create(
            title="La Película de Prueba",
            description="Descripción de la película de prueba.",
            release_year=1994,
            duration=118,
            director=cls.director,
        )
        cls.movie.genres.add(cls.accion, cls.drama)


class RecommendationPageTests(MovieTestData):
    """La portada de recomendaciones responde y se renderiza siempre."""

    def test_la_portada_responde_correctamente(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertEqual(response.status_code, 200)

    def test_la_portada_usa_la_plantilla_esperada(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertTemplateUsed(response, "movies/recommendations.html")
        self.assertTemplateUsed(response, "movies/base.html")

    def test_la_raiz_del_sitio_redirige_a_las_recomendaciones(self):
        response = self.client.get("/")

        self.assertRedirects(
            response,
            reverse("movies:recommendations"),
            fetch_redirect_response=True,
        )

    def test_la_portada_expone_el_contexto_esperado(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertIn("recommendations", response.context)
        self.assertIn("movie_count", response.context)
        self.assertIn("search_form", response.context)

    def test_la_portada_funciona_con_el_catalogo_vacio(self):
        Movie.objects.all().delete()

        response = self.client.get(reverse("movies:recommendations"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["movie_count"], 0)
        self.assertEqual(len(response.context["recommendations"]), 0)


class RecommendationsContentTests(MovieTestData):
    """Las películas con contenido aparecen agrupadas por género."""

    def _grupos_de(self, response):
        """Devuelve un dict {género: [películas]} desde el contexto."""
        return {
            grupo["genre"].name: list(grupo["movies"])
            for grupo in response.context["recommendations"]
        }

    def test_una_pelicula_aparece_cuando_existe_contenido(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertContains(response, self.movie.title)

    def test_la_pelicula_aparece_bajo_cada_genero_que_tiene(self):
        response = self.client.get(reverse("movies:recommendations"))

        grupos = self._grupos_de(response)

        self.assertIn(self.movie, grupos["Acción"])
        self.assertIn(self.movie, grupos["Drama"])

    def test_una_pelicula_sin_genero_no_crea_ningun_grupo(self):
        Movie.objects.all().delete()
        sin_genero = Movie.objects.create(
            title="Película Sin Géneros",
            release_year=2000,
            duration=90,
            director=self.director,
        )

        response = self.client.get(reverse("movies:recommendations"))

        grupos = self._grupos_de(response)
        self.assertNotIn("Drama", grupos)
        self.assertEqual(list(grupos), [])
        # Sigue contando para el total, aunque no se agrupe en ninguna sección.
        self.assertEqual(response.context["movie_count"], 1)
        self.assertNotIn(sin_genero, [m for ms in grupos.values() for m in ms])

    def test_una_pelicula_sin_valorar_no_es_la_primera(self):
        valorada = Movie.objects.create(
            title="Película Valorada",
            release_year=2001,
            duration=100,
            director=self.director,
        )
        valorada.genres.add(self.accion)
        Rating.objects.create(movie=valorada, score=9, comment="Excelente.")

        response = self.client.get(reverse("movies:recommendations"))

        grupo_accion = self._grupos_de(response)["Acción"]
        self.assertEqual(grupo_accion[0], valorada)

    def test_se_muestran_como_mucho_cinco_peliculas_por_genero(self):
        for indice in range(1, 8):
            pelicula = Movie.objects.create(
                title=f"Película {indice}",
                release_year=1990 + indice,
                duration=100,
                director=self.director,
            )
            pelicula.genres.add(self.accion)

        response = self.client.get(reverse("movies:recommendations"))

        self.assertEqual(len(self._grupos_de(response)["Acción"]), 5)

    def test_el_catalogo_completo_se_muestra_aunque_haya_truncamiento(self):
        for indice in range(1, 8):
            Movie.objects.create(
                title=f"Extra {indice}",
                release_year=1990 + indice,
                duration=100,
                director=self.director,
            ).genres.add(self.accion)

        response = self.client.get(reverse("movies:recommendations"))

        self.assertEqual(response.context["movie_count"], 8)


class MovieDetailPageTests(MovieTestData):
    """La ficha de una película responde y muestra sus datos."""

    def test_la_pagina_de_detalle_responde_correctamente(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_la_pagina_de_detalle_usa_las_plantillas_esperadas(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertTemplateUsed(response, "movies/movie_detail.html")
        self.assertTemplateUsed(response, "movies/base.html")

    def test_el_detalle_muestra_los_datos_de_la_pelicula(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertContains(response, self.movie.title)
        self.assertContains(response, str(self.movie.release_year))
        self.assertContains(response, f"{self.movie.duration} min")

    def test_el_detalle_expone_el_contexto_esperado(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertEqual(response.context["movie"], self.movie)
        self.assertIn("rating_form", response.context)
        self.assertIn("average_score", response.context)

    def test_el_detalle_funciona_sin_valoraciones(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["average_score"])

    def test_el_detalle_muestra_el_promedio_de_las_valoraciones(self):
        Rating.objects.create(movie=self.movie, score=8, comment="Bien.")
        Rating.objects.create(movie=self.movie, score=6)

        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertEqual(response.context["average_score"], 7)

    def test_una_pelicula_inexistente_devuelve_404(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[999_999])
        )

        self.assertEqual(response.status_code, 404)

    def test_un_identificador_no_numerico_devuelve_404(self):
        response = self.client.get("/movies/no-es-un-numero/")

        self.assertEqual(response.status_code, 404)


class RatingSubmissionTests(MovieTestData):
    """El envío de una valoración mantiene el flujo PRG actual."""

    def url(self):
        return reverse("movies:movie_detail", args=[self.movie.pk])

    def test_una_valoracion_valida_se_guarda_y_redirige(self):
        response = self.client.post(
            self.url(),
            {"score": 8, "comment": "Muy buena película."},
        )

        self.assertRedirects(response, self.url())
        self.assertEqual(Rating.objects.count(), 1)

        rating = Rating.objects.get()
        self.assertEqual(rating.movie, self.movie)
        self.assertEqual(rating.score, 8)
        self.assertEqual(rating.comment, "Muy buena película.")

    def test_la_valoracion_se_confirma_con_un_mensaje(self):
        response = self.client.post(
            self.url(),
            {"score": 9, "comment": "Excelente."},
        )

        mensajes = [str(m) for m in get_messages(response.wsgi_request)]

        self.assertEqual(len(mensajes), 1)
        self.assertIn("valoración", mensajes[0])

    def test_la_valoracion_aparece_luego_en_la_pagina(self):
        self.client.post(self.url(), {"score": 8, "comment": "Mi comentario."})

        response = self.client.get(self.url())

        self.assertContains(response, "Mi comentario.")
        self.assertContains(response, "8/10")

    def test_se_pueden_registrar_varias_valoraciones(self):
        self.client.post(self.url(), {"score": 8, "comment": "Primera."})
        self.client.post(self.url(), {"score": 4, "comment": "Segunda."})

        self.assertEqual(Rating.objects.filter(movie=self.movie).count(), 2)

    def test_una_puntuacion_fuera_de_rango_se_rechaza(self):
        response = self.client.post(
            self.url(),
            {"score": 11, "comment": "Fuera de rango."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Rating.objects.count(), 0)
        self.assertTrue(response.context["rating_form"].errors)

    def test_una_valoracion_sin_puntuacion_se_rechaza(self):
        response = self.client.post(self.url(), {"score": "", "comment": "Sin nota."})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Rating.objects.count(), 0)


class TemplateRenderingTests(MovieTestData):
    """Las plantillas actuales se cargan y renderizan sin errores."""

    def test_las_plantillas_del_proyecto_se_pueden_cargar(self):
        for nombre in (
            "movies/base.html",
            "movies/recommendations.html",
            "movies/movie_detail.html",
        ):
            with self.subTest(plantilla=nombre):
                self.assertIsNotNone(get_template(nombre))

    def test_la_plantilla_base_aporta_la_navegacion(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertContains(response, "<nav", html=False)
        self.assertContains(response, reverse("movies:recommendations"))
        self.assertContains(response, reverse("admin:index"))

    def test_la_plantilla_base_carga_el_archivo_estatico(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertContains(response, "css/movies.css")

    def test_las_valoraciones_se_listan_en_el_detalle(self):
        Rating.objects.create(movie=self.movie, score=7, comment=" Comentario visible.")

        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertContains(response, "Comentario visible.")

    def test_el_buscador_se_renderiza_en_la_portada(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertIn("query", response.context["search_form"].fields)
        self.assertIn("genre", response.context["search_form"].fields)
        self.assertIn("min_score", response.context["search_form"].fields)


class EscapingTests(MovieTestData):
    """El contenido HTML se escapa automáticamente en las plantillas.

    Sirven de línea base para el objetivo de escapado del Laboratorio #6:
    ningún campo renderizado debe interpretarse como HTML.
    """

    def test_los_comentarios_de_valoracion_se_escapan(self):
        Rating.objects.create(movie=self.movie, score=5, comment=HTML_SNIPPET)

        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_las_descripciones_de_genero_se_escapan(self):
        Genre.objects.create(name="Caché", description=HTML_SNIPPET)

        pelicula = Movie.objects.create(
            title="Película Con Caché",
            release_year=1999,
            duration=95,
            director=self.director,
        )
        pelicula.genres.add(Genre.objects.get(name="Caché"))

        response = self.client.get(reverse("movies:recommendations"))

        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_los_titulos_se_escapan(self):
        Movie.objects.create(
            title=HTML_SNIPPET,
            release_year=1998,
            duration=80,
            director=self.director,
        ).genres.add(self.drama)

        response = self.client.get(reverse("movies:recommendations"))

        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")


class MovieRelationsTests(MovieTestData):
    """Las relaciones Movie-Genre y Movie-Person funcionan como espera el sitio."""

    def test_el_director_de_una_pelicula_se_resuelve(self):
        Movie.objects.get(pk=self.movie.pk)

        self.assertEqual(self.movie.director, self.director)
        self.assertEqual(list(self.director.directed_movies.all()), [self.movie])

    def test_el_director_se_muestra_en_el_detalle(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertContains(response, self.director.name)

    def test_el_director_se_muestra_en_las_recomendaciones(self):
        response = self.client.get(reverse("movies:recommendations"))

        self.assertContains(response, self.director.name)

    def test_los_generos_de_una_pelicula_se_resuelven(self):
        generos = set(self.movie.genres.values_list("name", flat=True))

        self.assertEqual(generos, {"Acción", "Drama"})

    def test_el_genero_recibe_sus_peliculas(self):
        self.assertEqual(list(self.accion.movies.all()), [self.movie])
        self.assertEqual(list(self.drama.movies.all()), [self.movie])

    def test_los_generos_se_muestran_en_el_detalle(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.movie.pk])
        )

        self.assertContains(response, "Acción")
        self.assertContains(response, "Drama")

    def test_no_se_puede_borrar_un_director_con_peliculas(self):
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.director.delete()