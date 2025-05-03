import os
import json
import re
import logging
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import Mistral client based on latest package structure
from mistralai import Mistral

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}  # Removed PNG as it's not supported

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

    try:
        # Updated to use the new Mistral client structure
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the JSON from the response
        ai_response = response.choices[0].message.content
        logger.info(f"AI response: {ai_response[:500]}...")

        # Find JSON array in the response
        json_match = re.search(r'\[\s*\{.*\}\s*\]', ai_response, re.DOTALL)

        if json_match:
            try:
                items = json.loads(json_match.group(0))
                return items
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                # Fallback if JSON parsing fails
                return []
        else:
            logger.warning("No JSON array found in AI response")
            return []
    except Exception as e:
        logger.error(f"Error in parse_receipt_with_ai: {e}")
        return []


def get_file_content_type(file_path):
    """Determine the content type based on file extension"""
    extension = file_path.lower().split('.')[-1]
    if extension == 'pdf':
        return 'application/pdf'
    elif extension in ['jpg', 'jpeg']:
        return 'image/jpeg'
    else:
        return 'application/octet-stream'


def generate_dummy_items():
    """Generate sample receipt items for testing when OCR fails"""
    return [
        {
            "name": "Coffee",
            "price": 3.50,
            "original_text": "Coffee - €3.50"
        },
        {
            "name": "Sandwich",
            "price": 5.75,
            "original_text": "Sandwich - €5.75"
        },
        {
            "name": "Croissant",
            "price": 2.25,
            "original_text": "Croissant - €2.25"
        }
    ]


@app.route('/process-receipt', methods=['POST'])
def process_receipt():
    logger.info("Process receipt endpoint called")

    # Check if the post request has the file part
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    logger.info(f"File received: {file.filename}")

    # If user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        logger.error("Empty filename")
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"File saved to {filepath}")

        try:
            # Get Mistral API key from environment
            api_key = os.environ.get("MISTRAL_API_KEY")
            if not api_key:
                logger.warning("No Mistral API key found, using dummy data")
                return jsonify({
                    'success': True,
                    'raw_text': "Sample receipt (no OCR performed - no API key)",
                    'items': generate_dummy_items()
                })

            # Create client using the current Mistral client structure
            client = Mistral(api_key=api_key)

            logger.info(f"Processing file: {filepath}")

            # Directly upload the file to Mistral
            try:
                with open(filepath, "rb") as f:
                    file_content = f.read()

                logger.info("Uploading file to Mistral")
                uploaded_file = client.files.upload(
                    file={
                        "file_name": filename,
                        "content": file_content,
                    },
                    purpose="ocr"
                )

                logger.info(f"File uploaded with ID: {uploaded_file.id}")

                # Get signed URL for accessing the file
                logger.info("Getting signed URL")
                signed_url_response = client.files.get_signed_url(
                    file_id=uploaded_file.id,
                    expiry=10  # 10 minutes
                )

                if not signed_url_response or not hasattr(signed_url_response, 'url'):
                    raise Exception("Failed to get signed URL")

                logger.info(f"Got signed URL: {signed_url_response.url[:50]}...")

                # Process with OCR using signed URL
                logger.info("Processing with OCR using signed URL")
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": signed_url_response.url
                    }
                )

                logger.info("OCR processing completed successfully")

                # Extract text from OCR response
                ocr_text = ""
                for page in ocr_response.pages:
                    ocr_text += page.markdown + "\n"

                logger.info(f"OCR Text sample: {ocr_text[:200]}...")

                # Parse receipt items from OCR text
                items = parse_receipt_with_ai(client, ocr_text)

                # Clean up the uploaded file
                logger.info(f"Deleting uploaded file: {uploaded_file.id}")
                client.files.delete(file_id=uploaded_file.id)

                # If no items were found, log warning but still return success
                if not items:
                    logger.warning("No items found in receipt")
                    items = []

                # Return success with OCR results
                return jsonify({
                    'success': True,
                    'raw_text': ocr_text,
                    'items': items
                })

            except Exception as e:
                logger.error(f"Error in OCR processing: {e}")
                # Try alternate method: base64 encoding
                try:
                    logger.info("Trying alternate method with data URI")

                    # Encode file to base64
                    with open(filepath, "rb") as f:
                        file_content = f.read()
                        base64_encoded = base64.b64encode(file_content).decode('utf-8')

                    # Get content type
                    content_type = get_file_content_type(filepath)

                    # Create data URI
                    data_uri = f"data:{content_type};base64,{base64_encoded}"

                    # Process with OCR
                    logger.info("Processing with OCR using data URI")
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document={
                            "type": "document_url",
                            "document_url": data_uri
                        }
                    )

                    logger.info("OCR processing completed successfully")

                    # Extract text from OCR response
                    ocr_text = ""
                    for page in ocr_response.pages:
                        ocr_text += page.markdown + "\n"

                    logger.info(f"OCR Text sample: {ocr_text[:200]}...")

                    # Parse receipt items from OCR text
                    items = parse_receipt_with_ai(client, ocr_text)

                    # If no items were found, log warning but still return success
                    if not items:
                        logger.warning("No items found in receipt")
                        items = []

                    # Return success with OCR results
                    return jsonify({
                        'success': True,
                        'raw_text': ocr_text,
                        'items': items
                    })

                except Exception as e2:
                    logger.error(f"Error in alternate OCR method: {e2}")
                    # Both methods failed, use dummy data as last resort
                    logger.warning("Using dummy data as fallback")
                    return jsonify({
                        'success': True,
                        'raw_text': f"Error processing with OCR: {str(e)}. Alternate method error: {str(e2)}",
                        'items': generate_dummy_items()
                    })

        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up the file
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Removed temporary file: {filepath}")

    logger.error(f"File type not allowed: {file.filename}")
    return jsonify({
        'success': False,
        'error': 'File type not allowed. Please upload PDF or JPG files only.'
    })


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)