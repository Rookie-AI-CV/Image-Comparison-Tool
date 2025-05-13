from flask import Flask, send_from_directory, jsonify, request, send_file
import os
import json
from datetime import datetime

app = Flask(__name__)

# Default directories
RAW_DIR = ''
LABELED_DIR = ''
STATE_FILE = 'app_state.json'
CONFIG_DIR = 'configs'  # Directory to store configuration files

# Create configs directory if it doesn't exist
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

def save_state():
    state = {
        'raw_dir': RAW_DIR,
        'labeled_dir': LABELED_DIR,
        'saved_images': list(saved_images)
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return None

@app.route('/')
def index():
    return send_from_directory('.', 'image_comparison.html')

@app.route('/get_absolute_path', methods=['POST'])
def get_absolute_path():
    data = request.get_json()
    relative_path = data.get('path', '')
    
    if not relative_path:
        return jsonify({'error': 'No path provided'}), 400
    
    try:
        # Get the absolute path
        abs_path = os.path.abspath(relative_path)
        return jsonify({'path': abs_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/set_directories', methods=['POST'])
def set_directories():
    global RAW_DIR, LABELED_DIR
    data = request.get_json()
    
    raw_dir = data.get('raw_dir', '')
    labeled_dir = data.get('labeled_dir', '')
    
    if not os.path.exists(raw_dir) or not os.path.exists(labeled_dir):
        return jsonify({'error': 'One or both directories do not exist'}), 400
    
    RAW_DIR = raw_dir
    LABELED_DIR = labeled_dir
    save_state()
    
    return jsonify({'message': 'Directories set successfully'})

@app.route('/get_images')
def get_images():
    if not RAW_DIR or not LABELED_DIR:
        return jsonify([])
    
    # Get list of files from raw directory
    raw_files = set(f for f in os.listdir(RAW_DIR) if os.path.isfile(os.path.join(RAW_DIR, f)))
    # Get list of files from labeled directory
    labeled_files = set(f for f in os.listdir(LABELED_DIR) if os.path.isfile(os.path.join(LABELED_DIR, f)))
    
    # Get intersection of files that exist in both directories
    common_files = sorted(list(raw_files.intersection(labeled_files)))
    
    return jsonify(common_files)

@app.route('/raw/<path:filename>')
def serve_raw_image(filename):
    return send_from_directory(RAW_DIR, filename)

@app.route('/labeled/<path:filename>')
def serve_labeled_image(filename):
    return send_from_directory(LABELED_DIR, filename)

@app.route('/save_problematic', methods=['POST'])
def save_problematic():
    data = request.get_json()
    image = data.get('image')
    
    if not image:
        return jsonify({'error': 'No image specified'}), 400
    
    if not RAW_DIR:
        return jsonify({'error': 'Raw directory not set'}), 400
    
    try:
        saved_images.add(image)
        save_state()
        return jsonify({'message': 'Image saved successfully'})
    except Exception as e:
        print(f"Error saving problematic image: {str(e)}")
        return jsonify({'error': f'Failed to save image: {str(e)}'}), 500

@app.route('/remove_problematic', methods=['POST'])
def remove_problematic():
    data = request.get_json()
    image = data.get('image')
    
    if not image:
        return jsonify({'error': 'No image specified'}), 400
    
    try:
        saved_images.discard(image)
        save_state()
        return jsonify({'message': 'Image removed successfully'})
    except Exception as e:
        print(f"Error removing problematic image: {str(e)}")
        return jsonify({'error': f'Failed to remove image: {str(e)}'}), 500

@app.route('/export_problematic')
def export_problematic():
    if not saved_images:
        return jsonify({'error': 'No problematic images to export'}), 400
    
    # Create a text file with the list of problematic images
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'problematic_images_{timestamp}.txt'
    
    with open(filename, 'w') as f:
        for image in sorted(saved_images):
            f.write(f'{image}\n')
    
    return send_file(filename, as_attachment=True)

@app.route('/get_state')
def get_state():
    state = load_state()
    if state:
        return jsonify(state)
    return jsonify({'raw_dir': '', 'labeled_dir': '', 'saved_images': []})

@app.route('/save_config', methods=['POST'])
def save_config():
    data = request.get_json()
    config_name = data.get('name', '')
    config_path = data.get('path', '')
    
    if not config_name:
        return jsonify({'error': 'Configuration name is required'}), 400
    
    try:
        # Create config object
        config = {
            'raw_dir': RAW_DIR,
            'labeled_dir': LABELED_DIR,
            'saved_images': list(saved_images),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to specified path or default configs directory
        if config_path:
            save_path = os.path.join(config_path, f'{config_name}.json')
        else:
            save_path = os.path.join(CONFIG_DIR, f'{config_name}.json')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({'message': 'Configuration saved successfully', 'path': save_path})
    except Exception as e:
        return jsonify({'error': f'Failed to save configuration: {str(e)}'}), 500

@app.route('/load_config', methods=['POST'])
def load_config():
    data = request.get_json()
    config_path = data.get('path', '')
    
    if not config_path:
        return jsonify({'error': 'Configuration path is required'}), 400
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update global state
        global RAW_DIR, LABELED_DIR, saved_images
        RAW_DIR = config.get('raw_dir', '')
        LABELED_DIR = config.get('labeled_dir', '')
        saved_images = set(config.get('saved_images', []))
        
        # Save to current state
        save_state()
        
        return jsonify({
            'message': 'Configuration loaded successfully',
            'raw_dir': RAW_DIR,
            'labeled_dir': LABELED_DIR,
            'saved_images': list(saved_images)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to load configuration: {str(e)}'}), 500

@app.route('/list_configs')
def list_configs():
    try:
        configs = []
        for filename in os.listdir(CONFIG_DIR):
            if filename.endswith('.json'):
                config_path = os.path.join(CONFIG_DIR, filename)
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    configs.append({
                        'name': os.path.splitext(filename)[0],
                        'path': config_path,
                        'timestamp': config.get('timestamp', ''),
                        'raw_dir': config.get('raw_dir', ''),
                        'labeled_dir': config.get('labeled_dir', ''),
                        'saved_images_count': len(config.get('saved_images', []))
                    })
        return jsonify(sorted(configs, key=lambda x: x['timestamp'], reverse=True))
    except Exception as e:
        return jsonify({'error': f'Failed to list configurations: {str(e)}'}), 500

# Initialize saved_images set
saved_images = set()
# Load saved state if exists
saved_state = load_state()
if saved_state:
    RAW_DIR = saved_state.get('raw_dir', '')
    LABELED_DIR = saved_state.get('labeled_dir', '')
    saved_images = set(saved_state.get('saved_images', []))

if __name__ == '__main__':
    app.run(debug=True) 