from fastapi import FastAPI, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import subprocess
import time
import requests
from pytube import YouTube
import fireworks.client 
import fireworks
import assemblyai as aai

app = FastAPI()

# Set your AssemblyAI and Fireworks API keys
assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY", "d2bd36d30d9c43bba76bb4cd295ebe60")
fireworks_api_key = os.getenv("FIREWORKS_API_KEY", "dqd5BQHUmdfBtV8lEXlxaGs7MXmdisBiMOrChQ76oAo5LXru" )

aai.settings.api_key = assemblyai_api_key
fireworks.client.api_key = fireworks_api_key

# Function to download YouTube video
def download_youtube_video(youtube_url, video_output):
    yt = YouTube(youtube_url)
    video_stream = yt.streams.filter(only_audio=True).first()
    video_stream.download(filename=video_output)

# Function to extract audio from video
def extract_audio(video_path, audio_output):
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_output}"
    subprocess.run(command, shell=True, check=True)

# Function to upload audio to AssemblyAI
def upload_to_assemblyai(audio_path):
    headers = {
        "authorization": assemblyai_api_key,
    }
    with open(audio_path, "rb") as f:
        response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, files={"file": f})
    response.raise_for_status()
    return response.json()["upload_url"]

# Function to transcribe audio using AssemblyAI
def transcribe_audio(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json_data = {"audio_url": audio_url}
    headers = {
        "authorization": assemblyai_api_key,
        "content-type": "application/json"
    }
    response = requests.post(endpoint, json=json_data, headers=headers)
    response.raise_for_status()
    transcript_id = response.json()["id"]

    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        if result["status"] == "completed":
            return result["text"]
        elif result["status"] == "failed":
            raise HTTPException(status_code=500, detail="Transcription failed")
        time.sleep(5)

def get_completion(prompt, max_tokens=4096):
    completion = fireworks.client.Completion.create(
        model="accounts/fireworks/models/llama-v3-70b-instruct",
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

@app.post("/process-youtube-url")
async def process_youtube_url(youtube_url: str = Form(...)):
    try:
        transcription, action_items, mcqs = process_video(youtube_url=youtube_url)
        mcqs_list = [q.strip() for q in mcqs.split('\n') if q.strip()]
        mcqs_dict = {}
        question = ""
        for i, line in enumerate(mcqs_list):
            if i % 6 == 0:
                question = line
                mcqs_dict[question] = []
            else:
                mcqs_dict[question].append(line)
        return JSONResponse(content={
            "mcqs": mcqs_dict
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-video")
async def upload_video(file: UploadFile):
    try:
        video_file_path = file.filename
        with open(video_file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        transcription, action_items, mcqs = process_video(video_file_path=video_file_path)
        mcqs_list = [q.strip() for q in mcqs.split('\n') if q.strip()]
        mcqs_dict = {}
        question = ""
        for i, line in enumerate(mcqs_list):
            if i % 6 == 0:
                question = line
                mcqs_dict[question] = []
            else:
                mcqs_dict[question].append(line)
        
        os.remove(video_file_path)  # Clean up uploaded video file
        return JSONResponse(content={
            "transcription": transcription,
            "action_items": action_items,
            "mcqs": mcqs_dict
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
