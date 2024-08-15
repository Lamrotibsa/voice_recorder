import io
import random
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs
import os

app = Flask(__name__)
# Initialize CORS with specific configuration
CORS(app)  # Adjust origins as needed  # Enable CORS for all routes

# Initialize MongoDB connection
client = MongoClient('mongodb://localhost:27017')
db = client['stt']
fs = gridfs.GridFS(db)
coll = db['datasets']

@app.route('/sentence', methods=['GET'])
def get_random_sentence():
    try:
        # Find the total number of documents in the collection
        total_documents = coll.count_documents({})
        
        if total_documents == 0:
            return jsonify({"sentence": "No sentences available"}), 404
        
        # Generate a random index
        random_index = random.randint(0, total_documents - 1)
        
        # Fetch a random sentence based on the index
        document = coll.find().skip(random_index).limit(1)
        
        if document:
            document = list(document)[0]  # Convert cursor to a single document
            print(f"Fetched index: {random_index}")
            print(f"Found sentence in MongoDB: {document['sentence']}")
            return jsonify({"index": random_index, "sentence": document['sentence']})
        else:
            print("Sentence not found in the database.")
            return jsonify({"sentence": "No sentence found"}), 404

    except Exception as e:
        print(f"Error fetching random sentence: {e}")
        return jsonify({"error": "Error fetching random sentence"}), 500


# Directory to save uploaded audio files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the folder if it doesn't exist

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        index = request.form.get('index')

        if not index:
            return jsonify({"error": "Index not provided"}), 400

        index = int(index)  # Ensure index is an integer

        # Find the document by index
        document = coll.find_one({"index": index})

        if not document:
            return jsonify({"error": "Document not found"}), 404

        # Determine the filename based on the number of existing audio files
        audio_count = len(document.get('audio', []))
        filename = f"{index}_{audio_count + 1}.mp3"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the audio file to the local directory
        file.save(file_path)

        # Update the document in the database with the file path
        coll.update_one(
            {"index": index},
            {"$push": {"audio": filename}}
        )

        return jsonify({"message": "File uploaded and stored", "filename": filename})

    except Exception as e:
        print(f"Error processing file upload: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/get_audio/<int:index>', methods=['GET'])
def get_audio(index):
    try:
        # Find the document with the specified index
        document = coll.find_one({"index": index})
        
        if not document or "audio" not in document:
            return jsonify({"error": "Audio not found"}), 404

        # Retrieve the last audio file in the 'audio' array
        filename = document["audio"][-1]
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        if not os.path.exists(file_path):
            return jsonify({"error": "Audio file does not exist"}), 404

        # Send the audio file back to the client
        return send_file(file_path, mimetype='audio/mpeg', as_attachment=True, download_name=filename)

    except Exception as e:
        print(f"Error retrieving audio: {e}")  # Log the detailed error message
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


@app.route('/random-sentence', methods=['GET'])
def random_sentence():
    try:
        # Generate a random index within the range of your dataset
        max_index = coll.count_documents({})
        if max_index == 0:
            return jsonify({"error": "No documents in the collection"}), 404
        
        # Randomly select a starting index
        random_index = random.randint(0, max_index - 1)

        # Sequentially search for a valid document starting from the random index
        for i in range(random_index, max_index):
            document = coll.find_one({"index": i, "$expr": {"$lte": [{"$size": "$audio"}, 5]}})
            if document:
                document['_id'] = str(document['_id'])
                return jsonify(document)

        # If no valid document is found from the random index to the end, search from the beginning to the random index
        for i in range(random_index):
            document = coll.find_one({"index": i, "$expr": {"$lte": [{"$size": "$audio"}, 5]}})
            if document:
                document['_id'] = str(document['_id'])
                return jsonify(document)

        return jsonify({"error": "No valid document found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
