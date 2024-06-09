import assemblyai as aai
import requests
import time
import os
import subprocess
from pytube import YouTube
from textwrap import wrap
from fireworks.client import Fireworks
import fireworks.client
from dotenv import load_dotenv
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY')
fireworks.client.api_key = FIREWORKS_API_KEY

# Ensure the API key is set
if not ASSEMBLYAI_API_KEY:
    raise ValueError("ASSEMBLYAI_API_KEY is not set. Please set it as an environment variable.")

# Print API keys for debugging (remove these lines in production)
print(f"ASSEMBLYAI_API_KEY: {ASSEMBLYAI_API_KEY}")
print(f"FIREWORKS_API_KEY: {FIREWORKS_API_KEY}")

# Function to download YouTube video
def download_youtube_video(youtube_url, video_output):
    yt = YouTube(youtube_url)
    video_stream = yt.streams.filter(only_audio=True).first()
    video_stream.download(filename=video_output)

# Function to extract audio from video
def extract_audio(video_path, audio_output):
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_output}"
    subprocess.run(command, shell=True)

# Function to upload audio to AssemblyAI
def upload_to_assemblyai(audio_path):
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
    }
    try:
        with open(audio_path, "rb") as audio_file:
            response = requests.post("https://api.assemblyai.com/v2/upload",
                                     headers=headers,
                                     files={"file": audio_file})
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        response_json = response.json()
        print(f"Upload response: {response_json}")  # Debugging line
        return response_json["upload_url"]
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise
    except KeyError:
        print(f"Unexpected response structure: {response_json}")
        raise

# Function to transcribe audio using AssemblyAI
def transcribe_audio(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json = {
        "audio_url": audio_url
    }
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }
    response = requests.post(endpoint, json=json, headers=headers)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    transcript_id = response.json()["id"]

    # Polling for the transcription result
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        if result["status"] == "completed":
            return result["text"]
        elif result["status"] == "failed":
            raise Exception("Transcription failed")
        time.sleep(5)

def get_completion(prompt, max_tokens=4096):
    fw_model_dir = "accounts/fireworks/models/"
    model = "llama-v3-70b-instruct"
    model = fw_model_dir + model
    completion = fireworks.client.Completion.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0
    )
    return completion.choices[0].text

# Function to extract action items using Fireworks
def extract_action_items(transcription):
    prompt = f"Extract action items from the following meeting transcript:\n\n{transcription}\n\nAction items:"
    action_items = get_completion(prompt)
    return action_items.strip()

# Function to generate MCQs
def generate_mcqs(transcription):
    prompt = f"Generate 10 multiple choice questions from the following transcript. Only provide the questions and answer options without any additional text or formatting:\n\n{transcription}\n\nMCQs:"
    mcqs = get_completion(prompt)
    return mcqs.strip()

# Main process function
def process_video(video_file_path=None, youtube_url=None):
    video_file_path = "downloaded_video.mp4" if youtube_url else video_file_path
    audio_file_path = "output_audio.mp3"

    if youtube_url:
        download_youtube_video(youtube_url, video_file_path)

    extract_audio(video_file_path, audio_file_path)
    audio_url = upload_to_assemblyai(audio_file_path)
    transcription = transcribe_audio(audio_url)
    action_items = extract_action_items(transcription)
    mcqs = generate_mcqs(transcription)

    if youtube_url:
        os.remove(video_file_path)  # Clean up video file if it was downloaded
    os.remove(audio_file_path)  # Clean up audio file
    return transcription, action_items, mcqs

<<<<<<< HEAD
#if __name__ == "__main__":
=======
#if _name_ == "_main_":
>>>>>>> refs/remotes/origin/main
#    youtube_url = input("Enter YouTube URL (leave blank if uploading a video file): ").strip()
#    video_file_path = None if youtube_url else input("Enter the path to the video file: ").strip()
#    
#    # Process the video
#    transcription, action_items, mcqs = process_video(video_file_path=video_file_path, youtube_url=youtube_url)
##    
#    print("Transcription:")
#    print(transcription)
#    print("\nAction Items:")
#    print(action_items)
#    print("\nMCQs:")
<<<<<<< HEAD
#    print(mcqs)
=======
#    print(mcqs)
>>>>>>> refs/remotes/origin/main
