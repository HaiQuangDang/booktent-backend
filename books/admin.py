from django.contrib import admin

# Register your models here.
from .models import Book
from .models import Author, Genre

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "price", "status", "created_at")
    list_filter = ("status", "store")
    search_fields = ("title", "store__name")


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)

