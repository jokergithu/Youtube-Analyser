import streamlit as st
import requests
import subprocess
import time
import os
from pytube import YouTube
from textwrap import wrap
import fireworks
import assemblyai as aai
# Set AssemblyAI and Fireworks API keys
aai.settings.api_key = st.secrets["ASSEMBLYAI_API_KEY"]
api_key = st.secrets["FIREWORKS_API_KEY"]
fireworks.client.api_key = api_key
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
        "authorization": aai.settings.api_key,
    }
    response = requests.post("https://api.assemblyai.com/v2/upload",
                             headers=headers,
                             files={"file": open(audio_path, "rb")})
    return response.json()["upload_url"]

# Function to transcribe audio using AssemblyAI
def transcribe_audio(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json = {
        "audio_url": audio_url
    }
    headers = {
        "authorization": aai.settings.api_key,
        "content-type": "application/json"
    }
    response = requests.post(endpoint, json=json, headers=headers)
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

# Function to get completion using Fireworks API
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

    return completion.choices[0].text.strip()

# Function to extract action items using Fireworks
def extract_action_items(transcription):
    prompt = f"Extract action items from the following meeting transcript:\n\n{transcription}\n\nAction items:"
    action_items = get_completion(prompt)
    return action_items

# Function to generate MCQs using Fireworks
def generate_mcqs(transcription):
    prompt = f"Generate 10 multiple choice questions from the following transcript. Only provide the questions and answer options without any additional text or formatting:\n\n{transcription}\n\nMCQs:"
    mcqs = get_completion(prompt)
    return mcqs

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

# Streamlit App
st.title("YouTube Video Quiz Generator")

# Page 1: Upload Page
def upload_page():
    st.header("Upload Video")
    youtube_url = st.text_input("Enter YouTube URL:")
    video_file = st.file_uploader("Upload Video File", type=["mp4"])

    if st.button("Start Processing"):
        if youtube_url or video_file:
            transcription, action_items, mcqs = process_video(video_file_path=video_file, youtube_url=youtube_url)
            st.session_state.transcription = transcription
            st.session_state.action_items = action_items
            st.session_state.mcqs = mcqs
            st.session_state.current_question = 0
            st.session_state.answers = []
            st.session_state.page = "Quiz Start"
        else:
            st.error("Please provide either a YouTube URL or upload a video file.")

# Page 2: Quiz Start Page
def quiz_start_page():
    st.header("Quiz Start")
    st.write("The quiz is ready to start. Click the button below to begin.")
    if st.button("Start Quiz"):
        st.session_state.page = "Quiz"

# Page 3: Quiz Page
def quiz_page():
    st.header("Quiz Questions")
    questions = st.session_state.mcqs.split("\n")
    if st.session_state.current_question < len(questions):
        st.write(questions[st.session_state.current_question])
        answer = st.radio("Select an option", ["Option A", "Option B", "Option C", "Option D"])
        if st.button("Next"):
            st.session_state.answers.append(answer)
            st.session_state.current_question += 1
    else:
        st.session_state.page = "Report"

# Page 4: Report Page
def report_page():
    st.header("Quiz Report")
    st.write("You have completed the quiz! Here are your results:")
    st.write(f"Total Questions: {len(st.session_state.answers)}")
    st.write(f"Answers: {st.session_state.answers}")
    st.write("Suggestions for improvement:")
    st.write(st.session_state.action_items)

# Main Page Navigation
if 'page' not in st.session_state:
    st.session_state.page = "Upload"
if st.session_state.page == "Upload":
    upload_page()
elif st.session_state.page == "Quiz Start":
    quiz_start_page()
elif st.session_state.page == "Quiz":
    quiz_page()
elif st.session_state.page == "Report":
    report_page()
