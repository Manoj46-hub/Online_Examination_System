
import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from exams.models import Question


class Command(BaseCommand):

    help = 'Import Java MCQs from a CSV file'

    REQUIRED_COLUMNS = [
        'unit',
        'topic',
        'question_text',
        'option_a',
        'option_b',
        'option_c',
        'option_d',
        'correct_answer',
        'explanation',
        'difficulty',
    ]

    VALID_UNITS = {
        'UNIT_1', 'UNIT_2', 'UNIT_3', 'UNIT_4', 'UNIT_5'
    }

    VALID_DIFFICULTIES = {
        'EASY', 'MEDIUM', 'HARD'
    }

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):

        csv_file = options['csv_file']

        imported = 0
        skipped = 0
        errors = 0

        try:
            with open(
                csv_file,
                mode='r',
                encoding='utf-8-sig',
                newline=''
            ) as file:

                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise CommandError('CSV file is empty.')

                missing = (
                    set(self.REQUIRED_COLUMNS)
                    - set(reader.fieldnames)
                )

                if missing:
                    raise CommandError(
                        f'Missing columns: {", ".join(sorted(missing))}'
                    )

                for row_number, row in enumerate(reader, start=2):

                    try:
                        data = {
                            key: (row.get(key) or '').strip()
                            for key in self.REQUIRED_COLUMNS
                        }

                        if any(not value for value in data.values()):
                            raise ValueError('Some fields are empty.')

                        if data['unit'] not in self.VALID_UNITS:
                            raise ValueError('Invalid unit.')

                        if data['difficulty'] not in self.VALID_DIFFICULTIES:
                            raise ValueError('Invalid difficulty.')

                        if data['correct_answer'] not in {
                            'A', 'B', 'C', 'D'
                        }:
                            raise ValueError('Invalid correct answer.')

                        with transaction.atomic():

                            question, created = Question.objects.get_or_create(
                                unit=data['unit'],
                                topic=data['topic'],
                                question_text=data['question_text'],
                                defaults={
                                    'option_a': data['option_a'],
                                    'option_b': data['option_b'],
                                    'option_c': data['option_c'],
                                    'option_d': data['option_d'],
                                    'correct_answer': data['correct_answer'],
                                    'explanation': data['explanation'],
                                    'difficulty': data['difficulty'],
                                }
                            )

                        if created:
                            imported += 1
                        else:
                            skipped += 1

                    except Exception as error:
                        errors += 1
                        self.stderr.write(
                            f'Row {row_number}: {error}'
                        )

        except OSError as error:
            raise CommandError(str(error))

        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed! Added: {imported}, '
                f'Duplicates skipped: {skipped}, Errors: {errors}'
            )
        )
