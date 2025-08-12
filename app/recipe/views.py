from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    authentication_class = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        #retrieve recipes for authenticated user
        return self.queryset.filter(
            user=self.request.user
            ).order_by('-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecipeSerializer
    
        return serializers.RecipeDetailSerializer
    



