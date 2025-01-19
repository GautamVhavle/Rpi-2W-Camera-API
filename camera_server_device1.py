import os
import base64
import subprocess

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage of tasks
tasks = {}

# We'll hardcode the device ID for clarity
DEVICE_ID = 1

@app.route('/task', methods=['POST', 'GET'])
def task_handler():
    """
    POST /task
      - Expects JSON with at least:
         {
           "task_id": 12345,
           "custom_column": "some_value",
           "camera": "CAM1"  (or any identifier)
         }
      - Captures an image, encodes it as Base64, and stores it along with the task data.
      - Returns a JSON response with the stored task.

    GET /task
      - Returns all stored tasks with their Base64 images.
    """

    if request.method == 'POST':
        data = request.json or {}

        # Required fields (excluding 'image' since we capture automatically)
        required_fields = ['task_id', 'custom_column', 'camera']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        task_id = str(data['task_id'])  # Convert to string to use as dict key
        custom_column = data['custom_column']
        camera = data['camera']

        # 1) Capture the image using libcamera-still
        image_filename = f"device_{DEVICE_ID}_capture.jpg"
        try:
            subprocess.run(
                ["libcamera-still", "-n", "-o", image_filename],
                check=True
            )
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Image capture failed: {str(e)}"}), 500

        # 2) Convert the captured image to Base64
        if os.path.isfile(image_filename):
            with open(image_filename, "rb") as img_file:
                encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
        else:
            return jsonify({"error": "Image file not found after capture"}), 500

        # 3) Store the task in the in-memory dictionary
        tasks[task_id] = {
            "device_id": DEVICE_ID,
            "custom_column": custom_column,
            "camera": camera,
            "image": encoded_image  # Base64 encoded string
        }

        # 4) Return a success response
        return jsonify({
            "message": "Task added successfully",
            "task": tasks[task_id]
        }), 201

    elif request.method == 'GET':
        # Return all tasks in JSON format
        return jsonify(tasks), 200

@app.route('/status', methods=['GET'])
def status():
    """Quick check to see if the server is running and identify the device."""
    return jsonify({
        "status": "Device 1 is online",
        "device_id": DEVICE_ID
    }), 200

if __name__ == '__main__':
    # Default port is 8000 unless overridden by environment variable PORT
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', debug=True, port=port)
