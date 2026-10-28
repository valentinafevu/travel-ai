from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

from travel.models import Accommodation, Flight, Traveler, validate_vector


class Command(BaseCommand):
    help = "Verifica la conexión real a Oracle sin modificar datos ni mostrar credenciales."

    def add_arguments(self, parser):
        parser.add_argument("--check-data", action="store_true", help="Consulta las tablas y valida sus vectores después de migrate.")

    def handle(self, *args, **options):
        if connection.vendor != "oracle":
            raise CommandError("Oracle no está seleccionado. Instala las credenciales o usa DATABASE_BACKEND=oracle.")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                if cursor.fetchone()[0] != 1:
                    raise CommandError("Oracle devolvió una respuesta inesperada.")
            self.stdout.write(self.style.SUCCESS("Conexión real a Oracle verificada."))
            if options["check_data"]:
                for model in (Traveler, Flight, Accommodation):
                    count = 0
                    for vector in model.objects.values_list("vector", flat=True).iterator():
                        validate_vector(vector)
                        count += 1
                    self.stdout.write(f"{model.__name__}: {count} registros con vectores válidos.")
        except DatabaseError:
            raise CommandError("Falló la consulta a Oracle. Revisa credenciales, wallet, red, permisos y migraciones.") from None
        except ValidationError:
            raise CommandError("Hay un vector inválido en los datos de Oracle.") from None
