"""
Django command to wait for db to be available.
"""

from django.core.management.base import BaseCommand
from psycopg2 import OperationalError as psycopg2OpError
from django.db.utils import OperationalError
import time


class Command(BaseCommand):
    help = "Django command to wait for database to be available."

    def handle(self, *args, **option):
        db_check = False
        self.stdout.write("checking database availability...")
        while db_check is False:
            try:
                self.check(databases=["default"])
                db_check = True
            except(psycopg2OpError, OperationalError):
                self.stdout.write("Database is not ready yet. please wait.")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database is available!!"))
