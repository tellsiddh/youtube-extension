# YouTube Analytics and Transcription Fetcher

This Chrome extension fetches YouTube analytics data and audio transcriptions for a specified YouTube video. The extension uses the YouTube Data API to retrieve analytics data and a local server to fetch audio transcriptions.

## Features

- Fetch YouTube video analytics including:
  - Channel name and description
  - Subscriber count
  - Total views
  - Total videos
  - Video title, view count, like count, comment count, and duration
- Fetch audio transcription for the video

## Prerequisites

- Google API Key with access to YouTube Data API v3
- Local server running to handle audio transcription requests

## Setup

1. Clone the repository to your local machine.
2. Create a `config.json` file in the root directory with the following structure:

    ```json
    {
      "apiKey": "YOUR_YOUTUBE_API_KEY",
      "dev_key": "YOUR_DEV_KEY",
      "dev_url": "YOUR_DEV_URL"
    }
    ```

    Replace `YOUR_YOUTUBE_API_KEY` with your actual YouTube API key, `YOUR_DEV_KEY` with your server's development key, and `YOUR_DEV_URL` with your server's URL.

3. Install dependencies:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

### Start the Local Server

Run the Flask server:

```sh
python app.py
