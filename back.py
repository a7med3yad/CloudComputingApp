from flask import Flask, request, jsonify, render_template, send_from_directory
import boto3
from werkzeug.utils import secure_filename
import os
from botocore.exceptions import NoCredentialsError
import io

app = Flask(__name__)

S3_BUCKET = "project-bucket-1910"
S3_REGION = "eu-north-1"

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

s3 = boto3.client("s3", region_name=S3_REGION)

@app.route('/')
def index():
    return render_template("WebApp.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file found"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    
    file_content = file.read()
    file_stream = io.BytesIO(file_content)
    
    try:
        s3.upload_fileobj(file_stream, S3_BUCKET, filename)
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
        return jsonify({"download_link": url})
    
    except NoCredentialsError:
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(local_path, 'wb') as f:
            f.write(file_content)
        url = f"/uploads/{filename}"  # خلي بالك هنا !!
        return jsonify({"download_link": url})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# الحل اللي اتكلمنا عليه
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
