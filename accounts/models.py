from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User, PermissionsMixin
from django.contrib.auth import get_user_model
profile_user = get_user_model()

# Create your models here.

class User(User, PermissionsMixin):

    def __str__(self):
        return f"{self.username}"


class Profile(models.Model):
    '''Model that holds user profile data.'''
    
    # Model Fields
    user = models.ForeignKey(profile_user, on_delete=models.CASCADE)
    open_hockey_email = models.BooleanField(default=False)
    stick_and_puck_email = models.BooleanField(default=False)
    figure_skating_email = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, null=False)

    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'slug': self.slug})

    class Meta:
        unique_together = ['user', 'slug']
