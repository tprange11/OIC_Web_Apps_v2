from django.db import models
from rest_framework.generics import ListAPIView
from .serializers import ProgramSerializer

from . import models


class PublicProgramListAPIView(ListAPIView):
    '''Return public programs.'''

    serializer_class = ProgramSerializer
    queryset = models.Program.objects.filter(private=False)
