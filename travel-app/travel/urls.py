from django.urls import path

from . import views

urlpatterns = [
    path("users/", views.users, name="users"),
    path("users/<slug:user_id>/recommendations/", views.recommendations, name="recommendations"),
]
