import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from mistralai import Mistral
from werkzeug.utils import secure_filename

app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})



UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_receipt_with_ai(client, ocr_text):
    """
    Use Mistral AI to parse the OCR text into a structured format with items and prices.
    """
    prompt = f"""
    You are a receipt parsing assistant. Extract all items and their prices from the following receipt text.
    For each item, identify:
    1. Item name
    2. Price
    3. Quantity (if specified)

    If an item has a quantity (like "Coffee x2"), split it into individual items with the appropriate price per item.

    Return the results as a JSON array of items with the format:
    [
      {{
        "name": "Item Name",
        "price": 0.00,
        "original_text": "original line from receipt"
      }}
    ]

    Receipt text:
    {ocr_text}
    """

    response = client.chat.completions.create(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract the JSON from the response
    ai_response = response.choices[0].message.content

    # Find JSON array in the response
    import re
    json_match = re.search(r'\[\s*\{.*\}\s*\]', ai_response, re.DOTALL)

    if json_match:
        try:
            items = json.loads(json_match.group(0))
            return items
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return []

    return []


@app.route('/process-receipt', methods=['POST'])
def process_receipt():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # If user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Process with Mistral OCR API
            api_key = os.environ.get("MISTRAL_API_KEY")
            if not api_key:
                return jsonify({'error': 'Mistral API key not found in environment variables'}), 500

            # Create client using the current Mistral package structure
            client = Mistral(api_key=api_key)

            with open(filepath, 'rb') as f:
                file_bytes = f.read()

            # Upload the file first
            uploaded_file = client.files.upload(
                file={
                    "file_name": filename,
                    "content": file_bytes,
                },
                purpose="ocr"
            )

            # Process with OCR
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "file_id",
                    "file_id": uploaded_file.id
                }
            )

            # Extract text content from the OCR response
            ocr_text = ""
            for page in ocr_response.pages:
                ocr_text += page.markdown + "\n"

            # Parse the receipt using AI
            items = parse_receipt_with_ai(client, ocr_text)

            # Clean up the uploaded file
            client.files.delete(file_id=uploaded_file.id)

            # Return the parsed items
            return jsonify({
                'success': True,
                'raw_text': ocr_text,
                'items': items
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File type not allowed'}), 400


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)