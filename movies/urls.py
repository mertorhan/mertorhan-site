from django.urls import path

from . import views

urlpatterns = [
    path("", views.review_list, name="review_list"),
    path("<slug:slug>/", views.review_detail, name="review_detail"),
]