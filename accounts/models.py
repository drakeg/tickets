from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

class MyUserManager(BaseUserManager):
    def create_user(self, username, fname, lname, email, password=None):
        """
        Creates and saves a User with the given username, first name, last name, email,
        and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
			username=username,
            fname=fname,
            lname=lname,
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, fname, lname, email, password,):
        """
        Creates and saves a superuser with the given username, email,
        and password.
        """
        user = self.create_user(
			username,
            fname,
            lname,
            email,
            password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class Employee(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    username = models.CharField(max_length=100, unique=True)
    fname = models.CharField(max_length=50)
    lname = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['fname', 'lname', 'email', ]

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin