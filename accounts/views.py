from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.utils import IntegrityError
from . import forms
from accounts.models import Profile


class SignUp(CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy('web_apps')
    template_name = 'accounts/signup.html'


class UpdateProfileView(UpdateView):
    '''Displays page where user can update their profile.'''
    model = Profile
    form_class = forms.ProfileForm
    template_name = 'accounts/profile_form.html'

    def get_queryset(self):
        # Try to create a profile object
        try:
            profile = self.model(user=self.request.user, slug=self.request.user.id)
            profile.save()
            queryset = self.model.objects.filter(user=self.request.user)
            return queryset
        # If a profile already exists, return the user profile object
        except IntegrityError:
            queryset = super().get_queryset()
            return queryset

    def form_valid(self, form):
        # Return a message if the profile has been updated successfully
        messages.add_message(self.request, messages.SUCCESS, 'Your profile has been successfully updated!')
        return super().form_valid(form)
