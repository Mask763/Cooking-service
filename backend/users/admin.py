from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import ApplicationUser


class ApplicationUserAdmin(UserAdmin):
    model = ApplicationUser
    search_fields = ('username', 'email')


admin.site.register(ApplicationUser, ApplicationUserAdmin)
