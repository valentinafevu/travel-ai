import math

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

INTERESTS = ("lujo", "economico", "grupo", "aventura", "playa")


def validate_vector(value):
    if not isinstance(value, dict) or any(
        key not in INTERESTS
        or isinstance(weight, bool)
        or not isinstance(weight, (int, float))
        or not math.isfinite(weight)
        or not 0 <= weight <= 1
        for key, weight in value.items()
    ):
        raise ValidationError("El vector debe contener intereses conocidos con valores entre 0 y 1.")


class Traveler(models.Model):
    id = models.SlugField(primary_key=True)
    name = models.CharField(max_length=80)
    profile = models.CharField(max_length=100)
    description = models.TextField()
    history = models.JSONField(default=list)
    origin = models.CharField(max_length=3)
    party_size = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    max_price_per_person_usd = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    vector = models.JSONField(default=dict, validators=[validate_vector])

    class Meta:
        ordering = ["name"]


class Flight(models.Model):
    id = models.SlugField(primary_key=True)
    origin = models.CharField(max_length=3)
    destination = models.CharField(max_length=3)
    airline = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=12)
    cabin = models.CharField(max_length=40)
    departure_at = models.DateTimeField()
    arrival_at = models.DateTimeField()
    price_per_person_usd = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    available_seats = models.PositiveIntegerField()
    vector = models.JSONField(default=dict, validators=[validate_vector])

    class Meta:
        ordering = ["departure_at", "id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(arrival_at__gt=models.F("departure_at")), name="flight_arrives_after_departure"),
            models.CheckConstraint(condition=~models.Q(origin=models.F("destination")), name="flight_distinct_airports"),
            models.CheckConstraint(condition=models.Q(price_per_person_usd__gte=0), name="flight_nonnegative_price"),
        ]


class Accommodation(models.Model):
    id = models.SlugField(primary_key=True)
    name = models.CharField(max_length=120)
    hotel = models.CharField(max_length=120)
    destination = models.CharField(max_length=120)
    airport = models.CharField(max_length=3)
    description = models.TextField()
    check_in = models.DateField()
    check_out = models.DateField()
    # Total por persona para toda la estancia, no tarifa por noche.
    price_per_person_usd = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    max_people = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    vector = models.JSONField(default=dict, validators=[validate_vector])

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(check_out__gt=models.F("check_in")), name="stay_positive_nights"),
            models.CheckConstraint(condition=models.Q(price_per_person_usd__gte=0), name="stay_nonnegative_price"),
        ]
