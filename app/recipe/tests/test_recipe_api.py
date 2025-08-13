from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')

# for the single object - details
def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])

#helper function for creating a recipe
def create_recipe(user, **params):
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'link': 'http://example.com/recipe.pdf'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(
        user=user,
        **defaults
    )

    return recipe

def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    # def test_auth_required(self):
    #     response = self.client.get(RECIPES_URL)

    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='test123',
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(
            user=self.user,
        )
        create_recipe(
            user=self.user
        )

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = create_user(
            email='other@example.com', 
            password='password123'
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_recipe(self):
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99')
        }
        
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        recipe = Recipe.objects.get(id=response.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        original_link = 'https://example.com/recipe.pdf'

        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link
        )

        payload = {
            'title': 'New sample title',
        }
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe description',
            
        )

        payload = {
            'title': 'New sample title',
            'link': 'https://newexample.com/recipe.pdf',
            'description': 'New Sample recipe description',
            'time_minutes': 10,
            'price': Decimal('2.50')
        }

        url = detail_url(recipe.id)
        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, payload['link'])
        self.assertEqual(recipe.description, payload['description'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])

    def test_update_user_returns_error(self):
        new_user = create_user(
            email='user2@example.com',
            password='123pass'
        )
        recipe = create_recipe(user=self.user)

        payload = {
            'user': new_user.id,
        }

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(
            user=self.user
        )

        url = detail_url(recipe.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        new_user = create_user(
            email='user2@example.com',
            password='123pass'
        )
        recipe = create_recipe(
            user=new_user
        )

        url = detail_url(recipe.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [
                {
                    'name': 'Thai',
                },
                {
                    'name': 'Dinner',
                }
            ]
        }

        response = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)          

    def test_create_recipe_with_existing_tags(self):
        tag_indian = Tag.objects.create(
            user=self.user,
            name='Indian'
        )

        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [
                {
                    'name': 'Indian',
                },
                {
                    'name': 'Breakfast',
                }
            ]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(
            user=self.user
            )

        payload = {
            'tags': [
                {
                    'name': 'Lunch',
                }
            ]
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(
            user=self.user,
            name='Lunch'
        )
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(
            user=self.user,
            name='Breakfast'
        )
        recipe = create_recipe(user=self.user)

        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(
            user=self.user,
            name='Lunch'
        )
        payload = {
            'tags': [
                {
                    'name': 'Lunch'
                }
            ]
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag = Tag.objects.create(
            user=self.user,
            name='Dessert'
        )
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {
            'tags': []
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        payload = {
            'title': 'Cauliflower tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients' : [
                {
                    'name': 'Cauliflower'
                },
                {
                    'name': 'Salt',
                }
            ]
        }

        response = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Lemon'
        )

        payload = {
            'title': 'Vietnamese Soup',
            'time_minutes': 25,
            'price': Decimal('2.55'),
            'ingredients': [
                {
                    'name': 'Lemon'
                },
                {
                    'name': 'Fish Sauce'
                }
            ]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        recipe = create_recipe(
            user=self.user
            )

        payload = {
            'ingredients': [
                {
                    'name': 'Garlic',
                }
            ]
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(
            user=self.user,
            name='Garlic'
        )
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        ingredient_lime = Ingredient.objects.create(
            user=self.user,
            name='Lime'
        )
        recipe = create_recipe(user=self.user)

        recipe.ingredients.add(ingredient_lime)

        ingredient_sauce = Ingredient.objects.create(
            user=self.user,
            name='Soy Sauce'
        )
        payload = {
            'ingredients': [
                {
                    'name': 'Soy Sauce'
                }
            ]
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_sauce, recipe.ingredients.all())
        self.assertNotIn(ingredient_lime, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Spinach'
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients': []
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)