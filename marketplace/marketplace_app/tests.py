from django.urls import reverse
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Product, Category, User
from django.conf import settings

class CategoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password')
        self.client.login(username='admin', password='password')
        self.token = self.obtain_jwt_token()
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def obtain_jwt_token(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'admin',
            'password': 'password'
        })
        return response.data['access']

    def test_create_category(self):
        url = reverse('category-list')
        data = {'title': 'Art', 'slug': 'art'}
        response = self.client.post(url, data, format='json', **self.headers)

        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.get().title, 'Art')

    def test_update_category(self):
        category = Category.objects.create(title='Art', slug='art')
        url = reverse('category-detail', args=[category.id])
        data = {'title': 'Artwork'}
        
        response = self.client.patch(url, data, format='json', **self.headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.title, 'Artwork')

    def test_delete_category(self):
        category = Category.objects.create(title='Art', slug='art')
        url = reverse('category-detail', args=[category.id])
        
        response = self.client.delete(url, **self.headers)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_list_categories(self):
        Category.objects.create(title='Art', slug='art')
        Category.objects.create(title='Design', slug='design')
        url = reverse('category-list')
        
        response = self.client.get(url, **self.headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_unique_slug(self):
        Category.objects.create(title='Art', slug='art')
        url = reverse('category-list')
        data = {'title': 'Another Art', 'slug': 'art'}
        
        response = self.client.post(url, data, format='json', **self.headers)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ProductUpdateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.user1 = User.objects.create_user(username='testuser1', password='password')
        self.admin_user = User.objects.create_superuser(username='testuseradmin', password='password')
        self.client.login(username='testuser', password='password')
        self.token = self.obtain_jwt_token()
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        # self.assertTrue(self.client.login(username='testuser', password='password'))  # Check login was successful
        # self.client.login(username='testuseradmin', password='password')
        # self.admin_token = self.obtain_jwt_token_for_admin()
        # self.admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.admin_token}'}
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

        self.category = Category.objects.create(title='Art', slug='art')
        self.product = Product.objects.create(
            title='Test Product',
            description='A product for testing.',
            price=100.00,
            category=self.category,
            state='draft',
            creator=self.user
        )

    def obtain_jwt_token(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'password'
        })
        return response.data['access'] 
    
    def obtain_jwt_token_for_second_user(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser1',
            'password': 'password'
        })
        return response.data['access'] 
    
    def obtain_jwt_token_for_admin(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuseradmin',
            'password': 'password'
        })
        return response.data['access']

    def test_create_product(self):
        url = reverse('product-list')
        data = {
            'title': 'New Product',
            'description': 'A new product.',
            'price': 150.00,
            'category': self.category.id,
            'state': 'draft'
        }

        response = self.client.post(url, data, format='json', **self.headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)  # One existing, one created
        self.assertEqual(Product.objects.get(title='New Product').state, 'draft')

    def test_move_product_from_draft_to_new(self):
        self.product.state = 'draft'
        self.product.save()
        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'new'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'new')

    def test_update_product_state_as_admin(self):
        self.client.login(username='testuseradmin', password='password')
        self.admin_token = self.obtain_jwt_token_for_admin()
        self.admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.admin_token}'}
        self.product.state = 'new'
        self.product.save()
        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'accepted'}

        response = self.client.patch(url, data, format='json', **self.admin_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'accepted')

    def test_banned_product_cannot_change_state(self):
        self.product.state = 'new'
        self.product.save()

        self.client.login(username='testuseradmin', password='password')
        self.admin_token = self.obtain_jwt_token_for_admin()
        self.admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.admin_token}'}
        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'banned'}

        response = self.client.patch(url, data, format='json', **self.admin_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'banned')

        # Try changing state again
        data = {'state': 'accepted'}
        response = self.client.patch(url, data, format='json', **self.admin_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_product_as_non_admin(self):
        self.product.state = 'new'
        self.product.save()
        
        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'rejected'}

        response = self.client.patch(url, data, format='json', **self.headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'new')

    def test_update_product_state_to_accepted(self):
        self.client.login(username='testuseradmin', password='password')
        self.admin_token = self.obtain_jwt_token_for_admin()
        self.admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.admin_token}'}
        self.product.state = 'new'
        self.product.save()
        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'accepted'}

        response = self.client.patch(url, data, format='json', **self.admin_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'accepted')

    def test_update_product_state_to_rejected(self):
        self.client.login(username='testuseradmin', password='password')
        self.admin_token = self.obtain_jwt_token_for_admin()
        self.admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.admin_token}'}
        self.product.state = 'new'
        self.product.save()
        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'rejected'}

        response = self.client.patch(url, data, format='json', **self.admin_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'rejected')
    
    def test_move_rejected_product_back_to_new_as_creator(self):
        # Set product state to rejected
        self.product.state = 'rejected'
        self.product.save()

        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'new'}

        response = self.client.patch(url, data, format='json', **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'new')

    def test_move_rejected_product_back_to_new_as_non_creator(self):
        # Create another user
        self.client.logout()
        another_user = User.objects.create_user(username='anotheruser', password='password')
        self.client.login(username='anotheruser', password='password')
        self.token = self.obtain_jwt_token_for_second_user()
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        # Set product state to rejected
        self.product.state = 'rejected'
        self.product.save()

        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'new'}

        response = self.client.patch(url, data, format='json', **self.headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Expect forbidden
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'rejected')  # State should remain 'rejected'

    def test_accepted_product_cannot_change_state(self):
        self.client.login(username='testuseradmin', password='password')
        self.admin_token = self.obtain_jwt_token_for_admin()
        self.admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.admin_token}'}
        self.product.state = 'accepted'
        self.product.save()

        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'draft'}

        response = self.client.patch(url, data, format='json', **self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'accepted')  # Ensure the state hasn't changed

    def test_delete_product(self):
        url = reverse('product-detail', args=[self.product.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

    def test_non_admin_cannot_change_new_product_state(self):
        self.product.state = 'new'
        self.product.save()

        self.client.login(username='testuser', password='password')
        token = self.obtain_jwt_token()
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

        url = reverse('product-detail', args=[self.product.id])
        data = {'state': 'banned'}

        response = self.client.patch(url, data, format='json', **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.product.refresh_from_db()
        self.assertEqual(self.product.state, 'new')

    def test_list_accepted_products(self):
        self.product.state = 'accepted'
        self.product.save()
        Product.objects.create(
            title='Another Product',
            description='Another description.',
            price=200.00,
            category=self.category,
            state='draft',
            creator=self.user
        )

        url = reverse('product-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only accepted products should be listed

    def test_product_creator_is_set(self):
        url = reverse('product-detail', args=[self.product.id])
        self.assertEqual(self.product.creator, self.user)
