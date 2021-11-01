from django.db import models


class Category(models.Model):
    '''Model that holds categories for Hot To Videos.'''

    video_category = models.CharField(max_length=75)
    slug = models.SlugField(max_length=100, default=None, help_text='DO NOT CHANGE THIS FIELD!')
    staff_only = models.BooleanField(default=False)

    class Meta:
        ordering = ['video_category']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f'{self.video_category}'


class Keyword(models.Model):
    '''Model that holds keywords for use in How To Videos.'''

    keyword = models.CharField(max_length=100)

    class Meta:
        ordering = ['keyword']

    def __str__(self):
        return f'{self.keyword}'


class HowToVideo(models.Model):
    '''Model that stores How To Video data.'''

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
