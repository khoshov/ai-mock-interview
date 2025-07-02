from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Category


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'description', 'parent')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    mptt_level_indent = 20
