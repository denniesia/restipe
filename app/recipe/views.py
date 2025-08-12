from django.shortcuts import render

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSets(mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user
        ).order_by('-name')


