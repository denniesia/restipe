from django.shortcuts import render

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
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
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializers
    
        return serializers.RecipeDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image') #creating a custom action 
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet(mixins.DestroyModelMixin, 
                            mixins.UpdateModelMixin, 
                            mixins.ListModelMixin, 
                            viewsets.GenericViewSet):
       authentication_classes = [TokenAuthentication]
       permission_classes = [IsAuthenticated]

       def get_queryset(self):
           return self.queryset.filter(
               user=self.request.user
            ).order_by('-name')


class TagViewSets(BaseRecipeAttrViewSet):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
   


class IngredientViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    
   