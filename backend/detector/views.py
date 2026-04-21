from pathlib import Path

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .predictor import FEATURES_PATH, MODEL_PATH, Predictor
from .serializers import BatchPredictRequestSerializer, PredictRequestSerializer


_PREDICTOR: Predictor | None = None


def get_predictor() -> Predictor:
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = Predictor()
    return _PREDICTOR


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "model_loaded": Path(MODEL_PATH).exists() and Path(FEATURES_PATH).exists(),
            }
        )


class PredictView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PredictRequestSerializer(data=request.data)
        if not serializer.is_valid():
            field_errors = {
                field: errors[0] if isinstance(errors, list) and errors else "Invalid value."
                for field, errors in serializer.errors.items()
            }
            return Response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Please correct the highlighted input and try again.",
                        "fields": field_errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        url = serializer.validated_data["url"]

        if not (MODEL_PATH.exists() and FEATURES_PATH.exists()):
            return Response(
                {
                    "error": {
                        "code": "model_unavailable",
                        "message": "Model artifacts not found. Run `python model/train_model.py` first.",
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            result = get_predictor().predict_url(url)
        except Exception:
            return Response(
                {
                    "error": {
                        "code": "prediction_failed",
                        "message": "Prediction failed due to an internal error.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(result, status=status.HTTP_200_OK)


class BatchPredictView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = BatchPredictRequestSerializer(data=request.data)
        if not serializer.is_valid():
            field_errors = {
                field: errors[0] if isinstance(errors, list) and errors else "Invalid value."
                for field, errors in serializer.errors.items()
            }
            return Response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Please correct the highlighted input and try again.",
                        "fields": field_errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (MODEL_PATH.exists() and FEATURES_PATH.exists()):
            return Response(
                {
                    "error": {
                        "code": "model_unavailable",
                        "message": "Model artifacts not found. Run `python model/train_model.py` first.",
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        urls = serializer.validated_data["urls"]
        try:
            result = get_predictor().predict_batch(urls)
        except Exception:
            return Response(
                {
                    "error": {
                        "code": "prediction_failed",
                        "message": "Batch prediction failed due to an internal error.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(result, status=status.HTTP_200_OK)
