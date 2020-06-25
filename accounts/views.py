from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from . import forms
from accounts.models import Profile, ReleaseOfLiability, ChildSkater


class SignUp(CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/signup.html'


class UpdateProfileView(LoginRequiredMixin, UpdateView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_skaters'] = ChildSkater.objects.all().filter(user=self.request.user)
        return context

    def form_valid(self, form):
        # Return a message if the profile has been updated successfully
        messages.add_message(self.request, messages.SUCCESS, 'Your profile has been successfully updated!')
        return super().form_valid(form)


class ReleaseOfLiablityView(LoginRequiredMixin, CreateView):
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


class CreateChildSkaterView(LoginRequiredMixin, CreateView):
    '''Displays page where user can add child or dependent skaters.'''
    model = ChildSkater
    form_class = forms.CreateChildSkaterForm
    template_name = 'accounts/create_my_skater_form.html'
    

    def form_valid(self, form):
        self.object = form.save(commit=False)
        form.instance.user = self.request.user
        self.success_url = reverse('accounts:profile', kwargs={'slug': self.request.user.id})
        try:
            self.object.save()
        except IntegrityError:
            messages.add_message(self.request, messages.ERROR, 'This skater is already in your skater list!')
            return render(self.request, template_name=self.template_name, context=self.get_context_data())
        # If all goes well add success message
        messages.add_message(self.request, messages.SUCCESS, 'Skater successfully added to your list!')
        
        return super().form_valid(form)


class DeleteChildSkaterView(DeleteView):
    '''Displays page where user can remove child or dependent skaters.'''
    model = ChildSkater
    success_url = ''
    
    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS, 'Skater has been removed from your list!')
        self.success_url = reverse('accounts:profile', kwargs={'slug': self.request.user.id})
        return super().delete(*args, **kwargs)
    
