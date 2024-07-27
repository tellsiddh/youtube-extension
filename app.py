from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import base64
import io
import traceback
import logging
import os
import json
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Temporarily disable CORS for testing
CORS(app)

# Path to cache directory
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def cache_audio(video_id, base64_audio, transcription_text):
    cache_file_path = os.path.join(CACHE_DIR, f"{video_id}.json")
    with open(cache_file_path, 'w') as cache_file:
        json.dump({"base64_audio": base64_audio, "transcription_text": transcription_text}, cache_file)

def get_cached_audio(video_id):
    cache_file_path = os.path.join(CACHE_DIR, f"{video_id}.json")
    if os.path.exists(cache_file_path):
        with open(cache_file_path, 'r') as cache_file:
            data = json.load(cache_file)
            return data.get("base64_audio"), data.get("transcription_text")
    return None, None

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

@app.route('/fetch_mp3', methods=['POST', 'OPTIONS'])
def fetch_mp3():
    app.logger.info(f"Received request: {request.method}")
    app.logger.info(f"Request headers: {request.headers}")
    app.logger.info(f"Request body: {request.get_data(as_text=True)}")

    if request.method == 'OPTIONS':
        # Handle preflight request
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.json
        app.logger.info(f"Parsed JSON data: {data}")
        video_url = data.get('video_url')
        model_provider = data.get('model_provider', 'openai')
        model_name = data.get('model_name', 'whisper-1')
        
        if not video_url:
            app.logger.error("No video URL provided")
            return jsonify({"error": "No video URL provided"}), 400

        app.logger.info(f"Attempting to download video from URL: {video_url}")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            app.logger.info("Extracting video info")
            result = ydl.extract_info(video_url, download=False)  # Extract info without downloading
            video_id = result['id']
            app.logger.info(f"Video ID: {video_id}")

            cached_audio, cached_transcription = get_cached_audio(video_id)
            if cached_audio and cached_transcription:
                app.logger.info("Using cached audio and transcription")
                base64_audio = cached_audio
                transcription_text = cached_transcription
            else:
                app.logger.info("Downloading audio")
                result = ydl.extract_info(video_url, download=True)  # Now download the audio
                audio_file_path = ydl.prepare_filename(result)

                app.logger.info(f"Loading audio file from: {audio_file_path}")
                with open(audio_file_path, "rb") as webm_file:
                    encoded_string = base64.b64encode(webm_file.read())
                    base64_audio = encoded_string.decode('utf-8')

                app.logger.info("Sending audio to external API")
                config = load_config()
                dev_key = config.get('dev_key')
                dev_url = config.get('dev_url')

                audio_body = {
                    "query": "can you transcribe this",
                    "audio_file": base64_audio,
                    "model_provider": model_provider,
                    "model_name": model_name
                }

                headers = {
                    'Authorization': f'Bearer {dev_key}',
                    'Content-Type': 'application/json'
                }

                response = requests.post(dev_url, json=audio_body, headers=headers)
                app.logger.info(f"External API response status code: {response.status_code}")
                app.logger.info(f"External API response content: {response.text}")

                if response.status_code != 200:
                    return jsonify({"error": f"External API returned status code {response.status_code}", "content": response.text}), 500

                try:
                    response_data = response.json()
                    transcription_text = response_data.get("response").get("transcription_text").get("text")
                except json.JSONDecodeError as e:
                    app.logger.error(f"Error decoding JSON response: {str(e)}")
                    app.logger.error(traceback.format_exc())
                    return jsonify({"error": "Error decoding JSON response", "content": response.text}), 500

                app.logger.info("Caching audio and transcription")
                cache_audio(video_id, base64_audio, transcription_text)

            return jsonify({"base64_webm": base64_audio, "transcription_response": transcription_text})

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True)
