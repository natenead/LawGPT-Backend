from rest_framework import serializers


class TextSerializers(serializers.Serializer):
    text = serializers.CharField()
