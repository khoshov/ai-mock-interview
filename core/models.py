from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
import uuid


class Category(MPTTModel):
    name = models.CharField(
        max_length=100,
        verbose_name="Название",
        help_text="Введите название категории"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Введите описание категории"
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительская категория"
    )

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name
