from django.test import TestCase, Client
import os
from .helpers import download_directory, download_video, delete_file, add_url_to_db, add_urls_to_db, add_keyword_to_Query, calculate_keyword_metrics \
    , SINGLE_LOW_WEIGHT, SINGLE_MEDIUM_WEIGHT, SINGLE_HIGH_WEIGHT, MULTIPLE_WEIGHT
from server.settings import BASE_DIR
from .tasks import query_search #, generate_keyword_and_add_to_query
from .models import URL, Query, Prediction, VideoTimeStamps, Video
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

'''
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
'''


class QuerySearchTestCase(TestCase):
    """Test case for the query_search shared task."""

    def setUp(self):
        # Create some dummy Query objects for testing
        Query.objects.create(keyword='keyword1')
        Query.objects.create(keyword='keyword2')

    def test_query_search(self):
        
        
        n_of_urls_initial = URL.objects.all().count()
        # Call the task function
        # query_search()
        
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
    def URL_existence(self):
        n_of_urls = URL.objects.all().count()
        logger.warn(f"n_of_urls_initial:{n_of_urls}")
        assert(n_of_urls > 0)
    
    def Query_existence(self):
        n_of_keywords = Query.objects.all().count()
        logger.warn(f"n_of_urls_initial:{n_of_keywords}")
        assert(n_of_keywords > 0)

'''
class GenerateKeywords(TestCase):
    def test_generate_keyword_and_add_to_query(self):
        
        before_top_100_keywords = Query.objects.order_by('-last_processed', 'use_counter')[:100]
        n_of_keywords_initial = Query.objects.all().count()

        generate_keyword_and_add_to_query()

        self.assertGreater(Query.objects.all().count(), n_of_keywords_initial)
        after_top_100_keywords = Query.objects.order_by('-last_processed', 'use_counter')[:100]
        assert before_top_100_keywords != after_top_100_keywords, "Querysets are not different"
'''

class QueryQualityMetric(TestCase):
    '''Tests the quality_metric calculation in the Query model'''
    # i.e. creates a dummy keyword, linked dummy url, video and prediction with one timestamp for the whole video, uses calculate_keyword_metrics and checks the quality_metric and outputs to log
    def test_quality_metric(self):
        # Create a dummy keyword
        keyword = 'workout'
        add_keyword_to_Query(keyword)
        # Create a dummy URL
        video_url = 'https://www.youtube.com/shorts/AsrP4ji_Dtw'
        add_url_to_db(video_url, query=keyword)
        url = URL.objects.get(url=video_url)
        # Create a dummy video
        video = Video.objects.create(url=url)
        # Create two dummy timestamps
        VideoTimeStamps.objects.create(video=url, start_time=0, end_time=100)
        VideoTimeStamps.objects.create(video=url, start_time=100, end_time=200)
        # Create dummy predictions
        Prediction.objects.create(video_timestamp=VideoTimeStamps.objects.get(video=url, start_time=0, end_time=100), prediction='sh')
        Prediction.objects.create(video_timestamp=VideoTimeStamps.objects.get(video=url, start_time=100, end_time=200), prediction='sl')
        # Calculate the quality_metric
        calculate_keyword_metrics([keyword])
        # Log the quality_metric
        logger.warn(f"Quality metric for keyword '{keyword}': {Query.objects.get(keyword=keyword).quality_metric}")
        # Assert that the quality_metric is as expected, consider floating point error
        self.assertLess(Query.objects.get(keyword=keyword).quality_metric, 0.651)
        self.assertGreater(Query.objects.get(keyword=keyword).quality_metric, 0.649)

