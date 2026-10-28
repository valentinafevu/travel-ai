import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from travel.models import Accommodation, Flight, Traveler


def save_record(model, values):
    record, _ = model.objects.get_or_create(pk=values["id"], defaults=values)
    for key, value in values.items():
        setattr(record, key, value)
    record.full_clean()
    record.save()


class Command(BaseCommand):
    help = "Carga o actualiza los tres perfiles y el inventario ficticio de la demo."

    def add_arguments(self, parser):
        parser.add_argument("--start-date", help="Primera salida (YYYY-MM-DD). Por defecto, dentro de 30 días.")

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            start = date.fromisoformat(options["start_date"]) if options["start_date"] else timezone.localdate() + timedelta(days=30)
        except ValueError as error:
            raise CommandError("Usa una fecha válida con formato YYYY-MM-DD.") from error
        data = json.loads((Path(__file__).resolve().parents[2] / "data" / "demo.json").read_text())
        for values in data["users"]:
            save_record(Traveler, values)
        for values in data["accommodations"]:
            check_in = start + timedelta(days=values.pop("day_offset"))
            values["check_in"] = check_in
            values["check_out"] = check_in + timedelta(days=values.pop("nights"))
            save_record(Accommodation, values)
        for values in data["flights"]:
            departure_date = start + timedelta(days=values.pop("day_offset"))
            departure = timezone.make_aware(datetime.combine(departure_date, time.fromisoformat(values.pop("departure_time"))))
            values["departure_at"] = departure
            values["arrival_at"] = departure + timedelta(minutes=values.pop("duration_minutes"))
            save_record(Flight, values)
        self.stdout.write(self.style.SUCCESS("Demo lista: 3 usuarios, 6 alojamientos y 12 vuelos."))
