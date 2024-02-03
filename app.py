from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import os
import glob
import json

app = Flask(__name__)

wardrobe_json = """
{
    "bag": [],
    "belt": [],
    "boots": [],
    "footwear": [],
    "outer": [],
    "dress": [],
    "sunglasses": [],
    "scarf_and_tie": [],
    "pants": [],
    "top": [],
    "shorts": [],
    "skirt": [],
    "headwear": []
}
"""

wardrobe = json.loads(wardrobe_json)

# Function to get the latest folder
def get_latest_folder():
    folders = glob.glob("C:/Users/Redmi/PycharmProjects/DYPLOM/yolov5/runs/detect/exp*")
    if not folders:
        return None
    return max(folders, key=os.path.getctime)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile', methods=['POST'])
def profile():
    if request.method == 'POST':
        name = request.form['name']
        return render_template('profile.html', name=name, wardrobe=wardrobe)

@app.route('/run_yolo_detection', methods=['POST'])
def run_yolo_detection():
    if 'image' in request.files:
        image_file = request.files['image']
        image_path = 'static/uploaded_image.png'
        image_file.save(image_path)

        try:
            command = f'python yolov5/detect.py --weights best.pt --source {image_path} --save-csv --save-txt --save-conf --save-crop'
            subprocess.run(command, shell=True, check=True)

            latest_folder = get_latest_folder()
            if latest_folder:
                output_image_path = os.path.join(latest_folder, 'uploaded_image.png')

                return jsonify(success=True, output_image_path=output_image_path)
            else:
                return jsonify(success=False, error='No output image found')

        except subprocess.CalledProcessError as e:
            return jsonify(success=False, error=str(e))
    else:
        return jsonify(success=False, error='No image uploaded')

@app.route('/get_output_image')
def get_output_image():
    latest_folder = get_latest_folder()

    if latest_folder:
        output_image_path = os.path.join(latest_folder, 'uploaded_image.png')

        return send_file(output_image_path, mimetype='image/png')
    else:
        return jsonify(success=False, error='No output image found')

@app.route('/get_image', methods=['GET'])
def get_image():
    folder = request.args.get('folder')
    image = request.args.get('image')

    latest_folder = get_latest_folder()

    if latest_folder:
        image_path = os.path.join(latest_folder, 'crops', folder, image)
        return send_file(image_path, mimetype='image/png')
    else:
        return jsonify(success=False, error='No latest folder found')

@app.route('/get_folders_and_images', methods=['GET'])
def get_folders_and_images():
    exp_dir = get_latest_folder()
    crops_folders = [d for d in os.listdir(f'{exp_dir}/crops/')]

    folders_and_images = {}

    for folder in crops_folders:
        folder_path = os.path.join(exp_dir, 'crops', folder)
        images = [img for img in os.listdir(folder_path) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]

        folders_and_images[folder] = images
    return jsonify(folders_and_images=folders_and_images, base_path=exp_dir)

@app.route('/add_to_wardrobe', methods=['POST'])
def add_to_wardrobe():
    selected_categories = request.json.get('categories', [])
    selected_paths = request.json.get('paths', [])

    for category, path in zip(selected_categories, selected_paths):
        wardrobe[category].append(path)

    return jsonify(success=True)

@app.route('/delete_selected_from_wardrobe', methods=['POST'])
def delete_selected_from_wardrobe():
    data = request.json.get('data', [])

    for item in data:
        category = item.get('category', '')
        item_name = item.get('itemName', '')

        if category in wardrobe and item_name in wardrobe[category]:
            wardrobe[category].remove(item_name)

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)
