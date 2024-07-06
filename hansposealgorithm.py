import cv2
import os
import shutil
import json
import csv
from mmpose.apis import MMPoseInferencer
#from mmpretrain.models import VisionTransformer
import time
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

start_time = time.time()
inferencer = MMPoseInferencer('rtmpose-l')

def process_scene(scene_frames, scene_output_dir, frame_width, frame_height):
    frame_area = frame_width * frame_height
    min_bbox_area = frame_area / 60  # figure should be bigger than 1/60 of frame area

    frame_paths = []  # store frame
    people_counts = []  # store number of visible human
    frame_qualities = []  # save frame quality (high, medium, low)

    for frame_count, frame in enumerate(scene_frames):
         frame_path = os.path.join(scene_output_dir, f'{frame_count}.png')
         cv2.imwrite(frame_path, frame)
         frame_paths.append(frame_path)
         result_generator = inferencer(frame_path, pred_out_dir=scene_output_dir)
         next(result_generator)
    
    for frame_path in frame_paths:
        json_path = frame_path.replace('.png', '.json')
        with open(json_path, 'r') as file:
            data = json.load(file)
            visible_people = 0
            for person in data:
                scores = person['keypoint_scores']
                bbox = person['bbox'][0]
                bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                bbox_score = person['bbox_score']
                head_points = scores[:5]
                other_points = scores[5:]
                visible_head_points = sum(score >= 0.7 for score in head_points)
                visible_other_points = sum(score >= 0.35 for score in other_points)
                visible_points = visible_head_points + visible_other_points
                if bbox_area >= min_bbox_area and bbox_area < frame_area and bbox_score >= 0.4 and visible_points >= 5:
                    visible_people += 1
                    shoulders_visible = scores[5] >= 0.5 or scores[6] >= 0.5
                    knees_visible = scores[13] >= 0.5 or scores[14] >= 0.5
                    arms_hands_visible = sum(scores[i] >= 0.5 for i in [5, 6, 7, 8, 9, 10]) >= 3
                    if shoulders_visible and knees_visible and bbox_area/frame_area > 1/30:
                        frame_qualities.append("high")
                    elif arms_hands_visible and bbox_area/frame_area > 1/30:
                        frame_qualities.append("medium")
                    else:
                        frame_qualities.append("low")
                
            people_counts.append(visible_people)
    
    return people_counts, frame_qualities


def process_video(video_path, base_output_dir):
    video_name = os.path.basename(video_path).split('.')[0]
    video_output_dir = os.path.join(base_output_dir, 'temp', video_name)  # save temporal result
    os.makedirs(video_output_dir, exist_ok=True)
    
    # Detect scenes in the video
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=30))
    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()
    video_manager.release()

    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    results = []

    for scene_num, scene in enumerate(scene_list):
        start_frame, end_frame = scene[0].get_frames(), scene[1].get_frames()

        scene_duration = (end_frame - start_frame) / cap.get(cv2.CAP_PROP_FPS)
        if scene_duration < 5:
            continue
        
        frame_count = 0
        scene_frames = []

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        for _ in range(start_frame, end_frame):
            ret, frame = cap.read() 
            if not ret: # something went wrong
                break 
            if frame_count % 30 == 0:  # sample per 30 frames
                scene_frames.append(frame)
            frame_count += 1

        scene_output_dir = os.path.join(video_output_dir, f'scene_{scene_num}')
        os.makedirs(scene_output_dir, exist_ok=True)
        people_counts, frame_qualities = process_scene(scene_frames, scene_output_dir, frame_width, frame_height)
        
        # classify after number of human figure(single, multiple, nohuman)
        if all(count == 0 for count in people_counts):
            classification = 'nh'  # nh
        elif any(count > 1 for count in people_counts):
            classification = 'mu' # multiple
        else:
            classification = 'si' # single
            # further subdivision in single category
            high_count = sum(1 for i in range(len(frame_qualities) - 2) if all(q == "high" for q in frame_qualities[i:i+3]))
            medium_count = sum(1 for i in range(len(frame_qualities) - 2) if all(q in ["medium", "high"] for q in frame_qualities[i:i+3]))
            if high_count > 0:
                classification = 'sh' # single high
            elif medium_count > 0:
                classification = 'sm' # single medium
            else:
                classification = 'sl' # single low

        start_time = start_frame / cap.get(cv2.CAP_PROP_FPS)
        end_time = end_frame / cap.get(cv2.CAP_PROP_FPS)

        results.append([video_name, start_time, end_time, classification])
    
    cap.release()
    shutil.rmtree(os.path.join(base_output_dir, 'temp'))

    return results

# ''' When testing remove the hashtag in this line 
# video_folder = '/home/markusc/MyP/openpose_estimation/webvid1k'  # input video folder, change to your own path
video_folder = os.path.join(os.getcwd(), 'youtube-downloads')
# base_output_dir = '/home/markusc/MyP/mmpose_estimation/process_in_batch/rtml24webvid1k'  # output folder, change to your own path
base_output_dir = os.path.join(os.getcwd(), 'output')
os.makedirs(video_folder, exist_ok=True)
os.makedirs(base_output_dir, exist_ok=True)

video_formats = ['.mp4', '.avi', '.mov', '.mkv']  # add more video format if needed

all_results = []

for video_file in os.listdir(video_folder):
    video_path = os.path.join(video_folder, video_file)
    if os.path.isfile(video_path) and any(video_file.endswith(fmt) for fmt in video_formats):
        video_results = process_video(video_path, base_output_dir)
        all_results.extend(video_results)



from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import execute_values
load_dotenv()


# Database connection parameters
db_params = {
    'dbname': 'defaultdb',
    'user': 'doadmin',
    'password': os.environ.get('DO_DATABASE_PASSWORD', None),
    'host': 'vlp-database-docker-do-user-10555764-0.c.db.ondigitalocean.com',
    'port': '25060'
}

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

for result in all_results:
    insert_prediction_to_db(result[0], result[1], result[2], result[3])

# delete video folder at the end
shutil.rmtree(video_folder)

#with open(os.path.join(base_output_dir, 'predictions.csv'), mode='w+', newline='') as csv_file:
#    csv_writer = csv.writer(csv_file)
#    csv_writer.writerow(['Video Name', 'Start Time (s)', 'End Time (s)', 'Classification'])
#    for result in all_results:
#        csv_writer.writerow(result)
#'''
