from django.contrib import admin
from .models import Order, OrderItem

# class OrderItemInline(admin.TabularInline):  
#     model = OrderItem  
#     extra = 0  # Do not add empty extra fields

# class OrderAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "total_price", "status", "created_at")  # Show these fields in the list
#     list_filter = ("status", "created_at")  # Add filters for quick searching
#     search_fields = ("user__username", "id")  # Search orders by username or ID
#     ordering = ("-created_at",)  # Show newest orders first
#     inlines = [OrderItemInline]  # Show order items inside the order view
#     actions = ["mark_as_shipped", "mark_as_delivered"]  # Custom actions for admin

#     def mark_as_shipped(self, request, queryset):
#         queryset.update(status="Shipped")
#     mark_as_shipped.short_description = "Mark selected orders as Shipped"

#     def mark_as_delivered(self, request, queryset):
#         queryset.update(status="Delivered")
#     mark_as_delivered.short_description = "Mark selected orders as Delivered"

# admin.site.register(Order, OrderAdmin)
