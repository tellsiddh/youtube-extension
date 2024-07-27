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
from pydub import AudioSegment
import asyncio
import aiohttp

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

def split_audio(audio_segment, chunk_size=6 * 1024 * 1024):
    chunk_length = int((chunk_size / audio_segment.frame_rate / audio_segment.frame_width / audio_segment.channels) * 1000)
    chunks = [audio_segment[i:i + chunk_length] for i in range(0, len(audio_segment), chunk_length)]
    return chunks

def convert_chunk_to_mp3(chunk):
    mp3_io = io.BytesIO()
    chunk.export(mp3_io, format="mp3")
    return mp3_io.getvalue()

async def transcribe_chunk(session, chunk_base64, dev_url, headers, model_provider, model_name):
    audio_body = {
        "query": "can you transcribe this",
        "audio_file": chunk_base64,
        "model_provider": model_provider,
        "model_name": model_name
    }
    async with session.post(dev_url, json=audio_body, headers=headers) as response:
        response_data = await response.json()
        app.logger.debug(f"Transcription API response: {response_data}")
        return response_data.get("response", {}).get("transcription_text", {}).get("text")

async def transcribe_audio_chunks(audio_chunks, dev_url, headers, model_provider, model_name):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for chunk in audio_chunks:
            mp3_chunk = convert_chunk_to_mp3(chunk)
            chunk_base64 = base64.b64encode(mp3_chunk).decode('utf-8')
            tasks.append(transcribe_chunk(session, chunk_base64, dev_url, headers, model_provider, model_name))
        transcriptions = await asyncio.gather(*tasks)
        app.logger.debug(f"Transcriptions: {transcriptions}")
        return " ".join(transcriptions)

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
                transcription_string = cached_transcription
            else:
                app.logger.info("Downloading audio")
                result = ydl.extract_info(video_url, download=True)  # Now download the audio
                audio_file_path = ydl.prepare_filename(result)

                app.logger.info(f"Loading audio file from: {audio_file_path}")
                audio = AudioSegment.from_file(audio_file_path)
                audio_chunks = split_audio(audio)

                app.logger.info("Sending audio chunks to external API")
                config = load_config()
                dev_key = config.get('dev_key')
                dev_url = config.get('dev_url')

                headers = {
                    'Authorization': f'Bearer {dev_key}',
                    'Content-Type': 'application/json'
                }

                transcription_text = asyncio.run(transcribe_audio_chunks(audio_chunks, dev_url, headers, model_provider, model_name))

                encoded_string = base64.b64encode(audio.raw_data)
                base64_audio = encoded_string.decode('utf-8')
                transcription_string = "".join(transcription_text)
                app.logger.info("Caching audio and transcription")
                cache_audio(video_id, base64_audio, transcription_string)

                # Delete the audio file after transcription and caching
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                    app.logger.info(f"Deleted audio file: {audio_file_path}")
        
            return jsonify({"base64_webm": base64_audio, "transcription_response": transcription_string})

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True)
