from rest_framework import serializers
from .models import Video, VideoTimeStamps, Prediction, Query, URL
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
    
class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = ['keyword', 'last_processed', 'use_counter', 'quality_metric']
        read_only_fields = ['last_processed', 'use_counter', 'quality_metric']

class VideoTimeStampsSerializer(serializers.ModelSerializer):
    video_url = serializers.CharField(source='video.url', read_only=True)
    class Meta:
        model = VideoTimeStamps
        fields = ['video_url', 'start_time', 'end_time']

class PredictionSerializer(serializers.ModelSerializer):
    video_timestamp = VideoTimeStampsSerializer()

    class Meta:
        model = Prediction
        fields = ['video_timestamp', 'prediction']

class CustomVideoTimeStampsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoTimeStamps
        fields = ['start_time', 'end_time']

class CustomPredictionSerializer(serializers.ModelSerializer):
    video_timestamp = CustomVideoTimeStampsSerializer()

    class Meta:
        model = Prediction
        fields = ['video_timestamp', 'prediction']

class GroupedPredictionSerializer(serializers.ModelSerializer):
    video_url = serializers.CharField(source='video.url', read_only=True)
    predictions = serializers.SerializerMethodField()

    class Meta:
        model = VideoTimeStamps
        fields = ['video_url', 'predictions']

    def get_predictions(self, obj):
        video_timestamps = VideoTimeStamps.objects.filter(video=obj.video)
        predictions = Prediction.objects.filter(video_timestamp__in=video_timestamps)
        return CustomPredictionSerializer(predictions, many=True).data

class URLSerializer(serializers.ModelSerializer):
    class Meta:
        model = URL
        fields = ['url', 'is_processed', 'came_from_keyword']