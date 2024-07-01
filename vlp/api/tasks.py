from celery import shared_task
from .helpers import download_video, delete_file, create_folder_from_video_path, delete_folder_from_video_path, \
                    take_screenshot_at_second, get_video_file_clip, get_video_duration, get_video_area, \
                    search_videos_and_add_to_db, detect_video_scenes, mock_search_videos_and_add_to_db
from .models import Query, Video, URL
from django.utils import timezone
from django.db.models import F,Subquery, OuterRef
from server.settings import AUTH_PASSWORD_FOR_REQUESTS, DEBUG
from googleapiclient.errors import HttpError


import logging
logger = logging.getLogger(__name__)


@shared_task
def query_search():
    logger.warn("Searching for videos with  first 100 Keywords in Query")
    # Subquery to get the top 100 keywords' IDs
    top_100_keywords = Query.objects.order_by('-last_processed', 'use_counter')[:100]
    logger.warning(top_100_keywords)
    logger.warning("Subquery with top 100 Keywords")
    for keyword in top_100_keywords:
        try:
            if DEBUG:
                mock_search_videos_and_add_to_db(keyword.keyword)
                print("Mock search")
            else:
                search_videos_and_add_to_db(keyword.keyword)

        except HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                logger.warning("YouTube API quota exceeded: " + str(e))
                break
            else:
                # Handle other HttpErrors
                logger.warning("HTTP error: " + str(e))
                break
        # Updating keyword in query
        if not DEBUG:
            keyword.update_used_keyword()
            keyword.save()  # I think we can delete this line
        logger.warning(f"Keyword '{keyword.keyword}' queried and urls added to db")
    