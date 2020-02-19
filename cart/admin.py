from django.contrib import admin
from .models import Cart

app_name = 'cart'

# Register your models here.

class CartAdmin(admin.ModelAdmin):
    list_display = ['customer', 'item', 'skater_name', 'event_date', 'amount']

admin.site.register(Cart, CartAdmin)
