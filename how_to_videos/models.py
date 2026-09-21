from django.db import models


class Category(models.Model):
    '''A How To Video category. The slug is the URL key, so it must not change once
    links exist. staff_only categories are hidden from non-staff users.'''

    video_category = models.CharField(max_length=75)
    slug = models.SlugField(max_length=100, default=None, help_text='DO NOT CHANGE THIS FIELD!')
    staff_only = models.BooleanField(default=False)

    class Meta:
        ordering = ['video_category']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f'{self.video_category}'


class Keyword(models.Model):
    '''Search keyword that can be attached to any number of videos.'''

    keyword = models.CharField(max_length=100)

    class Meta:
        ordering = ['keyword']

    def __str__(self):
        return f'{self.keyword}'


class HowToVideo(models.Model):
    '''A How To Video link, filtered by category, keyword search and staff_only.'''

    title = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    keywords = models.ManyToManyField(Keyword)
    video_url = models.CharField(max_length=300, blank=False, null=True)
    staff_only = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    date_created = models.DateField(auto_now_add=True)
    last_modified = models.DateField(auto_now=True)

    class Meta:
        unique_together = ['title', 'category', 'video_url']
