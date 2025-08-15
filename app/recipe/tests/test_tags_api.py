from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from recipe.serializers import TagSerializer
from core.models import Tag, Recipe


TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='pass123'):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsAPITests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        response = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_tags_limited_to_user(self):
        user2 = create_user(email='user2@xample.com')
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)
        self.assertEqual(response.data[0]['id'], tag.id)

    def test_update_tag(self):
        tag = Tag.objects.create(
            user=self.user,
            name='After Dinner'
        )

        payload = {
            'name':'Dessert'
        }

        url = detail_url(tag.id)
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user, self.user)

    def test_delete_tag(self):
        tag = Tag.objects.create(
            user=self.user,
            name='Dessert'
        )

        url = detail_url(tag.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(name='Dessert').exists())

    def test_filtered_tags_assigned_to_recipes(self):
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')

        recipe = Recipe.objects.create(
            title='Blueberry Crumble',
            time_minutes=5,
            price=Decimal('4.6'),
            user=self.user
        )
        recipe.tags.add(tag1)

        response = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1=TagSerializer(tag1)
        s2=TagSerializer(tag2)

        self.assertIn(s1.data, response.data)
        self.assertNotIn(s2.data, response.data)
    
    def test_filtered_tags_unique(self):
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')

        recipe1 = Recipe.objects.create(
            title='Blueberry Crumble',
            time_minutes=5,
            price=Decimal('4.6'),
            user=self.user
        )

        recipe2 = Recipe.objects.create(
            title='Lasagna',
            time_minutes=5,
            price=Decimal('4.6'),
            user=self.user
        )

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        response = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)
