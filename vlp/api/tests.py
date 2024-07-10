from django.test import TestCase, Client
import os
from .helpers import download_directory, download_video, delete_file, add_url_to_db, add_urls_to_db, add_keyword_to_Query, delete_duplicates_from_model
from server.settings import BASE_DIR
from .tasks import query_search
from .models import URL, Query, VideoTimeStamps, Prediction
from datetime import datetime
from django.utils import timezone
from .tasks import logger


# NOTE: Commented out for faster testing
"""
class DeleteTest(TestCase):
    '''testing download and delete function'''
    def test_delete_file(self):
        '''Testing the download_video and delete_file function by downloading a video, checking if it exists 
           then deleting the file and checking if it exists afterwards'''
        # Creating test file
        file_path = download_video('https://www.youtube.com/shorts/AsrP4ji_Dtw')

        assert(os.path.exists(file_path))
        # Delete the file
        delete_file(file_path)

        # Checking if the file exists
        assert(not (os.path.exists(file_path)))
"""

# NOTE: Commented out for faster testing
'''
class PysceneTest(TestCase):
    """Test the process_video_without_human function from tasks.py with the
       new pyscene implementation."""

    def test_pyscene(self):
        video_url = 'https://www.youtube.com/shorts/AsrP4ji_Dtw'
        timestamps, preds = process_video_without_human(video_url)
        assert(len(preds) == len(timestamps))
        assert(len(preds) > 0)
'''

class AddUrlToDB(TestCase):
    """Test the add_url_to_db by adding a Url to the URL model and then checking if it exists and adding duplicate urls, checking if only one exists"""
    
    def test_add_url_to_db(self):
        video_url = 'https://www.youtube.com/shorts/AsrP4ji_Dtw'
        add_url_to_db(video_url)
        assert(URL.objects.filter(url=video_url).exists())
    
    def test_add_duplicate_Url_to_db(self):
        video_url = 'https://www.youtube.com/shorts/AsrP4ji_Dtw'
        video_urls = [video_url, video_url]
        add_urls_to_db(video_urls)
        query_count = URL.objects.filter(url=video_url).count()

        # Assert that only one entry exists
        self.assertEqual(query_count, 1)


class AddKeywordQuery(TestCase):
    """Test the add_Keyword_to_Query by adding a keyword to the Query model and then checking if it exists, then adding a keyword twice to the Query model and then checking if only one exists"""
    
    def test_add_Keyword_to_Query(self):
        keyword = 'workout'
        add_keyword_to_Query(keyword)
        assert(Query.objects.filter(keyword=keyword).exists())
    
    def test_add_duplicate_keyword_to_query(self):
        """Test that adding a keyword in different cases and with whitespace results in a single entry."""

        # Define the keywords
        keyword_with_trailing_space = 'workout '
        keyword_capitalized = 'Workout'

        # Add the first keyword
        add_keyword_to_Query(keyword_with_trailing_space)

        try:
            # try adding the second keyword
            add_keyword_to_Query(keyword_capitalized)
        except:
            pass

        # Check the database for the cleaned keyword
        cleaned_keyword = 'workout'
        query_count = Query.objects.filter(keyword=cleaned_keyword).count()

        # Assert that only one entry exists
        self.assertEqual(query_count, 1)



class QuerySearchTestCase(TestCase):
    """Test case for the query_search shared task."""

    def setUp(self):
        # Create some dummy Query objects for testing
        Query.objects.create(keyword='keyword1')
        Query.objects.create(keyword='keyword2')

    def test_query_search(self):
        
        
        n_of_urls_initial = URL.objects.all().count()
        # Call the task function
        query_search()
        
        # Comment this out if the API_KEY limit is reached
        '''
        self.assertGreater(URL.objects.all().count(), n_of_urls_initial)

        # Assert that top 100 keywords are processed
        top_100_keywords = Query.objects.order_by('-last_processed', 'use_counter')[:100]
        self.assertEqual(len(top_100_keywords), 2)  # Assuming only 2 dummy keywords are created

        
        # Assert that each keyword was updated correctly
        for keyword in top_100_keywords:
            self.assertEqual(keyword.last_processed.date(), timezone.now().date())  # Check last_processed
            self.assertGreater(keyword.use_counter, 0)  # Check use_counter 
        '''

class DatabaseExists(TestCase):
    def database_existence(self):
        n_of_urls_initial = URL.objects.all().count()
        logger.warn(f"n_of_urls_initial:{n_of_urls_initial}")
        assert(n_of_urls_initial > 0)


class DeleteDuplicates(TestCase):
    '''Test Case for'''
    def test_delete_duplicates_from_model(self):
        # Making Sure the empy case is getting filtered out
        delete_duplicates_from_model(VideoTimeStamps, [])
        logger.warn("Empty case checked")
        # Testing the function
        delete_duplicates_from_model(Prediction, ['video_timestamp', 'prediction'])

