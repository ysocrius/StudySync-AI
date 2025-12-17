from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Citrine & Sage Integration Backend"})

from rag import rag_system
from audio_gen import generate_dialogue_script, generate_audio_files

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    from flask import Response, stream_with_context
    import json

    def generate():
        # Yield result
        # Note: If stream_answer_with_docs fails, we should handle it
        try:
            for text_chunk, docs in rag_system.stream_answer_with_docs(question):
                if text_chunk:
                    yield text_chunk
                if docs:
                    # Send sources as a special delimiter line at the end
                    sources = []
                    for doc in docs:
                        sources.append({
                            "content": doc.page_content[:200] + "...", 
                            "metadata": doc.metadata
                        })
                    yield "\n__SOURCES__:" + json.dumps(sources)
        except Exception as e:
            yield f"Error: {str(e)}"

    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/api/summary', methods=['GET'])
def get_summary_route():
    summary = rag_system.get_summary()
    return jsonify({"summary": summary})

@app.route('/api/dialogue', methods=['GET'])
def get_dialogue():
    # In a real app, we might cache this or generate on demand.
    # For MVP, let's generate if empty, or return cached.
    # We'll just generate every time for simplicity or check simpler cache
    
    try:
        script = generate_dialogue_script()
        audio_data = generate_audio_files(script)
        return jsonify({"dialogue": audio_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.lower().endswith('.pdf'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({"success": True, "filename": file.filename})
    return jsonify({"error": "Only PDF files allowed"}), 400

from ingest import validate_video_captions

# Async Processing State
processing_state = {
    "status": "idle", # idle, processing, complete, error
    "message": "",
    "percent": 0
}

import threading

def update_progress(msg):
    """Callback to update global processing state."""
    global processing_state
    print(f"[Progress] {msg}")
    processing_state["message"] = msg
    processing_state["status"] = "processing"

def run_ingestion_thread(pdf_files, youtube_urls):
    global processing_state
    try:
        processing_state["status"] = "processing"
        processing_state["message"] = "Starting ingestion..."
        
        rag_system.initialize_vector_store(
            pdf_paths=pdf_files, 
            video_urls=youtube_urls, 
            progress_callback=update_progress
        )
        
        processing_state["status"] = "complete"
        processing_state["message"] = "Knowledge base updated!"
    except Exception as e:
        print(f"Ingestion failed: {e}")
        processing_state["status"] = "error"
        processing_state["message"] = f"Error: {str(e)}"

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(processing_state)

@app.route('/api/process-sources', methods=['POST'])
def process_sources():
    global processing_state
    
    # Don't start if already running
    if processing_state["status"] == "processing":
         return jsonify({"status": "Busy", "message": "Already processing"}), 409

    data = request.json
    youtube_urls = data.get('youtube_urls', [])
    
    # Validation
    for url in youtube_urls:
        lines_valid, error_msg = validate_video_captions(url)
        if not lines_valid:
             return jsonify({"error": f"Invalid Video ({url}): {error_msg}"}), 400

    # Get PDFs based on user selection (if provided)
    pdf_filenames = data.get('pdf_filenames')
    
    if pdf_filenames is not None:
        # User provided specific list, use it (security filter applied via os.path.basename implicitly by match check)
        available_files = os.listdir(UPLOAD_FOLDER)
        pdf_files = [
            os.path.join(UPLOAD_FOLDER, f) 
            for f in available_files 
            if f in pdf_filenames and f.endswith('.pdf')
        ]
    else:
        # Fallback: Use all files in folder
        pdf_files = [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    
    # Reset State
    processing_state = {
        "status": "queued",
        "message": "Queued for processing...",
        "percent": 0
    }
    
    # Start Thread
    thread = threading.Thread(target=run_ingestion_thread, args=(pdf_files, youtube_urls))
    thread.daemon = True # Kill if main kills
    thread.start()
    
    return jsonify({"status": "Accepted", "message": "Processing started in background"}), 202


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
