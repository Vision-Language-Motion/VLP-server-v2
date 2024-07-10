import os
import yt_dlp as youtube_dl
from server.settings import BASE_DIR, GOOGLE_DEV_API_KEY, DEBUG
from moviepy.editor import VideoFileClip
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from .models import URL, Query
from django.db import transaction
from googleapiclient.discovery import build
from datetime import datetime
from django.db.models import Count

import logging
logger = logging.getLogger(__name__)


# Definining download directory
download_directory = os.path.join(BASE_DIR,'youtube-downloads')


# Download
def download_video(url):
    """
    This function creates a variable ydl_opts containing how the video should be downloaded 
    and then uses the yt_dlp module to download the video into the download_directory
    """
    # ydl_opts specifies download paramter
    ydl_opts = {
        'format': 'best[height<=720]',  # best quality up to 720p
        'outtmpl': f'{download_directory}/%(id)s.%(ext)s',  # Save file as the video ID
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Ensure the video is in mp4 format
        }]
    }

    # Create a YoutubeDL object with the options
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    video_id = youtube_dl.YoutubeDL().extract_info(url, download=False)['id']
    file_path = f"{download_directory}/{video_id}.mp4"
    return file_path

# Delete 
def delete_file(file_path):
    ''' This function checks if a file (/the directory) exists and deletes it'''
    if os.path.exists(file_path):
        os.remove(file_path)

    return file_path

# Create/delete Folder
def create_folder_from_video_path(video_path):
    ''' This function creates a folder from the video path'''
    video_id = video_path.split('.')[0]
    new_video_directory = os.path.join(BASE_DIR, video_id)  # Create a new directory for the video screenshots

    if not os.path.exists(new_video_directory):
        os.makedirs(new_video_directory)

    return new_video_directory

def delete_folder_from_video_path(video_path):
    ''' This function deletes a folder from the video path'''
    video_id = video_path.split('.')[0]
    video_directory = os.path.join(BASE_DIR, video_id)

    if os.path.exists(video_directory):
        for filename in os.listdir(video_directory):
            file_path = os.path.join(video_directory, filename)
            try:
                os.unlink(file_path)  # Remove the file or link
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        os.rmdir(video_directory)

    return video_directory

# Video File clip and screenshots
def get_video_file_clip(video_path):
    ''' This function returns a VideoFileClip object from the video path'''
    video = VideoFileClip(video_path)
    return video

def take_screenshot_at_second(video : VideoFileClip, second, output_dir):
    """
    This function takes a screenshot of the video at a specific second and saves it to the output_path
    """
    output_path = f"{output_dir}/screenshot_at_second_{second}.png"

    video.save_frame(output_path, t=second)

    return output_path


def get_video_duration(video : VideoFileClip):
    """
    This function returns the duration of a video in seconds
    """
    return video.duration

def get_video_area(video : VideoFileClip):
    """
    This function returns the area of the video in pixels
    """
    return video.size[0] * video.size[1]


def detect_video_scenes(input_video_path, threshold=30.0):
    '''
    detects the scenes in a video, seperated by cuts.
    Returns a list of timestamps in seconds.
    '''

    # Open the video file
    video = open_video(input_video_path)

    # Add ContentDetector algorithm with adjustable threshold
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))

    # Perform scene detection
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    # convert list into the correct format
    formatted_scene_list = []
    for i, scene in enumerate(scene_list):
        start_time = scene[0].get_seconds()
        end_time = scene[1].get_seconds()

        if (end_time - start_time) < 2:
            continue

        formatted_scene_list.append([start_time, end_time])
    
    return formatted_scene_list



def add_urls_to_db(urls, query=None):
    # Fetch existing URLs
    existing_urls = URL.objects.filter(url__in=urls).values_list('url', flat=True)

    # Determine new URLs to be added
    new_urls = set([url for url in urls if url not in existing_urls]) # set for no duplicates

    if query:
        # Fetch the query object
        query_obj = Query.objects.get(keyword=query)

        # Bulk create new URL objects with the query
        with transaction.atomic():
            URL.objects.bulk_create([URL(url=url, came_from_keyword=query_obj) for url in new_urls])
    else:
        # Bulk create new URL objects
        with transaction.atomic():
            URL.objects.bulk_create([URL(url=url) for url in new_urls])

    # Fetch all URLs after insertion
    # all_urls = URL.objects.filter(url__in=urls)
    # response_data = [{'id': url.id, 'url': url.url} for url in all_urls]


def add_url_to_db(url, query=None):
    add_urls_to_db([url], query=query)


def mock_search_videos_and_add_to_db(query, video_amount = 50):
    '''
    This function mocks the search_videos_and_add_to_db function
    '''
    pass


if not DEBUG:
    # Create a service object for interacting with the API
    youtube = build('youtube', 'v3', developerKey = GOOGLE_DEV_API_KEY)

    def search_videos_and_add_to_db(query, video_amount = 50):
        '''
        Accepts a query and video_amount (default: 50) to use the youtube API to search for videos 
        and then fills them into the URL model as unprocessed videos
        '''

        # Make a request to the API's search.list method to retrieve videos
        request = youtube.search().list(
            part ='snippet',
            q = query,
            type = 'video',
            maxResults = video_amount
        )
        
        response = request.execute()
        
    # Adding the Urls into the URL model
        for item in response['items']:
            add_url_to_db(f"https://www.youtube.com/watch?v={item['id']['videoId']}", query=query)

else:
    def search_videos_and_add_to_db(query, video_amount = 50):
        '''
        This function mocks the search_videos_and_add_to_db function
        '''
        print("MOCK SEARCH")
        pass

def add_keyword_to_Query(Keyword):
    '''
    This function adds an Keyword to the Query model 
    (default: use_counter = 0, quality metric = 0)
    '''
    keyword_instance, created = Query.objects.get_or_create(keyword=Keyword, defaults={"last_processed": datetime(1, 1, 1, 0, 0)})

def remove_keyword_from_Query(keyword):
    '''
    This function removes a keyword from the Query model.
    '''
    try:
        # Try to get the keyword instance from the Query model
        keyword_instance = Query.objects.get(keyword=keyword)
        # If found, delete the instance
        keyword_instance.delete()
    except Query.DoesNotExist:
        # If the keyword does not exist in the Query model, do nothing 
        pass


def delete_duplicates_from_model(model,fields = []):
    """
    Delete duplicate records from the given model based on specified fields.

    Parameters:
    model (Django model class): The model class to remove duplicates from.
    fields (list of str): The list of fields to check for duplicates.
    """
    if not fields:
     logger.warn("No fields Specified")
     return
    
    duplicates = (model.objects
                 .values(*fields)
                 .annotate(count=Count('id'))
                 .filter(count__gt=1))
    
    logger.warn("Duplicates:", duplicates)
    ids_to_delete = []
    for duplicate in duplicates:
        # Get IDs of records to delete (all except the first one)
        ids_to_delete = (model.objects
                         .filter(**{field: duplicate[field] for field in fields})
                         .order_by('id')
                         .values_list('id', flat=True)[1:])
     
    if ids_to_delete:
        logger.warn("ids_to_delete:", ids_to_delete)
        logger.warn("model instance:", model.objects.filter(id__in=ids_to_delete))
        # model.objects.filter(id__in=ids_to_delete).delete()
    else:
        logger.warn("No duplicates found", duplicates)