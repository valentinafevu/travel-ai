from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import INTERESTS, Traveler
from .recommendations import recommend_packages


def serialize_user(user):
    return {
        "id": user.pk,
        "name": user.name,
        "profile": user.profile,
        "description": user.description,
        "history": user.history,
        "origin": user.origin,
        "party_size": user.party_size,
        "max_price_per_person_usd": str(user.max_price_per_person_usd),
        "vector": user.vector,
    }


def serialize_flight(flight):
    return {
        "id": flight.pk,
        "origin": flight.origin,
        "destination": flight.destination,
        "airline": flight.airline,
        "flight_number": flight.flight_number,
        "cabin": flight.cabin,
        "departure_at": timezone.localtime(flight.departure_at).isoformat(),
        "arrival_at": timezone.localtime(flight.arrival_at).isoformat(),
        "price_per_person_usd": str(flight.price_per_person_usd),
        "available_seats": flight.available_seats,
        "vector": flight.vector,
    }


def serialize_package(package, party_size):
    stay = package.accommodation
    return {
        "id": package.id,
        "name": stay.name,
        "destination": stay.destination,
        "nights": (stay.check_out - stay.check_in).days,
        "description": stay.description,
        "score": round(package.score, 6),
        "vector": package.vector,
        "price_per_person_usd": str(package.price_per_person_usd),
        "total_price_usd": str(package.price_per_person_usd * party_size),
        "max_people": min(stay.max_people, package.outbound.available_seats, package.inbound.available_seats),
        "accommodation": {
            "id": stay.pk,
            "hotel": stay.hotel,
            "airport": stay.airport,
            "check_in": stay.check_in.isoformat(),
            "check_out": stay.check_out.isoformat(),
            "price_per_person_usd": str(stay.price_per_person_usd),
            "vector": stay.vector,
        },
        "outbound_flight": serialize_flight(package.outbound),
        "return_flight": serialize_flight(package.inbound),
    }


@require_GET
def users(request):
    return JsonResponse({"users": [serialize_user(user) for user in Traveler.objects.all()], "vector_dimensions": INTERESTS})


@require_GET
def recommendations(request, user_id):
    try:
        user = Traveler.objects.get(pk=user_id)
    except Traveler.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado."}, status=404)
    try:
        limit = int(request.GET.get("limit", "2"))
        if not 1 <= limit <= 20:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({"error": "limit debe ser un entero entre 1 y 20."}, status=400)

    packages = recommend_packages(user, limit)
    return JsonResponse({
        "user": serialize_user(user),
        "currency": "USD",
        "recommendations": [serialize_package(package, user.party_size) for package in packages],
    })
