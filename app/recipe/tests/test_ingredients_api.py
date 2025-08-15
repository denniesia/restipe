from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='pass123'):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientsAPITests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)


    def test_retrieve_ingredients_list(self):
        Ingredient.objects.create(
            user=self.user,
            name='Cacao'
        ) 
        Ingredient.objects.create(
            user=self.user,
            name='Vanilla'
        ) 

        response = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


    def test_ingredients_limited_to_user(self):
        user2 = create_user(
            email='user2@example.com',
        )
        Ingredient.objects.create(
            user=user2,
            name='Salt'
        ) 
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Pepper',
        )

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], ingredient.name)
        self.assertEqual(response.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        ingredient =Ingredient.objects.create(
            user=self.user,
            name='Sugar'
        ) 
         
        payload = {'name': 'Coriander'}

        url = detail_url(ingredient.id)
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    
    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Oil'
        )

        url = detail_url(ingredient.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='Apples'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name='Pepper'
        )

        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.6'),
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        response = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)
    
    def test_filtered_ingredients_unique(self):
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='Apples'
        )
        Ingredient.objects.create(
            user=self.user,
            name='Pepper'
        )
        
        recipe1 = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.6'),
            user=self.user
        )

        recipe2 = Recipe.objects.create(
            title='Blueberry Crumble',
            time_minutes=5,
            price=Decimal('4.6'),
            user=self.user
        )

        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient1)

        response = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)