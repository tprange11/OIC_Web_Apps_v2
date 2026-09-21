from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User, PermissionsMixin
from django.contrib.auth import get_user_model
profile_user = get_user_model()


class User(User, PermissionsMixin):
    '''Multi-table subclass of Django's User (adds an accounts_user table). It is not
    the AUTH_USER_MODEL and nothing in the project references it; the rest of the app
    uses get_user_model(), i.e. the stock auth User.'''

    def __str__(self):
        return f"{self.username}"


class Profile(models.Model):
    '''Per-user email opt-ins, one boolean per program. Created lazily by
    UpdateProfileView; slug is the user id.'''

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
    open_roller_email = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, null=False)

    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'slug': self.slug})

    class Meta:
        unique_together = ['user', 'slug']


class ReleaseOfLiability(models.Model):
    '''Records that the user accepted the release of liability (one row per user).'''

    user = models.ForeignKey(profile_user, on_delete=models.CASCADE)
    release_of_liability = models.BooleanField(
        default=False, null=False, blank=False)
    release_of_liability_date_signed = models.DateTimeField(
        auto_now_add=True, null=True)

    class Meta:
        unique_together = ['user', 'release_of_liability']


class ChildSkater(models.Model):
    '''A child or dependent skater registered under a user's account.'''

    user = models.ForeignKey(profile_user, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    date_of_birth = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class UserCredit(models.Model):
    '''Prepaid credits (whole dollars) a user can spend on sessions.

    balance: spendable credits. pending: credits bought but not yet paid for; moved
    into balance by payment/views.py and zeroed nightly if never paid. paid: True while
    the user has a paid-for balance; program apps require it before deducting, and it is
    reset to False when the balance hits zero. slug is the username.'''

    user = models.ForeignKey(profile_user, on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(null=True, default=0)
    pending = models.PositiveIntegerField(null=True, default=0)
    paid = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, null=False)

    class Meta:
        unique_together = ['user', 'slug']

    def __str__(self):
        return f"{self.user.get_full_name()} credit balance: ${self.balance}"
