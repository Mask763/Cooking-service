from django.contrib import admin
from recipes.models import Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)


admin.site.register(Tag, TagAdmin)
