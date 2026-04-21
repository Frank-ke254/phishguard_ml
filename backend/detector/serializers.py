from rest_framework import serializers


class PredictRequestSerializer(serializers.Serializer):
    url = serializers.URLField(
        max_length=2048,
        error_messages={
            "invalid": "Enter a valid URL starting with http:// or https://.",
            "blank": "URL cannot be empty.",
            "required": "URL is required.",
        },
    )

    def validate_url(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("URL cannot be empty.")
        return cleaned


class BatchPredictRequestSerializer(serializers.Serializer):
    urls = serializers.ListField(
        child=serializers.URLField(
            max_length=2048,
            error_messages={
                "invalid": "Each URL must start with http:// or https://.",
            },
        ),
        allow_empty=False,
        max_length=200,
    )

    def validate_urls(self, value: list[str]) -> list[str]:
        cleaned = [url.strip() for url in value if url and url.strip()]
        if not cleaned:
            raise serializers.ValidationError("At least one URL is required.")
        return cleaned
