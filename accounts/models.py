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
    thane_storck_email = models.BooleanField(default=False)
    figure_skating_email = models.BooleanField(default=False)
    adult_skills_email = models.BooleanField(default=False)
    mike_schultz_email = models.BooleanField(default=False)
    yeti_skate_email = models.BooleanField(default=False)
    womens_hockey_email = models.BooleanField(default=False)
    bald_eagles_email = models.BooleanField(default=False)
    lady_hawks_email = models.BooleanField(default=False)
    chs_alumni_email = models.BooleanField(default=False)
    kranich_email = models.BooleanField(default=False)
    nacho_skate_email = models.BooleanField(default=False)
    ament_email = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, null=False)

    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'slug': self.slug})

    class Meta:
        unique_together = ['user', 'slug']


class ReleaseOfLiability(models.Model):
    '''Model that holds user release of liability.'''

    # Model Fields
    user = models.ForeignKey(profile_user, on_delete=models.CASCADE)
    release_of_liability = models.BooleanField(
        default=False, null=False, blank=False)
    release_of_liability_date_signed = models.DateTimeField(
        auto_now_add=True, null=True)

    class Meta:
        unique_together = ['user', 'release_of_liability']


class ChildSkater(models.Model):
    '''Model that holds users child or dependant skater(s) information.'''

    # Model Fields
    user = models.ForeignKey(profile_user, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    date_of_birth = models.DateField(blank=True, null=True)

    class Meta:
        # Prevent duplicate skaters
        unique_together = ['user', 'first_name', 'last_name']

    def __str__(self):
        '''Overrides string representation of class.'''
        return f"{self.first_name} {self.last_name}"


class UserCredit(models.Model):
    '''Model that holds user purchased credits'''

    # Model Fields
    user = models.ForeignKey(profile_user, on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(null=True, default=0)
    pending = models.PositiveIntegerField(null=True, default=0)
    paid = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, null=False)

    class Meta:
        unique_together = ['user', 'slug']

    def __str__(self):
        return f"{self.user.get_full_name()} credit balance: ${self.balance}"
