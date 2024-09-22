from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from users.models import Follow


User = get_user_model()


class ApplicationUserAdmin(UserAdmin):
    model = User
    search_fields = ('username', 'email')


class FollowAdmin(admin.ModelAdmin):
    model = Follow
    list_display = ('user', 'following')
    list_filter = ('user', 'following')
    search_fields = ('user', 'following')


admin.site.register(User, ApplicationUserAdmin)
admin.site.register(Follow, FollowAdmin)
