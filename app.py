from flask import Flask, request, jsonify, render_template, send_from_directory
import boto3
from werkzeug.utils import secure_filename
import os
from botocore.exceptions import NoCredentialsError
import io

app = Flask(__name__)

# AWS Configuration
S3_BUCKET = ""
S3_REGION = ""
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""

# Local uploads fallback
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create S3 client with credentials
s3 = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

@app.route('/')
def index():
    return render_template("index.html")

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
        print(f"Uploaded to S3: {url}")
        return jsonify({"download_link": url})

    except NoCredentialsError as e:
        print("No AWS credentials found:", str(e))
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(local_path, 'wb') as f:
            f.write(file_content)
        url = f"/uploads/{filename}"
        return jsonify({"download_link": url})

    except Exception as e:
        print("Upload failed:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/get-files', methods=['GET'])
def get_files():
    try:
        # Fetch list of objects in the S3 bucket
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        
        if 'Contents' not in response:
            return jsonify({"message": "No files found in the bucket"}), 404

        # Prepare list of files and their URLs
        files = [
            {
                "name": file['Key'],
                "url": f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file['Key']}"
            }
            for file in response['Contents']
        ]
        
        return jsonify(files)

    except NoCredentialsError as e:
        return jsonify({"error": "No AWS credentials found"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
