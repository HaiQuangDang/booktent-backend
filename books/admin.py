from django.contrib import admin

# Register your models here.
from books.models import Author, Genre, Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "store", "price", "status", "stock_quantity", "created_at")
    list_filter = ("status", "store")
    search_fields = ("title", "store__name")


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)

