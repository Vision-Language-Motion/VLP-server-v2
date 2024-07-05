import os
import yt_dlp as youtube_dl
from server.settings import BASE_DIR, GOOGLE_DEV_API_KEY, DEBUG
from moviepy.editor import VideoFileClip
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from .models import URL, Query, VideoTimeStamps, Prediction
from django.db import transaction
from django.db.models import Max
from googleapiclient.discovery import build
from datetime import datetime


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

SINGLE_HIGH_WEIGHT = 1
SINGLE_MEDIUM_WEIGHT = 0.7
SINGLE_LOW_WEIGHT = 0.3
MULTIPLE_WEIGHT = 0.7

def calculate_keyword_metrics(keywords=[]):
    '''
    This function calculates the quality metric for a given list or all keywords
    input: limited list of keywords (default or empty list calculates all keywords)
    '''
    keywords = [keyword.lower().strip() for keyword in keywords] # normalize keywords
    # Step 1: Filter queries based on provided keywords or select all queries if keywords is none or empty
    if keywords:
        queries = Query.objects.filter(keyword__in=keywords)
    else:
        queries = Query.objects.all()

    for query in queries:
        if query.use_counter == 0:
            # Skip queries with no use_counter
            continue
        urls = URL.objects.filter(came_from_keyword=query)
        total_video_length = 0
        weighted_usable_material = 0

        for url in urls:
            if url.is_processed == False:
                continue
            video_timestamps = VideoTimeStamps.objects.filter(video=url)
            
            if not video_timestamps.exists():
                continue

            # Get the total video length using the end time of the last timestamp
            total_video_length = video_timestamps.aggregate(
                max_end_time=Max('end_time')
            )['max_end_time'] or 0

            # Get all predictions and calculate the weighted usable material
            for timestamp in video_timestamps:
                prediction = Prediction.objects.filter(video_timestamp=timestamp).first()
                
                #prediction switch case:
                if prediction:
                    if prediction.prediction == 'sh':
                        weight = SINGLE_HIGH_WEIGHT
                    elif prediction.prediction == 'sm':
                        weight = SINGLE_MEDIUM_WEIGHT
                    elif prediction.prediction == 'sl':
                        weight = SINGLE_LOW_WEIGHT
                    elif prediction.prediction == 'mu':
                        weight = MULTIPLE_WEIGHT
                    else:
                        weight = 0

                    segment_length = timestamp.end_time - timestamp.start_time
                    weighted_usable_material += segment_length * weight

        # Calculate the final quality metric for the query, adjust if necessary
        if total_video_length > 0:
            quality_metric = weighted_usable_material / total_video_length
        else:
            quality_metric = 0

        # Update the query's quality_metric field
        query.quality_metric = quality_metric
        #output to log
        print(f"Quality metric for keyword '{query.keyword}' is {quality_metric}")
        query.save(update_fields=['quality_metric'])

    print("Quality metrics updated for specified keywords.")

def generate_new_keywords():
    '''
    This function generates the new keywords and adds them to the Query model
    '''
    pass