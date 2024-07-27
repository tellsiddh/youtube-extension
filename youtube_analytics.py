import os
import googleapiclient.discovery
import isodate
from urllib.parse import urlparse, parse_qs
import json

# Define the API service name/version and your API key
api_service_name = "youtube"
api_version = "v3"

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    api_key = config['api_key']

def get_authenticated_service():
    # Create an API client using the API key
    return googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

def get_video_id(video_url):
    # Extract the video ID from the video URL
    url_data = urlparse(video_url)
    query = parse_qs(url_data.query)
    return query["v"][0]

def get_channel_id_from_video(youtube, video_id):
    # Get the channel ID from the video ID
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    channel_id = response["items"][0]["snippet"]["channelId"]
    return channel_id

def get_channel_videos(youtube, channel_id):
    # Get the list of video IDs from the channel
    video_ids = []
    request = youtube.search().list(
        part="id",
        channelId=channel_id,
        maxResults=50,
        type="video"
    )

    while request:
        response = request.execute()
        for item in response['items']:
            video_ids.append(item['id']['videoId'])
        
        request = youtube.search().list_next(request, response)
    
    return video_ids

def get_video_durations(youtube, video_ids):
    # Get the durations of the videos
    durations = []
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="contentDetails",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()
        for item in response['items']:
            duration = isodate.parse_duration(item['contentDetails']['duration'])
            durations.append(duration.total_seconds())
    
    return durations

def calculate_average_duration(durations):
    if not durations:
        return 0
    return sum(durations) / len(durations)

def get_channel_statistics(youtube, channel_id):
    # Get the channel statistics
    request = youtube.channels().list(
        part="statistics,snippet",
        id=channel_id
    )
    response = request.execute()
    return response["items"][0]

if __name__ == "__main__":
    try:
        # Initialize the YouTube API client
        youtube = get_authenticated_service()

        # Define the video URL you want to get the average video duration for
        video_url = "https://www.youtube.com/watch?v=wjZofJX0v4M"

        # Extract the video ID from the video URL
        video_id = get_video_id(video_url)

        # Get the channel ID from the video ID
        channel_id = get_channel_id_from_video(youtube, video_id)
        print(f"Channel ID: {channel_id}")

        # Get the channel statistics
        channel_statistics = get_channel_statistics(youtube, channel_id)
        print("Channel Statistics:")
        print(f"Title: {channel_statistics['snippet']['title']}")
        print(f"Description: {channel_statistics['snippet']['description']}")
        print(f"Subscribers: {channel_statistics['statistics'].get('subscriberCount', 'hidden')}")
        print(f"Total Views: {channel_statistics['statistics']['viewCount']}")
        print(f"Total Videos: {channel_statistics['statistics']['videoCount']}")

        # Get the list of video IDs from the channel
        video_ids = get_channel_videos(youtube, channel_id)
        print(f"Total videos found: {len(video_ids)}")

        # Get the durations of the videos
        video_durations = get_video_durations(youtube, video_ids)
        print(f"Total durations collected: {len(video_durations)}")

        # Calculate the average video duration
        average_duration = calculate_average_duration(video_durations)
        print(f"Average video duration: {average_duration / 60:.2f} minutes")

    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
