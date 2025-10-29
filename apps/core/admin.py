from mptt.admin import MPTTModelAdmin
from import_export.admin import ImportExportModelAdmin

from django.contrib import admin

from .models import Category
from .resources import CategoryResource


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin, MPTTModelAdmin):
    resource_classes = [CategoryResource]
    list_display = ("name", "description", "parent")
    list_filter = ("parent",)
    search_fields = ("name", "description")
    mptt_level_indent = 20
