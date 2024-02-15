from rest_framework import serializers

from core.models import Info


class BaseCardSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ['title', 'description', 'active', 'url', 'url_display']


class InfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Info
        fields = ['title', 'description']
