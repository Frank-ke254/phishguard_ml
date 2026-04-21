from django.urls import path

from .views import BatchPredictView, HealthView, PredictView


urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("predict/", PredictView.as_view(), name="predict"),
    path("batch-predict/", BatchPredictView.as_view(), name="batch-predict"),
]
