from rest_framework import serializers
from .models import Video
from server.settings import AUTH_PASSWORD_FOR_REQUESTS

class VideoSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Video
        fields = ['url', 'keywords', 'human_presence', 'visibility', 'password']
        extra_kwargs = {
            'visibility': {'required': False},  # Since visibility is optional
            'human_presence': {'required': False},  # Since human_presence is optional
            'keywords': {'required': False}  # Since keywords is optional
        }

    def validate_visibility(self, value):
        """
        Check that visibility is provided when human_presence is 'Single'.
        """
        data = self.initial_data
        if data['human_presence'] == 'S' and not value:
            raise serializers.ValidationError("Visibility must be set when human presence is 'Single'.")
        return value

    
    def create(self, validated_data):
        """
        Check that the provided password matches the required password.
        """
        password = self.initial_data.get('password', None)
        if password != AUTH_PASSWORD_FOR_REQUESTS:
            raise serializers.ValidationError("Invalid password.")
        validated_data.pop('password', None)  
        return super().create(validated_data)
