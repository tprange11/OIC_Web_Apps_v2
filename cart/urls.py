from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='shopping-cart'),
    path('remove_item/<pk>/', views.RemoveItemFromCartView.as_view(), name='cart-remove-item'),
    
]
