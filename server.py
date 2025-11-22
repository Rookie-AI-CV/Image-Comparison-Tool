from flask import Flask, send_from_directory, jsonify, request, send_file
import os
import json
from datetime import datetime
import sys

app = Flask(__name__)

# Default directories
RAW_DIR = ''
LABELED_DIR = ''
STATE_FILE = 'app_state.json'
CONFIG_DIR = 'configs'  # Directory to store configuration files

# COCO format support
RAW_COCO_DATA = {}  # Store COCO annotation data for raw images
LABELED_COCO_DATA = {}  # Store COCO annotation data for labeled images

# Get the base directory for the application
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle
    BASE_DIR = sys._MEIPASS
else:
    # If the application is run from a Python interpreter
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            return state
    except:
        return None

# Initialize saved_images from state
saved_images = set()
state = load_state()
if state:
    saved_images = set(state.get('saved_images', []))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'image_comparison.html')

def is_coco_file(path):
    """Check if path is a COCO annotation file"""
    return os.path.isfile(path) and path.endswith('_annotations.coco.json')

def load_coco_data(coco_file_path):
    """Load and parse COCO format annotation file, return (coco_data_dict, image_dir)"""
    try:
        with open(coco_file_path, 'r', encoding='utf-8') as f:
            coco_data = json.load(f)
        
        # Get image directory (same directory as COCO file)
        image_dir = os.path.dirname(coco_file_path)
        
        # Build image filename to image_id mapping
        image_id_to_filename = {}
        for img in coco_data.get('images', []):
            image_id_to_filename[img['id']] = img['file_name']
        
        # Build category id to name mapping
        category_id_to_name = {}
        for cat in coco_data.get('categories', []):
            category_id_to_name[cat['id']] = cat['name']
        
        # Group annotations by image_id
        coco_data_dict = {}
        for ann in coco_data.get('annotations', []):
            image_id = ann['image_id']
            filename = image_id_to_filename.get(image_id)
            if filename:
                if filename not in coco_data_dict:
                    coco_data_dict[filename] = {
                        'annotations': [],
                        'categories': category_id_to_name
                    }
                
                # Convert bbox from [x, y, width, height] to format we need
                bbox = ann.get('bbox', [])
                if len(bbox) == 4:
                    annotation = {
                        'id': ann['id'],
                        'category_id': ann.get('category_id'),
                        'category_name': category_id_to_name.get(ann.get('category_id'), 'Unknown'),
                        'bbox': bbox,  # [x, y, width, height]
                        'area': ann.get('area', 0),
                        'iscrowd': ann.get('iscrowd', 0)
                    }
                    coco_data_dict[filename]['annotations'].append(annotation)
        
        print(f"Loaded COCO data: {len(coco_data_dict)} images with annotations")
        return (coco_data_dict, image_dir)
    except Exception as e:
        print(f"Error loading COCO file: {str(e)}")
        return (None, None)

@app.route('/set_directories', methods=['POST'])
def set_directories():
    global RAW_DIR, LABELED_DIR, RAW_COCO_DATA, LABELED_COCO_DATA
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        raw_dir = data.get('raw_dir', '')
        labeled_dir = data.get('labeled_dir', '')
        
        if not raw_dir or not labeled_dir:
            return jsonify({'error': 'Both raw_dir and labeled_dir are required'}), 400
        
        # Check if either path is a COCO file
        is_raw_coco = is_coco_file(raw_dir)
        is_labeled_coco = is_coco_file(labeled_dir)
        
        # 处理 raw_dir
        if is_raw_coco:
            if not os.path.exists(raw_dir):
                return jsonify({'error': f'COCO file does not exist: {raw_dir}'}), 400
            coco_data, image_dir = load_coco_data(raw_dir)
            if coco_data is None:
                return jsonify({'error': f'Failed to load or parse COCO file: {raw_dir}. Please check if it is a valid COCO format JSON file.'}), 400
            if not image_dir or not os.path.exists(image_dir):
                return jsonify({'error': f'Image directory not found for COCO file: {image_dir}'}), 400
            RAW_COCO_DATA = coco_data
            RAW_DIR = image_dir
        else:
            if not os.path.exists(raw_dir):
                return jsonify({'error': f'Raw directory does not exist: {raw_dir}'}), 400
            if not os.path.isdir(raw_dir):
                return jsonify({'error': f'Raw path is not a directory: {raw_dir}'}), 400
            RAW_DIR = raw_dir
            RAW_COCO_DATA = {}  # 清空 raw COCO 数据
        
        # 处理 labeled_dir
        if is_labeled_coco:
            if not os.path.exists(labeled_dir):
                return jsonify({'error': f'COCO file does not exist: {labeled_dir}'}), 400
            coco_data, image_dir = load_coco_data(labeled_dir)
            if coco_data is None:
                return jsonify({'error': f'Failed to load or parse COCO file: {labeled_dir}. Please check if it is a valid COCO format JSON file.'}), 400
            if not image_dir or not os.path.exists(image_dir):
                return jsonify({'error': f'Image directory not found for COCO file: {image_dir}'}), 400
            LABELED_COCO_DATA = coco_data
            LABELED_DIR = image_dir
        else:
            if not os.path.exists(labeled_dir):
                return jsonify({'error': f'Labeled directory does not exist: {labeled_dir}'}), 400
            if not os.path.isdir(labeled_dir):
                return jsonify({'error': f'Labeled path is not a directory: {labeled_dir}'}), 400
            LABELED_DIR = labeled_dir
            LABELED_COCO_DATA = {}  # 清空 labeled COCO 数据
        
        save_state()
        
        return jsonify({
            'message': 'Directories set successfully',
            'is_raw_coco': is_raw_coco,
            'is_labeled_coco': is_labeled_coco
        })
    except Exception as e:
        print(f"Error in set_directories: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/get_images')
def get_images():
    if not RAW_DIR or not LABELED_DIR:
        print("Directories not set")
        return jsonify([])
    
    try:
        import fnmatch

        # If COCO format is loaded, use images from COCO data
        # 优先使用 raw COCO 数据，如果没有则使用 labeled COCO 数据
        if RAW_COCO_DATA:
            coco_images = sorted(list(RAW_COCO_DATA.keys()))
            print(f"Raw COCO images found: {len(coco_images)}")
            return jsonify(coco_images)
        elif LABELED_COCO_DATA:
            coco_images = sorted(list(LABELED_COCO_DATA.keys()))
            print(f"Labeled COCO images found: {len(coco_images)}")
            return jsonify(coco_images)

        # Helper to recursively collect image files
        def get_image_files(base_dir):
            image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.tiff', '*.webp']
            files = set()
            for root, dirs, filenames in os.walk(base_dir):
                for pattern in image_extensions:
                    for filename in fnmatch.filter(filenames, pattern):
                        # use relative path from base_dir for cross dir matching
                        rel_path = os.path.relpath(os.path.join(root, filename), base_dir)
                        files.add(rel_path)
            return files

        # Recursively get files from RAW_DIR and LABELED_DIR
        raw_files = get_image_files(RAW_DIR)
        print(f"Raw files found (recursive): {len(raw_files)}")

        labeled_files = get_image_files(LABELED_DIR)
        print(f"Labeled files found (recursive): {len(labeled_files)}")

        # Intersection of files (files with same relative path in both)
        common_files = sorted(list(raw_files.intersection(labeled_files)))
        print(f"Common files found (recursive): {len(common_files)}")

        return jsonify(common_files)
    except Exception as e:
        print(f"Error getting images: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/get_annotations/<path:filename>')
def get_annotations(filename):
    """Get COCO annotations for a specific image"""
    # 尝试从 raw COCO 数据获取
    if filename in RAW_COCO_DATA:
        return jsonify(RAW_COCO_DATA[filename])
    # 尝试从 labeled COCO 数据获取
    if filename in LABELED_COCO_DATA:
        return jsonify(LABELED_COCO_DATA[filename])
    return jsonify({'annotations': [], 'categories': {}})

@app.route('/get_raw_annotations/<path:filename>')
def get_raw_annotations(filename):
    """Get COCO annotations for raw image"""
    if filename in RAW_COCO_DATA:
        return jsonify(RAW_COCO_DATA[filename])
    return jsonify({'annotations': [], 'categories': {}})

@app.route('/get_labeled_annotations/<path:filename>')
def get_labeled_annotations(filename):
    """Get COCO annotations for labeled image"""
    if filename in LABELED_COCO_DATA:
        return jsonify(LABELED_COCO_DATA[filename])
    return jsonify({'annotations': [], 'categories': {}})

@app.route('/get_all_raw_annotations', methods=['POST'])
def get_all_raw_annotations():
    """Get all raw COCO annotations at once"""
    data = request.get_json()
    filenames = data.get('filenames', [])
    result = {}
    for filename in filenames:
        if filename in RAW_COCO_DATA:
            result[filename] = RAW_COCO_DATA[filename]
        else:
            result[filename] = {'annotations': [], 'categories': {}}
    return jsonify(result)

@app.route('/get_all_labeled_annotations', methods=['POST'])
def get_all_labeled_annotations():
    """Get all labeled COCO annotations at once"""
    data = request.get_json()
    filenames = data.get('filenames', [])
    result = {}
    for filename in filenames:
        if filename in LABELED_COCO_DATA:
            result[filename] = LABELED_COCO_DATA[filename]
        else:
            result[filename] = {'annotations': [], 'categories': {}}
    return jsonify(result)

if __name__ == '__main__':
    # Run in debug mode only when not packaged
    debug_mode = not getattr(sys, 'frozen', False)
    app.run(debug=debug_mode) 