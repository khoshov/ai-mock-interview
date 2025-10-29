import csv
from django.core.management.base import BaseCommand
from apps.questions.models import Question
from apps.questions.resources import QuestionResource

class Command(BaseCommand):
    help = 'Export questions to a CSV file'

    def handle(self, *args, **options):
        queryset = Question.objects.all()
        resource = QuestionResource()
        dataset = resource.export(queryset)
        
        with open('questions.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in dataset:
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS('Successfully exported questions to questions.csv'))
