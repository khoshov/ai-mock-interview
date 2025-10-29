from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export.forms import ExportForm

from .models import Question
from .resources import QuestionResource


@admin.register(Question)
class QuestionAdmin(ImportExportModelAdmin):
    resource_classes = [QuestionResource]
    # export_form_class = ExportForm
    list_display = ("text_short", "category", "difficulty", "question_type")
    list_filter = ("category", "difficulty", "question_type")
    search_fields = ("text", "correct_answer")
    list_per_page = 20

    def text_short(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_short.short_description = "Вопрос"
