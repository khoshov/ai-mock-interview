from mptt.admin import MPTTModelAdmin

from django.contrib import admin

from .models import Category, ChatSession, Message


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ("name", "description", "parent")
    list_filter = ("parent",)
    search_fields = ("name", "description")
    mptt_level_indent = 20


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "message_count")
    list_filter = ("created",)
    readonly_fields = ("id", "created")

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = "Количество сообщений"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("session", "sender", "text_short", "created")
    list_filter = ("sender", "created")
    search_fields = ("text",)
    list_per_page = 20

    def text_short(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_short.short_description = "Сообщение"
