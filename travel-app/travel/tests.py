from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import Accommodation, Flight, Traveler, validate_vector
from .recommendations import cosine_similarity, recommend_packages


class RecommendationTests(TestCase):
    def setUp(self):
        self.start = timezone.localdate() + timedelta(days=30)
        self.user = Traveler.objects.create(
            id="ana", name="Ana", origin="MDE", party_size=2,
            max_price_per_person_usd=Decimal("500.00"), vector={"playa": 1},
        )
        self.stay = Accommodation.objects.create(
            id="playa", name="Escapada al mar", hotel="Hotel demo", airport="CTG",
            destination="Cartagena", description="Alojamiento de prueba junto al mar.", check_in=self.start,
            check_out=self.start + timedelta(days=3), max_people=2,
            price_per_person_usd="300.00", vector={"playa": 1},
        )
        departure = timezone.make_aware(datetime.combine(self.start, datetime.min.time())) + timedelta(hours=9)
        self.outbound = Flight.objects.create(
            id="ida", origin="MDE", destination="CTG", airline="Demo", flight_number="DM1", cabin="Económica",
            departure_at=departure, arrival_at=departure + timedelta(hours=1),
            price_per_person_usd="100.00", available_seats=2, vector={"playa": 1},
        )
        returning = departure + timedelta(days=3, hours=8)
        self.inbound = Flight.objects.create(
            id="vuelta", origin="CTG", destination="MDE", airline="Demo", flight_number="DM2", cabin="Económica",
            departure_at=returning, arrival_at=returning + timedelta(hours=1),
            price_per_person_usd="100.00", available_seats=2, vector={"playa": 1},
        )

    def test_package_has_one_stay_and_round_trip_at_budget_boundary(self):
        response = self.client.get("/api/users/ana/recommendations/")
        self.assertEqual(response.status_code, 200)
        package, = response.json()["recommendations"]
        self.assertEqual(package["accommodation"]["id"], "playa")
        self.assertEqual(package["outbound_flight"]["id"], "ida")
        self.assertEqual(package["return_flight"]["id"], "vuelta")
        self.assertEqual(package["price_per_person_usd"], "500.00")
        self.assertEqual(package["total_price_usd"], "1000.00")
        self.assertEqual(package["nights"], 3)
        self.assertEqual(package["score"], 1)
        self.assertEqual(package["accommodation"]["vector"], {"playa": 1})
        self.assertEqual(package["outbound_flight"]["vector"], {"playa": 1})
        self.assertEqual(package["return_flight"]["vector"], {"playa": 1})
        self.assertEqual(package["vector"]["playa"], 1)

    def test_budget_counts_both_flights_and_entire_stay(self):
        self.user.max_price_per_person_usd = Decimal("499.99")
        self.assertEqual(recommend_packages(self.user), [])

    def test_capacity_required_in_each_component(self):
        for component, field in [(self.stay, "max_people"), (self.outbound, "available_seats"), (self.inbound, "available_seats")]:
            with self.subTest(component=component.pk):
                setattr(component, field, 1)
                component.save()
                self.assertEqual(recommend_packages(self.user), [])
                setattr(component, field, 2)
                component.save()

    def test_routes_must_connect_to_user_and_hotel(self):
        for flight, field in [(self.outbound, "origin"), (self.outbound, "destination"), (self.inbound, "origin"), (self.inbound, "destination")]:
            with self.subTest(flight=flight.pk, field=field):
                original = getattr(flight, field)
                setattr(flight, field, "BOG")
                flight.save()
                self.assertEqual(recommend_packages(self.user), [])
                setattr(flight, field, original)
                flight.save()

    def test_dates_must_match_check_in_and_check_out(self):
        for flight in [self.outbound, self.inbound]:
            with self.subTest(flight=flight.pk):
                flight.departure_at += timedelta(days=1)
                flight.arrival_at += timedelta(days=1)
                flight.save()
                self.assertEqual(recommend_packages(self.user), [])
                flight.departure_at -= timedelta(days=1)
                flight.arrival_at -= timedelta(days=1)
                flight.save()

    def test_past_inventory_is_excluded(self):
        self.stay.check_in -= timedelta(days=60)
        self.stay.check_out -= timedelta(days=60)
        self.stay.save()
        for flight in [self.outbound, self.inbound]:
            flight.departure_at -= timedelta(days=60)
            flight.arrival_at -= timedelta(days=60)
            flight.save()
        self.assertEqual(recommend_packages(self.user), [])

    def test_missing_return_is_not_a_package(self):
        self.inbound.delete()
        self.assertEqual(recommend_packages(self.user), [])

    def test_combines_alternative_flights_and_sorts_by_affinity_then_price(self):
        self.outbound.pk = "otra-ida"
        self.outbound.vector = {"aventura": 1}
        self.outbound.price_per_person_usd = Decimal("50.00")
        self.outbound.save()
        results = recommend_packages(self.user)
        self.assertEqual([item.outbound.pk for item in results], ["ida", "otra-ida"])
        self.outbound.vector = {"playa": 1}
        self.outbound.save()
        self.assertEqual(recommend_packages(self.user, limit=1)[0].outbound.pk, "otra-ida")

    def test_money_keeps_decimal_precision(self):
        self.stay.price_per_person_usd = Decimal("299.99")
        self.stay.save()
        self.assertEqual(recommend_packages(self.user)[0].price_per_person_usd, Decimal("499.99"))

    def test_empty_results_are_successful(self):
        self.stay.delete()
        response = self.client.get("/api/users/ana/recommendations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recommendations"], [])

    def test_invalid_limit_and_unknown_user(self):
        for limit in ["0", "-1", "21", "1.5", "abc", ""]:
            with self.subTest(limit=limit):
                response = self.client.get("/api/users/ana/recommendations/", {"limit": limit})
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json())
        self.assertEqual(self.client.get("/api/users/unknown/recommendations/").status_code, 404)

    def test_read_only_api(self):
        self.assertEqual(self.client.post("/api/users/").status_code, 405)
        self.assertEqual(self.client.post("/api/users/ana/recommendations/").status_code, 405)

    def test_vector_validation_and_zero_vector(self):
        self.assertEqual(cosine_similarity({}, {"playa": 1}), 0)
        self.assertEqual(cosine_similarity({"playa": 1}, {"lujo": 1}), 0)
        for vector in [{"playa": float("nan")}, {"playa": -1}, {"other": 1}, {"playa": True}, [1, 2]]:
            with self.subTest(vector=vector), self.assertRaises(ValidationError):
                validate_vector(vector)

    def test_invalid_inventory_is_rejected_by_model_validation(self):
        self.outbound.full_clean()
        self.stay.full_clean()
        self.outbound.arrival_at = self.outbound.departure_at
        with self.assertRaises(ValidationError):
            self.outbound.full_clean()
        self.stay.check_out = self.stay.check_in
        with self.assertRaises(ValidationError):
            self.stay.full_clean()


class DemoTests(TestCase):
    def test_seed_is_repeatable_and_profiles_receive_distinct_recommendations(self):
        for _ in range(2):
            call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Traveler.objects.count(), 3)
        self.assertEqual(Accommodation.objects.count(), 6)
        self.assertEqual(Flight.objects.count(), 12)
        response = self.client.get("/api/users/")
        self.assertEqual(len(response.json()["users"]), 3)
        expected = {"camila": "cartagena_premium", "diego": "santa_marta_grupo", "sofia": "san_gil_aventura"}
        for user_id, stay_id in expected.items():
            with self.subTest(user=user_id):
                packages = self.client.get(f"/api/users/{user_id}/recommendations/").json()["recommendations"]
                self.assertEqual(len(packages), 2)
                self.assertEqual(packages[0]["accommodation"]["id"], stay_id)
