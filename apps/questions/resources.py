from import_export import resources
from .models import Question


class QuestionResource(resources.ModelResource):
    class Meta:
        model = Question
        fields = ('id', 'text', 'category', 'difficulty', 'question_type', 'correct_answer', 'explanation')
        export_order = ('id', 'text', 'category', 'difficulty', 'question_type', 'correct_answer', 'explanation')
