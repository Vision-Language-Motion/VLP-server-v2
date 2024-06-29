from dotenv import load_dotenv
import os
import yt_dlp as youtube_dl
import psycopg2
from psycopg2.extras import execute_values
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
load_dotenv()


# Database connection parameters
db_params = {
    'dbname': 'defaultdb',
    'user': 'doadmin',
    'password': os.environ.get('DO_DATABASE_PASSWORD', None),
    'host': 'vlp-database-docker-do-user-10555764-0.c.db.ondigitalocean.com',
    'port': '25060'
}

def get_table_names():
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Query to get all table names
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """

        # Execute the query
        cursor.execute(query)

        # Fetch all table names
        tables = cursor.fetchall()

        # Print the table names
        for table in tables:
            print(table[0])

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


def connect_and_retrieve(query):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query)

        # Fetch all rows from the executed query
        rows = cursor.fetchall()

        # Print the retrieved data
        for row in rows:
            print(row)

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()

def get_unprocessed_rows():
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Query to get rows where is_processed is False
        query = """
        SELECT * FROM api_url
        WHERE is_processed = FALSE
        """

        # Execute the query
        cursor.execute(query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Print the rows
        for row in rows:
            print(row)

        return rows

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


def get_all_rows():
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Query to get rows where is_processed is False
        query = """
        SELECT * FROM api_url
        """

        # Execute the query
        cursor.execute(query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Print the rows
        for row in rows:
            print(row)

        return rows

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


def update_processed_rows():
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Update query to set is_processed to True
        update_query = """
        UPDATE api_url
        SET is_processed = TRUE
        WHERE is_processed = FALSE
        """

        # Execute the update query
        cursor.execute(update_query)

        # Commit the transaction
        connection.commit()

        print(f"{cursor.rowcount} rows updated to is_processed = True")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


def update_processed_rows_by_url(url):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Update query to set is_processed to True
        update_query = """
        UPDATE api_url
        SET is_processed = TRUE
        WHERE url = (%s)
        """ 

        # Execute the update query
        cursor.execute(update_query, (url,))

        # Commit the transaction
        connection.commit()

        print(f"{cursor.rowcount} rows updated to is_processed = True")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()

def add_new_url(youtube_url):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # SQL query to insert a new record
        insert_query = """
        INSERT INTO api_url (url, is_processed)
        VALUES (%s, %s)
        """
        # Values to be inserted
        values = (youtube_url, False)

        # Execute the insert query
        cursor.execute(insert_query, values)

        # Commit the transaction
        connection.commit()

        print("New URL added successfully")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()



# Download
def download_video(url):
    """
    This function creates a variable ydl_opts containing how the video should be downloaded 
    and then uses the yt_dlp module to download the video into the download_directory
    """
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

def make_test_url_false():
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Query to get rows where is_processed is False
        query = """
        UPDATE api_url
        SET is_processed = FALSE
        WHERE url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        """

        # Execute the query
        cursor.execute(query)

        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


def add_timestamp(video_id, start_time, end_time):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # SQL query to insert a new timestamp
        insert_query = """
        INSERT INTO api_videotimestamps (video_id, start_time, end_time)
        VALUES (%s, %s, %s)
        """
        # Values to be inserted
        values = (video_id, start_time, end_time)

        # Execute the insert query
        cursor.execute(insert_query, values)

        # Commit the transaction
        connection.commit()

        print("Timestamp added successfully")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


# Video Analysis
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

        formatted_scene_list.append([start_time, end_time])
    
    return formatted_scene_list

def add_multiple_timestamps(video_id, scenes):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Check if there are existing timestamps for the video
        check_query = """
        SELECT 1 FROM api_videotimestamps
        WHERE video_id = %s
        LIMIT 1
        """
        cursor.execute(check_query, (video_id,))
        if cursor.fetchone():
            print("Timestamps already exist for this video. Exiting.")
            return

        # SQL query to insert multiple timestamps
        insert_query = """
        INSERT INTO api_videotimestamps (video_id, start_time, end_time)
        VALUES %s
        """
        # Create a list of tuples for the values to be inserted
        values = [(video_id, scene[0], scene[1]) for scene in scenes]

        # Use psycopg2's execute_values for efficient bulk insert
        execute_values(cursor, insert_query, values)

        # Commit the transaction
        connection.commit()

        print("Timestamps added successfully")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


def fetch_timestamps(print_output=False):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # SQL query to fetch timestamps for a given video ID
        fetch_query = """
        SELECT * 
        FROM api_videotimestamps
        """
        # Execute the fetch query
        cursor.execute(fetch_query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Print the rows
        if print_output:
            for row in rows:
                print(f"Video Id {row[3]}, Start Time: {row[1]}, End Time: {row[2]}")
        return rows
    
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


if __name__ == "__main__":
    # Definining download directory
    download_directory = os.path.join(os.getcwd(), 'youtube-downloads')
    os.makedirs(download_directory, exist_ok=True)

    #new_youtube_url = 'https://www.youtube.com/shorts/MkzFodsSOHc'  # insert url here
    #add_new_url(new_youtube_url)
    # make_test_url_false()
    rows = get_all_rows()
    print(rows)