from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, UserSerializer
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics
from django.contrib.auth.models import User
# from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
import os


class CategoryViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing category instances.
    """
    queryset = Category.objects.all()  # Retrieve all categories from the database
    serializer_class = CategorySerializer  # Serializer for category data
    permission_classes = [permissions.IsAdminUser]  # Only admins can access this viewset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            return response
        except ValidationError as e:
            # Handle unique constraint violation
            if 'slug' in str(e):  # Check for a specific unique field
                return Response({'error': 'A category with this slug already exists.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'Invalid data provided.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing product instances.
    """
    queryset = Product.objects.all() 
    serializer_class = ProductSerializer  # Serializer for product data

    def get_queryset(self):
        """
        Optionally restricts the returned products to only those
        that are accepted if the request method is 'GET'.
        """
        if self.request.method == 'GET':
            return Product.objects.filter(state=Product.ACCEPTED)
        return Product.objects.all()  # For other methods, return all products

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save(creator=request.user, state='draft')
            resp = Response(serializer.data, status=status.HTTP_201_CREATED)
            return resp
        except ValidationError as e:
            # Handle unique constraint violation
            if 'slug' in str(e):  # Check for a specific unique field
                return Response({'error': 'A product with this slug already exists.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'Invalid data provided.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            # Handle unique constraint violation
            if 'slug' in str(e):  # Check for a specific unique field
                return Response({'error': 'A product with this slug already exists.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'Invalid data provided.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """
        Handle updating a product instance, including state changes.
        Args:
            request: The HTTP request containing data for the update.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        product = self.get_object()  # Get the product instance being updated
        new_state = request.data.get('state')  # Get the new state from the request data
        
        if new_state:  # Check if a new state is provided
            try:
                # Attempt to change the state of the product
                product.change_state(new_state, request.user)
                # Check if the new state is one of the states that require email notification
                if new_state in ['rejected', 'banned', 'accepted']:
                    self.send_state_change_email(product, new_state)
                return Response({'status': 'state updated'}, status=status.HTTP_200_OK)  # Return success response
            except PermissionDenied as e:
                # Handle permission errors
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)  # Forbidden access
            except ValueError as e:
                # Handle invalid state transition errors
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)  # Bad request due to invalid state

        # If no new state is provided, proceed with the default update behavior
        return super().update(request, *args, **kwargs)

    def send_state_change_email(self, product, new_state):
        """
        Send an email notification to the creator when the state changes.
        Args:
            product: The product instance whose state has changed.
            new_state: The new state of the product.
        """
        subject = f"Product '{product.title}' state changed to '{new_state}'"
        message = f"Hello {product.creator.username},\n\n" \
                  f"The state of your product '{product.title}' has been changed to '{new_state}'.\n\n" \
                  "Thank you!"        
        send_mail(
            subject,
            message,
            'whoppah.marketplace@example.com',
            [product.creator.email],
            fail_silently=False,
        )

class UserCreateViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"id": user.id, "username": user.username}, status=status.HTTP_201_CREATED)
