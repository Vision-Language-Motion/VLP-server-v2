from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Video, Query
from .forms import FileUploadForm
from .serializers import VideoSerializer
from .helpers import add_keyword_to_Query
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from datetime import datetime


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

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