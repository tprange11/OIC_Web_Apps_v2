from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Cart(models.Model):
    '''One unpaid line item in a user's cart. `item` is the program name (or
    "User Credits"), which cart/views.py and payment/views.py match on by string.
    `amount` is whole dollars. Rows are wiped nightly by clear_cart_and_unpaid_items.py.'''

    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    skater_name = models.CharField(max_length=100)
    event_date = models.DateField()
    event_start_time = models.CharField(max_length=10, blank=True)
    amount = models.IntegerField()
    time_stamp = models.DateTimeField(auto_now_add=True, null=True)
