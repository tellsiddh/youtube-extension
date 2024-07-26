import os
import googleapiclient.discovery

# Define the API service name/version and your API key
api_service_name = "youtube"
api_version = "v3"
api_key = "AIzaSyC5emxRJDALTQaj07vbB9eCvZuKmCE7ExA"

def get_authenticated_service():
    # Create an API client using the API key
    return googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

def get_video_analytics(youtube, video_id):
    # Get video details
    request = youtube.videos().list(
        part="statistics",
        id=video_id
    )
    response = request.execute()

    return response

if __name__ == "__main__":
    # Initialize the YouTube API client
    youtube = get_authenticated_service()

    # Define the video ID you want to get analytics for
    video_id = "euYR3Kxlvhk"

    # Get video analytics data
    analytics_data = get_video_analytics(youtube, video_id)
    print(analytics_data)
