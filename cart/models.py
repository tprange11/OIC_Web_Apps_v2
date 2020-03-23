from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.

class Cart(models.Model):
    '''Shopping cart model.'''

    # Model fields
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    skater_name = models.CharField(max_length=100)
    event_date = models.DateField()
    event_start_time = models.CharField(max_length=10, blank=True)
    amount = models.IntegerField()
    time_stamp = models.DateTimeField(auto_now_add=True, null=True)
