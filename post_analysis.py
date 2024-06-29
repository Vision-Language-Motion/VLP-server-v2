from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import execute_values
load_dotenv()
import csv


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

def insert_csv_file_in_db(filepath="./output/predictions.csv"):
    try:
        with open(filepath, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                video_id = row['Video Name']
                start_time = float(row['Start Time (s)'])
                end_time = float(row['End Time (s)'])
                prediction = row['Classification']
                insert_prediction_to_db(video_id, start_time, end_time, prediction)

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL or the file does not exist: {error}")


def fetch_urls(print_output=False):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # SQL query to fetch URLs
        fetch_query = """
        SELECT * 
        FROM api_url
        """
        # Execute the fetch query
        cursor.execute(fetch_query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Print the rows
        if print_output:
            for row in rows:
                print(f"URL: {row[1]}")
        return rows
    
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


def insert_prediction_to_db(video_id, start_time, end_time, prediction):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Execute the query
        cursor.execute("SELECT id FROM api_URL WHERE url LIKE %s", ('%' + video_id + '%',))
        video_url_result = cursor.fetchone()

        if not video_url_result:
            print("Video URL not found.")
            return
        
        video_url_id = video_url_result[0]
         # Step 2: Find the corresponding VideoTimeStamps ID
        cursor.execute(
            "SELECT id FROM api_VideoTimeStamps WHERE video_id = %s AND start_time = %s AND end_time = %s",
            (video_url_id, start_time, end_time)
        )
        video_timestamp_result = cursor.fetchone()
        if not video_timestamp_result:
            print("VideoTimeStamps entry not found.")
            return

        video_timestamp_id = video_timestamp_result[0]

        # Step 3: Insert the new prediction
        cursor.execute(
            "INSERT INTO api_Prediction (video_timestamp_id, prediction) VALUES (%s, %s)",
            (video_timestamp_id, prediction)
        )

        # Commit the transaction
        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()

def fetch_predictions(print_output=False):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # SQL query to fetch predictions
        fetch_query = """
        SELECT * 
        FROM api_prediction
        """
        # Execute the fetch query
        cursor.execute(fetch_query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Print the rows
        if print_output:
            for row in rows:
                print(f"Video Foreignkey {row[2]}, Prediction: {row[1]}")
        return rows
    
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


if __name__ == "__main__":
    
    insert_csv_file_in_db()
    
    # fetch_timestamps(print_output=True)
    # fetch_urls(print_output=True)
    # insert_prediction_to_db("MkzFodsSOHc", "56.88", "58.16", "TE")
    # fetch_predictions(print_output=True)


