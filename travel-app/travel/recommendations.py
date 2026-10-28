from dataclasses import dataclass
from decimal import Decimal
from math import sqrt

from django.utils import timezone

from .models import Accommodation, Flight, INTERESTS


def cosine_similarity(first, second):
    product = sum(first.get(key, 0) * second.get(key, 0) for key in INTERESTS)
    first_norm = sqrt(sum(first.get(key, 0) ** 2 for key in INTERESTS))
    second_norm = sqrt(sum(second.get(key, 0) ** 2 for key in INTERESTS))
    return product / (first_norm * second_norm) if first_norm and second_norm else 0.0


@dataclass(frozen=True)
class Package:
    accommodation: Accommodation
    outbound: Flight
    inbound: Flight
    price_per_person_usd: Decimal
    score: float
    vector: dict

    @property
    def id(self):
        return f"{self.accommodation.pk}:{self.outbound.pk}:{self.inbound.pk}"


def recommend_packages(user, limit=2):
    """Combina inventario compatible y devuelve las mejores afinidades.

    La estancia y ambos vuelos pesan por igual en el vector del paquete.
    Los precios de los tres componentes son por persona, en USD.
    """
    today = timezone.localdate()
    flights = Flight.objects.filter(available_seats__gte=user.party_size, departure_at__gt=timezone.now())
    outbound_by_arrival = {}
    inbound_by_departure = {}
    for flight in flights:
        if flight.origin == user.origin:
            key = (flight.destination, timezone.localtime(flight.arrival_at).date())
            outbound_by_arrival.setdefault(key, []).append(flight)
        if flight.destination == user.origin:
            key = (flight.origin, timezone.localtime(flight.departure_at).date())
            inbound_by_departure.setdefault(key, []).append(flight)

    packages = []
    stays = Accommodation.objects.filter(max_people__gte=user.party_size, check_in__gte=today)
    for stay in stays:
        for outbound in outbound_by_arrival.get((stay.airport, stay.check_in), []):
            for inbound in inbound_by_departure.get((stay.airport, stay.check_out), []):
                if inbound.departure_at <= outbound.arrival_at:
                    continue
                price = stay.price_per_person_usd + outbound.price_per_person_usd + inbound.price_per_person_usd
                if price > user.max_price_per_person_usd:
                    continue
                vector = {
                    key: (stay.vector.get(key, 0) + outbound.vector.get(key, 0) + inbound.vector.get(key, 0)) / 3
                    for key in INTERESTS
                }
                packages.append(Package(stay, outbound, inbound, price, cosine_similarity(user.vector, vector), vector))

    return sorted(packages, key=lambda package: (-package.score, package.price_per_person_usd, package.id))[:limit]
