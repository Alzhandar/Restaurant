"""
User models for Restaurant Reservation System
"""

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField


class UserRole(models.TextChoices):
    """User roles in the system"""
    GUEST = 'guest', 'Guest'
    RESTAURANT_OWNER = 'owner', 'Restaurant Owner'
    ADMIN = 'admin', 'Administrator'


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user"""
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for Restaurant Reservation System
    
    Uses email as the primary identifier instead of username.
    Supports role-based access control (RBAC).
    """
    
    username = None  # Remove username field
    
    # Basic Information
    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.',
        },
    )
    first_name = models.CharField('first name', max_length=150)
    last_name = models.CharField('last name', max_length=150)
    
    # Contact Information
    phone = PhoneNumberField(
        'phone number',
        blank=True,
        null=True,
        help_text='Phone number in international format'
    )
    
    # Role
    role = models.CharField(
        'role',
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.GUEST,
        help_text='User role in the system'
    )
    
    # Status
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Designates whether this user should be treated as active.'
    )
    
    # Timestamps
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between"""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user"""
        return self.first_name
    
    @property
    def is_guest(self):
        """Check if user is a guest"""
        return self.role == UserRole.GUEST
    
    @property
    def is_owner(self):
        """Check if user is a restaurant owner"""
        return self.role == UserRole.RESTAURANT_OWNER
    
    @property
    def is_admin_user(self):
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN or self.is_superuser

