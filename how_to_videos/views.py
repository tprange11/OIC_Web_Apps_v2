from django.views.generic import TemplateView, ListView, View
from django.shortcuts import render

from .models import HowToVideo, Category

class HowToVideoTemplateView(TemplateView):
    '''Index page for How To Videos.'''

    template_name = 'how_to_video_index.html'
    # model = HowToVideo
    # context_object_name = 'videos'


class HowToVideoCategoryListView(ListView):
    '''Page that displays button links for each how to video category.'''

    template_name = 'how_to_video_categories_list.html'
    model = Category
    context_object_name = 'categories'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(staff_only=False)
        return queryset    


class HowToVideoListView(ListView):
    '''Page that displays list of videos in a given category.'''

    template_name = 'how_to_video_list.html'
    model = HowToVideo
    context_object_name = 'videos'

    def get_queryset(self):
        category = Category.objects.get(slug=self.kwargs.get('slug'))
        
        if not self.request.user.is_staff:
            queryset = super().get_queryset().filter(category=category.id, staff_only=False)
        else:
            queryset = super().get_queryset().filter(category=category.id)

        return queryset

    def get_context_data(self, **kwargs):
        category = Category.objects.get(slug=self.kwargs.get('slug'))
        context = super().get_context_data(**kwargs)
        context['category'] = category
        return context


class HowToVideoSearchResultsListView(ListView):
    '''Page that displays list of videos from keyword search.'''

    template_name = 'how_to_video_search_results.html'
    model = HowToVideo
    context_object_name = 'videos'

    def get_queryset(self):
        keyword = self.request.GET.get('keyword')
        if not self.request.user.is_staff:
            queryset = self.model.objects.filter(keywords__keyword__icontains=keyword, staff_only=False)
        else:
            queryset = self.model.objects.filter(keywords__keyword__icontains=keyword)

        return queryset
