from django.contrib import admin

from .models import Genre, Movie, Person, Rating

# Basic registration: Django builds a default ModelAdmin for each model.
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Person)
admin.site.register(Rating)
