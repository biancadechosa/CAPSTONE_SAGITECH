from flask import Flask, request, jsonify
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load your model
model = load_model(r'C:\Users\MyPc\CAPSTONE\sagitech\model\banana_ripeness_model.h5')

# Updated class labels
labels = ['1.3_months_old', '3_weeks_before_harvest', '15_days_old']

# Try to get the expected input shape from the model
try:
    # For Sequential models
    if hasattr(model, 'input_shape'):
        input_shape = model.input_shape[1:3]
        print(f"Model expects input shape: {input_shape}")
    else:
        # For functional models, try to get from the first layer's input
        input_shape = (224, 224)  # Default to a common size
        print(f"Could not determine model input shape, using default: {input_shape}")
except Exception as e:
    print(f"Error getting model input shape: {e}")
    input_shape = (224, 224)  # Default to a common size

@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'API is running'})

@app.route('/predict', methods=['POST'])
def predict():
    print("Received request")
    print("Files:", request.files)
    
    if 'file' not in request.files:
        print("No file found in request")
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    try:
        # Use the model's expected input shape instead of hardcoding 150x150
        img = Image.open(file).convert('RGB')
        
        # Print original image size for debugging
        print(f"Original image size: {img.size}")
        
        # Resize to the model's expected input shape
        img = img.resize((input_shape[1], input_shape[0]))  # PIL uses (width, height)
        print(f"Resized to: {img.size}")
        
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        print(f"Input array shape: {img_array.shape}")

        prediction = model.predict(img_array)
        predicted_label = labels[np.argmax(prediction)]
        confidence = float(np.max(prediction))

        return jsonify({'prediction': predicted_label, 'confidence': confidence})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)