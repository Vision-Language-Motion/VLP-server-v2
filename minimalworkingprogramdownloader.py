import os
import yt_dlp as youtube_dl
from pytube import YouTube


def download_video_pytube(url):
    """
    This function downloads the video using pytube module into the download_directory.
    The video is saved in the best quality available up to 720p.
    """
    # Create a YouTube object
    yt = YouTube(url)
    
    # Filter streams to get the best quality video up to 720p
    stream = yt.streams.filter(progressive=True, file_extension='mp4', res='720p').first()
    
    # If no 720p video is found, get the highest resolution below 720p
    if not stream:
        stream = yt.streams.filter(progressive=True, file_extension='mp4', res='480p').first()
    
    # If no 360p video is found, get the highest resolution below 720p
    if not stream:
        stream = yt.streams.filter(progressive=True, file_extension='mp4', res='360p').first()

    # Download the video
    file_path = stream.download(output_path=download_directory, filename=f'{yt.video_id}.mp4')
    
    return file_path

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


if __name__ == "__main__":

    # Definining download directory
    download_directory = os.path.join(os.getcwd(), 'youtube-downloads')
    os.makedirs(download_directory, exist_ok=True)

    # new_youtube_url = 'https://www.youtube.com/shorts/MkzFodsSOHc'  # insert url here
    url = "https://www.youtube.com/watch?v=5ukw9wVRYg4"

    file_path = download_video(url)

    