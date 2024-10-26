from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

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
    queryset = Product.objects.filter(state=Product.ACCEPTED)  # Retrieve only accepted products
    serializer_class = ProductSerializer  # Serializer for product data

    def perform_create(self, serializer):
        """
        Save a new product instance, associating it with the current user.
        Args:
            serializer: The serializer instance that validates and saves the product data.
        """
        serializer.save(creator=self.request.user)  # Set the creator of the product to the current user

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
                return Response({'status': 'state updated'}, status=status.HTTP_200_OK)  # Return success response
            except PermissionDenied as e:
                # Handle permission errors
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)  # Forbidden access
            except ValueError as e:
                # Handle invalid state transition errors
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)  # Bad request due to invalid state

        # If no new state is provided, proceed with the default update behavior
        return super().update(request, *args, **kwargs)
