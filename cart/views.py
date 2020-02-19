from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from . import models

# Create your views here.


class CartView(ListView):
    '''Shopping Cart View'''

    model = models.Cart
    template_name = 'shopping_cart.html'
    context_object_name = 'shopping_cart_items'

    def get_queryset(self):
        '''Returns the shopping cart items to the template.'''

        queryset = super().get_queryset()
        return queryset.filter(customer=self.request.user.id)

    def get_context_data(self, **kwargs):
        '''Returns the shopping cart total to the template.'''

        context = super().get_context_data(**kwargs)
        items_cost = self.model.objects.filter(customer=self.request.user).values_list('amount', flat=True)
        total = 0
        for item_cost in items_cost:
            total += item_cost
        context['cart_total'] = total
        return context
