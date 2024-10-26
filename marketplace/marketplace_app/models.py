from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied

class Category(models.Model):
    title = models.CharField(max_length=255)  # Title of the category
    slug = models.SlugField(unique=True, blank=True)  # Unique slug of the category

    def save(self, *args, **kwargs):
        # Automatically generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title  # String representation of the category


class Product(models.Model):
    # Define possible states for the product
    DRAFT = 'draft'
    NEW = 'new'
    REJECTED = 'rejected'
    BANNED = 'banned'
    ACCEPTED = 'accepted'

    STATE_CHOICES = [
        (DRAFT, 'Draft'),
        (NEW, 'New'),
        (REJECTED, 'Rejected'),
        (BANNED, 'Banned'),
        (ACCEPTED, 'Accepted'),
    ]

    title = models.CharField(max_length=255)  # Title of the product
    slug = models.SlugField(unique=True, blank=True)  # Unique slug of the product
    description = models.TextField()  # Detailed description of the product
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price of the product
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # Category the product belongs to
    creator = models.ForeignKey(User, on_delete=models.CASCADE)  # User who created the product
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=DRAFT)  # Current state of the product

    def save(self, *args, **kwargs):
        # Automatically generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def change_state(self, new_state, user):
        """
        Change the state of the product based on the specified rules.
        
        Args:
            new_state (str): The new state to transition to.
            user (User): The user attempting to change the state.
        
        Raises:
            PermissionDenied: If the user is not allowed to change the state.
            ValueError: If the transition is invalid.
        """
        if self.state == self.DRAFT and new_state == self.NEW:
            # Move from DRAFT to NEW
            self.state = new_state
        elif self.state == self.NEW:
            if user.is_staff:  # Only admin can change from NEW
                if new_state in [self.REJECTED, self.BANNED, self.ACCEPTED]:
                    self.state = new_state
                    self.send_notification()  # Notify creator of the change
                else:
                    raise ValueError("Invalid state transition.")
            else:
                raise PermissionDenied("Only admins can change products in 'new' state.")
        elif self.state == self.REJECTED and new_state == self.NEW:
            if user == self.creator:
                # Only the creator can move rejected products back to NEW
                self.state = new_state
            else:
                raise PermissionDenied("Only the creator can move rejected products back to 'new'.")
        elif self.state in [self.BANNED, self.ACCEPTED]:
            raise PermissionDenied("Banned and accepted products cannot change state.")
        else:
            raise ValueError("Invalid state transition.")
        
        self.save()  # Save changes to the database

    def send_notification(self):
        #todo --> will configure later
        return
