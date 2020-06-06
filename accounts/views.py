from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib import messages
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from . import forms
from accounts.models import Profile, ReleaseOfLiability


class SignUp(CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy('login')
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


class ReleaseOfLiablityView(CreateView):
    '''Displays page where user must sign Release of Liablity form.'''
    model = ReleaseOfLiability
    form_class = forms.ReleaseOfLiablityForm
    success_url = reverse_lazy('web_apps')
    template_name = 'accounts/release_of_liability.html'

    def get(self, request, *args, **kwargs):
        try:
            self.model.objects.get(user=self.request.user)
            return redirect('web_apps')
        except ObjectDoesNotExist:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
