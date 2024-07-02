from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Video, Query, Prediction, VideoTimeStamps
from .forms import FileUploadForm
from .serializers import VideoSerializer, PredictionSerializer, QuerySerializer, VideoTimeStampsSerializer, GroupedPredictionSerializer
from .helpers import add_keyword_to_Query
from django.db.models import Prefetch
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from datetime import datetime


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    pagination_class = PageNumberPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # Process uploaded file to extract keywords
            keywords_list = extract_keywords_from_file(uploaded_file)

            # Save keywords to Query model
            for keyword in keywords_list:
                keyword = keyword.strip().lower()  # Ensure to strip whitespace, forces lowercase for no case sensitive duplicates
                if keyword:  # Only process non-empty keywords
                    add_keyword_to_Query(keyword)
                    
    else:
        form = FileUploadForm()

    return render(request, 'upload_file.html', {'form': form})

def extract_keywords_from_file(uploaded_file):
    content = uploaded_file.read().decode('utf-8')
    keywords = content.split(',')  # Split content into keywords (assuming comma-separated)
    return keywords

class QueryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer
    pagination_class = PageNumberPagination

class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    pagination_class = PageNumberPagination

class TimeStampViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VideoTimeStamps.objects.all()
    serializer_class = VideoTimeStampsSerializer
    pagination_class = PageNumberPagination

class GroupedPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GroupedPredictionSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        # Fetch unique video timestamps, ensuring each has a related video
        return VideoTimeStamps.objects.select_related('video').distinct('video')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)