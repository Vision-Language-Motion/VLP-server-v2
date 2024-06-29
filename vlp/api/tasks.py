from celery import shared_task
from .helpers import download_video, delete_file, create_folder_from_video_path, delete_folder_from_video_path, \
                    take_screenshot_at_second, get_video_file_clip, get_video_duration, get_video_area, \
                    search_videos_and_add_to_db, detect_video_scenes, mock_search_videos_and_add_to_db, add_keyword_to_Query
from .models import Query, Video, URL
from django.utils import timezone
from django.db.models import F,Subquery, OuterRef
from server.settings import AUTH_PASSWORD_FOR_REQUESTS, DEBUG, RAPIDAPI_KEY
from googleapiclient.errors import HttpError

import requests
import random
import string

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
            keyword.save()
        logger.warning(f"Keyword '{keyword.keyword}' queried and urls added to db")
    


@shared_task
def generate_keyword_and_add_to_query():


    gpt_url ="https://chatgpt-42.p.rapidapi.com/conversationgpt4-2"
    gpt_host ="chatgpt-42.p.rapidapi.com"
    
    meta_llm_url ="https://meta-llama-2-ai.p.rapidapi.com/"
    meta_llm_host ="https://meta-llama-2-ai.p.rapidapi.com"



    seed = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    prompt = f"Generate a list of 100 unique keywords to use for a YouTube search. Seed: {seed}. Videos should contain humans doing stuff and/or moving. Separate keywords with commas."

    payload = {
	 "messages": [
		 {
			"role": "user",
			"content": prompt
		 }
	    ],
     "system_prompt": "",
	 "temperature": 0.9,
	 "top_k": 5,
     "top_p": 0.9,
	 "max_tokens": 256,
	 "web_access": True
    } 
    headers = {
	 "x-rapidapi-key": RAPIDAPI_KEY,
	 "x-rapidapi-host": gpt_host,
	 "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(gpt_url, json=payload, headers=headers)

        if response.status_code == 200:
            api_data = response.json()
            if api_data.get('status') and api_data.get('server_code') == 1:
                result = api_data.get('result', '')
                keywords_list = [keyword.strip().lower() for keyword in result.split(',') if keyword.strip()]

                count = 0

                for keyword in keywords_list:
                   if keyword and not Query.objects.filter(keyword=keyword).exists():
                      add_keyword_to_Query(keyword)
                      count += 1

                if count > 0:
                    logger.info(f'Successfully added {count} new keywords to Query model.')
                else:
                    logger.warning('No new keywords were added.')

            else:
                logger.warning('API response status or server code is not as expected.')

        else:
            if response.status_code == 429:
                logger.error('API rate limit exceeded:' + str(e))
            else:
                logger.error(f'Failed to fetch keywords from API. Status code: {response.status_code}')

    except requests.exceptions.RequestException as e:
        logger.error(f'Error occurred while making API request: {str(e)}')

    except Exception as ex:
        logger.error(f'Unexpected error occurred: {str(ex)}')
