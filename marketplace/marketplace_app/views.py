from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
import os


class CategoryViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing category instances.
    """
    queryset = Category.objects.all()  # Retrieve all categories from the database
    serializer_class = CategorySerializer  # Serializer for category data
    permission_classes = [permissions.IsAdminUser]  # Only admins can access this viewset

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

    def perform_create(self, serializer):
        """
        Save a new product instance, associating it with the current user.
        Args:
            serializer: The serializer instance that validates and saves the product data.
        """
        serializer.save(creator=self.request.user, state='draft')  # Set the creator of the product to the current user

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
        print('mail', os.getenv('EMAIL_HOST_PASSWORD'))
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
