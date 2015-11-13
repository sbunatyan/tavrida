from django.core.management.base import BaseCommand, CommandError

from my_app import hello_tavrida


class Command(BaseCommand):

    help = "run tavrida service"

    def handle(self, *args, **options):
        hello_tavrida.run_me()