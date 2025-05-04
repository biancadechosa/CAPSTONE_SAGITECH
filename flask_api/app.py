from flask import Flask, request, jsonify
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
from flask_cors import CORS
import traceback
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load your model
model_path = r'C:\Users\MyPc\CAPSTONE_SAGITECH\sagitech\model\banana_ripeness_model.h5'
logger.info(f"Loading model from: {model_path}")

try:
    model = load_model(model_path)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    logger.error(traceback.format_exc())
    raise

# IMPORTANT: These are the exact class indices from your model
# The order here MUST match the order used during training
# This is the correct order based on your training code
CLASS_INDICES = {
    0: "1.5_months_old",
    1: "15_days_old",
    2: "3_weeks_before_harvest"
}

logger.info(f"Class indices mapping: {CLASS_INDICES}")

# Try to get the expected input shape from the model
try:
    # For Sequential models
    if hasattr(model, 'input_shape'):
        input_shape = model.input_shape[1:3]
        logger.info(f"Model expects input shape: {input_shape}")
    else:
        # For functional models
        input_shape = (224, 224)  # Default to a common size
        logger.info(f"Using default input shape: {input_shape}")
except Exception as e:
    logger.error(f"Error getting model input shape: {e}")
    input_shape = (224, 224)  # Default to a common size

@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'API is running'})

@app.route('/predict', methods=['POST'])
def predict():
    logger.info("Received prediction request")
    logger.info(f"Files in request: {request.files}")
    
    if 'file' not in request.files:
        logger.warning("No file found in request")
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    if file.filename == '':
        logger.warning("Empty filename")
        return jsonify({'error': 'No file selected'})
    
    try:
        # Process the image
        img = Image.open(file).convert('RGB')
        logger.info(f"Original image size: {img.size}")
        
        # Resize to the model's expected input shape
        img = img.resize((input_shape[1], input_shape[0]))  # PIL uses (width, height)
        logger.info(f"Resized to: {img.size}")
        
        # Normalize the image
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        logger.info(f"Input array shape: {img_array.shape}")

        # Make prediction
        prediction = model.predict(img_array)
        logger.info(f"Raw prediction: {prediction}")
        
        # Get the index of the highest probability
        predicted_index = int(np.argmax(prediction))
        logger.info(f"Predicted index: {predicted_index}")
        
        # Map the index to the corresponding class
        predicted_class = CLASS_INDICES[predicted_index]
        logger.info(f"Predicted class: {predicted_class}")
        
        # Get the confidence score
        confidence = float(np.max(prediction))
        logger.info(f"Confidence: {confidence}")

        # Return the prediction
        response = {
            'prediction': predicted_class,
            'confidence': confidence,
            'predicted_index': predicted_index,
            'all_probabilities': prediction.tolist()[0]
        }
        
        logger.info(f"Sending response: {response}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        })

if __name__ == '__main__':
    logger.info("Starting Flask server")
    app.run(host='0.0.0.0', port=5000, debug=True)

