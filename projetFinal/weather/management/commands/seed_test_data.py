from pathlib import Path

import sqlparse
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


SEED_TABLES = [
    "alerts",
    "weather_report",
    "weather_daily",
    "weather_hourly",
    "weather_stations",
    "variables",
    "units",
    "api_sources",
    "regions",
    "climate_types",
]


class Command(BaseCommand):
    help = "Load test data from test-data.sql into PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            dest="file_path",
            default=str(Path(settings.BASE_DIR) / "test-data.sql"),
            help="Path to the SQL seed file.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Truncate the target tables before seeding.",
        )

    def handle(self, *args, **options):
        seed_path = Path(options["file_path"])
        if not seed_path.exists():
            raise CommandError(f"Seed file not found: {seed_path}")

        sql_text = seed_path.read_text(encoding="utf-8")
        statements = [
            statement.strip()
            for statement in sqlparse.split(sql_text)
            if statement.strip()
        ]

        with transaction.atomic():
            if options["reset"]:
                self._truncate_tables()

            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

        self.stdout.write(self.style.SUCCESS(f"Seed loaded successfully from {seed_path}"))

    def _truncate_tables(self):
        with connection.cursor() as cursor:
            cursor.execute(
                f'TRUNCATE TABLE {", ".join(SEED_TABLES)} RESTART IDENTITY CASCADE;'
            )
