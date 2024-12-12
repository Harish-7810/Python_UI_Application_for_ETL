from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from flask_socketio import SocketIO
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Directory Configuration
UPLOAD_FOLDER = "D:/in"
DOWNLOAD_FOLDER = "D:/out"

# Create directories if they do not exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

@app.route('/')
def index():
    # List files in the downloads directory for downloading
    files = [file for file in os.listdir(DOWNLOAD_FOLDER) if file.endswith('.json')]
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Simulate processing (you can replace this with your actual processing logic)
    processed_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
    with open(filepath, "r") as f:
        file_data = f.read()

    # Here, we can simulate processing the data and saving it to the download folder
    with open(processed_filepath, "w") as f:
        f.write(file_data)

    socketio.emit('file_uploaded', {'filename': filename})  # Notify client about new file

    return '', 204

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Check if the file exists in the download folder
    filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)

def monitor_download_folder():
    # Monitor the download folder for file changes (deletions, new files)
    previous_files = set(os.listdir(DOWNLOAD_FOLDER))

    while True:
        time.sleep(1)  # Check every second
        current_files = set(os.listdir(DOWNLOAD_FOLDER))

        # Files that were deleted
        deleted_files = previous_files - current_files
        if deleted_files:
            for file in deleted_files:
                socketio.emit('file_deleted', {'filename': file})

        # Files that were added
        new_files = current_files - previous_files
        if new_files:
            for file in new_files:
                if file.endswith('.json'):  # Only send .json files
                    socketio.emit('file_uploaded', {'filename': file})

        previous_files = current_files

if __name__ == '__main__':
    # Start the folder monitoring in a separate thread
    thread = threading.Thread(target=monitor_download_folder)
    thread.daemon = True
    thread.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
