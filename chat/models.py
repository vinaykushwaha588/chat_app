from django.db import models
from django.contrib.auth.models import PermissionsMixin, BaseUserManager, AbstractBaseUser
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import uuid


class BaseUUID(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):

    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.is_active = True
        user.status = 'Active' if extra_fields.get('is_superuser', False) else 'Inactive'
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, password, **extra_fields)


class User(BaseUUID, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Banned', 'Banned'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    last_logout = models.DateTimeField(null=True, blank=True) 
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    def tokens(self):
        """
            Generate JWT tokens using DRF SimpleJWT
        """
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class PrivateChat(BaseUUID):
    """
        A private chat between two users.
    """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats_initiated")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats_received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user1', 'user2']

    def __str__(self):
        return f"Chat between {self.user1} and {self.user2}"

    def save(self, *args, **kwargs):
        if self.user1 == self.user2:
            raise ValueError("A user cannot start a chat with themselves.")
        super().save(*args, **kwargs)


class Message(BaseUUID):
    """
        A message exchanged in a private chat.
    """
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_received', null = True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)  # Seen/unseen status

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.name}: {self.content[:30]} ({'Seen' if self.seen else 'Unseen'})"
    
    def mark_seen(self):
        """Marks the message as seen."""
        self.seen = True
        self.save(update_fields=['seen'])


class FakeUserData(models.Model):
    id = models.BigAutoField(primary_key=True) 
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
