# app.py
from flask import Flask, request, redirect, url_for, render_template
import os
from model import process_video

app = Flask(__name__)
UPLOAD_FOLDER = 'uploaded_videos/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        transcription, action_items, mcqs = process_video(video_file_path=file_path)
        return redirect(url_for('start_quiz', mcqs=mcqs))
    return redirect(url_for('index'))

@app.route('/start_quiz')
def start_quiz():
    return render_template('start_quiz.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/report')
def report():
    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)
