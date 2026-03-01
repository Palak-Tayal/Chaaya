import os
import sys
# Add the parent directory to sys.path so that 'backend' is recognized
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid

import backend.parser as parser
import backend.vector_store as vector_store
import backend.query_engine as query_engine

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# In-memory store for uploaded chat metadata
chat_registry = {}

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    collection_id = str(uuid.uuid4())
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{collection_id}_{filename}")
    file.save(filepath)
    
    try:
        messages = parser.parse_whatsapp_chat(filepath)
    except Exception as e:
        return jsonify({'error': f'Failed to parse chat: {str(e)}'}), 400
    
    senders = list(set(m['sender'] for m in messages))
    
    chat_registry[collection_id] = {
        'filename': filename,
        'senders': senders,
        'filepath': filepath,
        'messages': messages
    }
    
    return jsonify({
        'collection_id': collection_id,
        'senders': senders,
        'message_count': len(messages)
    })

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    collection_id = data.get('collection_id')
    person = data.get('person')
    question = data.get('question')
    use_openai = data.get('use_openai', True)
    
    if not collection_id or not person or not question:
        return jsonify({'error': 'Missing collection_id, person, or question'}), 400
    
    chat_info = chat_registry.get(collection_id)
    if not chat_info:
        return jsonify({'error': 'Invalid collection_id'}), 404
    
    messages = chat_info['messages']
    filtered = [m for m in messages if m['sender'] == person]
    if not filtered:
        return jsonify({'error': f'No messages from {person} found in this chat.'}), 404
    
    result = query_engine.query_perspective(filtered, question, person, use_openai=use_openai)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)