from django.contrib.auth.models import AbstractUser
from django.db import models

from .constatns import MAX_CHARFIELD_LENGTH, MAX_EMAIL_LENGTH, DEFAULT_AVATAR


class ApplicationUser(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    username = models.CharField(
        max_length=MAX_CHARFIELD_LENGTH,
        unique=True,
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': "Пользователь с таким именем уже существует.",
        },
        verbose_name='Имя пользователя'
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует.'
        },
        verbose_name='Email',
    )
    first_name = models.CharField(
        max_length=MAX_CHARFIELD_LENGTH,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_CHARFIELD_LENGTH,
        blank=False,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name='Аватар',
        default=DEFAULT_AVATAR
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
