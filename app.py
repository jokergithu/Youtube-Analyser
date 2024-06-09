# app.py
from flask import Flask, request, redirect, url_for, render_template, jsonify
import os
from model import process_video, generate_report

app = Flask(__name__)
UPLOAD_FOLDER = 'uploaded_videos/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' in request.files:
        # Handle file upload
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        transcription, action_items, mcqs = process_video(video_file_path=file_path)
        return redirect(url_for('start_quiz', mcqs=mcqs))
    elif 'link' in request.json:
        youtube_link = request.json['link']
        print(youtube_link)
        transcription, action_items, mcqs = process_video(youtube_url=youtube_link)
        print(mcqs)
        return jsonify({'mcqs': mcqs})
    else:
        print("error")
        return jsonify({'error': 'No file or link provided'}), 400
    return redirect(url_for('index'))

@app.route('/start_quiz')
def start_quiz():
    return render_template('start_quiz.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if request.is_json:
        data = request.get_json()
        report = generate_report(data)
        return jsonify({'message': report}), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400

@app.route('/report')
def report():
    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)
