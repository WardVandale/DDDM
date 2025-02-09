from flask import Flask, jsonify, request, render_template, url_for
import os
import json
import glob
app = Flask(__name__)

# Configuration paths
UPLOAD_FOLDER = 'static/uploads'
GAMES_FOLDER = 'static/games'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GAMES_FOLDER'] = GAMES_FOLDER

# Check if the folder exists, and create it if it doesn't
if not os.path.exists(GAMES_FOLDER):
    os.makedirs(GAMES_FOLDER)
    print(f"Folder '{GAMES_FOLDER}' created.")
else:
    print(f"Folder '{GAMES_FOLDER}' already exists.")


# In-memory storage for messages
messages = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/getGames', methods=['GET'])
def get_games():
    try:
        games = []

        # Scan the GAMES_FOLDER for game directories
        for game_folder_name in os.listdir(GAMES_FOLDER):
            game_folder_path = os.path.join(GAMES_FOLDER, game_folder_name)
            if os.path.isdir(game_folder_path):
                thumbnail_path = None

                # Find a file named "thumbnail.*" directly in the game folder
                thumbnail_files = glob.glob(os.path.join(game_folder_path, 'thumbnail.*'))
                if thumbnail_files:
                    thumbnail_path = thumbnail_files[0].replace("\\", "/")

                games.append({
                    "name": game_folder_name,
                    "thumbnail": thumbnail_path if thumbnail_path else ""
                })

        return jsonify(games), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/getGames/<gameTitle>', methods=['GET'])
def get_game_data(gameTitle):
    game_folder_path = os.path.join(GAMES_FOLDER, gameTitle)
    data_json_path = os.path.join(game_folder_path, 'data.json')

    if not os.path.isfile(data_json_path):
        return jsonify({"error": f"No data.json found for game '{gameTitle}'"}), 404

    try:
        with open(data_json_path, 'r') as file:
            game_data = json.load(file)
        return jsonify(game_data), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to decode JSON"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/createGame', methods=['POST'])
def create_game():
    game_name = request.form.get('gameName')
    thumbnail = request.files.get('thumbnail')

    if not game_name or not thumbnail:
        return jsonify({"error": "Game name and thumbnail are required"}), 400

    game_folder_path = os.path.join(app.config['GAMES_FOLDER'], game_name)

    # Create game directory and its subdirectories
    os.makedirs(os.path.join(game_folder_path, 'images'), exist_ok=True)
    os.makedirs(os.path.join(game_folder_path, 'sounds'), exist_ok=True)

    thumbnail_filename = "thumbnail." + thumbnail.filename.split('.')[-1]
    thumbnail_path = os.path.join(game_folder_path, thumbnail_filename)
    thumbnail.save(thumbnail_path)

    # Initialize data.json with an empty images list
    with open(os.path.join(game_folder_path, 'data.json'), 'w') as file:
        json.dump({"images": [], "sounds":[]}, file, indent=4)

    return jsonify({"message": "Game created successfully"}), 201

@app.route('/upload-text-voice', methods=['POST'])
def upload_text_voice():
    # Retrieve text and file from the request
    text_content = request.form.get('text')
    voice_file = request.files.get('voice')
    game_name = request.form.get('gameName')

    if not text_content or not voice_file or not game_name:
        return jsonify({'result': False, 'error': 'Text, voice file, and game name are required'}), 400

    # Define the paths based on the game name
    game_folder_path = os.path.join(app.config['GAMES_FOLDER'], game_name)
    sounds_folder_path = os.path.join(game_folder_path, 'sounds')
    data_json_path = os.path.join(game_folder_path, 'data.json')

    # Ensure the sounds folder exists
    os.makedirs(sounds_folder_path, exist_ok=True)

    # Secure the filename and save the file in the sounds folder
    voice_filename = voice_file.filename
    voice_path = os.path.join(sounds_folder_path, voice_filename)
    voice_file.save(voice_path)

    # Prepare the sound entry with the relative path for JSON
    sound_entry = {
        "text": text_content,
        "soundclip": url_for('static', filename=f'games/{game_name}/sounds/{voice_filename}', _external=False)
    }

    # Load or initialize data.json
    if os.path.exists(data_json_path):
        with open(data_json_path, 'r') as file:
            data = json.load(file)
    else:
        data = {"sounds": []}

    # Ensure "sounds" key exists in data.json
    if "sounds" not in data:
        data["sounds"] = []

    # Append the new sound entry and save it to data.json
    data['sounds'].append(sound_entry)
    with open(data_json_path, 'w') as file:
        json.dump(data, file, indent=4)

    return jsonify({'result': True, 'message': 'Text and voice uploaded successfully'}), 200

@app.route('/upload-image', methods=['POST'])
def upload_image():
    game_name = request.form.get('gameName')
    image_file = request.files.get('image')

    if not game_name or not image_file:
        return jsonify({'error': 'Game name and image file are required'}), 400

    # Secure the image filename and define the folder paths
    image_name = image_file.filename
    game_folder_path = os.path.join(app.config['GAMES_FOLDER'], game_name)
    images_folder_path = os.path.join(game_folder_path, 'images')
    data_json_path = os.path.join(game_folder_path, 'data.json')

    # Ensure the images directory exists
    os.makedirs(images_folder_path, exist_ok=True)

    # Save the image file to the specified path
    image_file_path = os.path.join(images_folder_path, image_name)
    image_file.save(image_file_path)

    # Prepare the image data with the relative path
    image_data = {
        "image_name": url_for('static', filename=f'games/{game_name}/images/{image_name}', _external=False),
        "image_size": 100,
        "isLanding": False
    }

    # Load or initialize data.json for the game
    if os.path.exists(data_json_path):
        with open(data_json_path, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {"images": []}

    # Append the new image data and save it back to data.json
    data['images'].append(image_data)
    with open(data_json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    return jsonify({'result': True})

import os
import json
import urllib.parse  # Import for decoding %20
from flask import Flask, request, jsonify

@app.route('/remove-image', methods=['DELETE'])
def remove_image():
    try:
        data = request.get_json()
        game_name = data.get('gameName')
        image_name = data.get('imageName')

        if not game_name or not image_name:
            return jsonify({'error': 'Game name and image name are required'}), 400

        # Decode %20 to spaces
        image_name = urllib.parse.unquote(image_name)

        # Define paths
        game_folder_path = os.path.join(app.config['GAMES_FOLDER'], game_name)
        images_folder_path = os.path.join(game_folder_path, 'images')
        data_json_path = os.path.join(game_folder_path, 'data.json')
        image_file_path = os.path.join(images_folder_path, os.path.basename(image_name))  # Ensure we extract only the filename

        # Debugging: Print paths
        print(f"Decoded Image Name: {image_name}")
        print(f"Full Image Path: {image_file_path}")

        # Check if the image exists and remove it
        if os.path.exists(image_file_path):
            os.remove(image_file_path)
            print(f"Deleted Image: {image_file_path}")
        else:
            print(f"Image not found: {image_file_path}")
            return jsonify({'error': 'Image file not found'}), 404

        # Update data.json by removing the image entry
        if os.path.exists(data_json_path):
            with open(data_json_path, 'r') as json_file:
                data = json.load(json_file)

            # Filter out the image entry
            new_images = [img for img in data.get('images', []) if os.path.basename(urllib.parse.unquote(img['image_name'])) != image_name]

            print(f"Updated Images List: {new_images}")

            data['images'] = new_images

            # Save the updated data.json
            with open(data_json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

        return jsonify({'result': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_updates', methods=['GET'])
def get_updates():
    return jsonify({'result': True, 'messages': messages}) if messages else jsonify({'result': False})


# Route to get available images and sounds for a selected game
@app.route('/getSoundTexts/<selectedGameName>', methods=['GET'])
def get_sound_texts(selectedGameName):
    # Path to the game's data.json file
    data_file_path = os.path.join('static', 'games', selectedGameName, 'data.json')

    # Read data.json file
    with open(data_file_path, 'r') as f:
        data = json.load(f)

    # Return images and sounds data
    return jsonify({
        "sounds": data.get("sounds", [])
    })

@app.route('/update-sound-text', methods=['POST'])
def update_sound_text():
    global messages
    data = request.json
    game_name = data.get('gameName')
    soundclip = data.get('soundclip')
    new_text = data.get('text')

    if not game_name or not soundclip or new_text is None:
        return jsonify({'result': False, 'error': 'Game name, soundclip, and text are required'}), 400

    # Path to the game's data.json
    game_folder_path = os.path.join(app.config['GAMES_FOLDER'], game_name)
    data_json_path = os.path.join(game_folder_path, 'data.json')

    # Load data.json
    if os.path.exists(data_json_path):
        with open(data_json_path, 'r') as file:
            game_data = json.load(file)
    else:
        return jsonify({'result': False, 'error': 'Game data not found'}), 404

    # Find and update the sound entry
    sound_updated = False
    for sound in game_data.get('sounds', []):
        if sound['soundclip'] == soundclip:
            sound['text'] = new_text
            sound_updated = True
            break

    # Save the updated data.json
    if sound_updated:
        with open(data_json_path, 'w') as file:
            json.dump(game_data, file, indent=4)
        messages = [{'type': 'text', 'content': new_text}]
        return jsonify({'result': True, 'message': 'Sound text updated successfully'})
    else:
        return jsonify({'result': False, 'error': 'Soundclip not found'}), 404


# Route to get available images and sounds for a selected game
@app.route('/getImages/<selectedGameName>', methods=['GET'])
def get_images(selectedGameName):
    # Path to the game's data.json file
    data_file_path = os.path.join('static', 'games', selectedGameName, 'data.json')

    # Read data.json file
    with open(data_file_path, 'r') as f:
        data = json.load(f)

    # Return images and sounds data
    return jsonify({
        "images": data.get("images", [])
    })

# Route to update image details
@app.route('/updateImage/<selectedGameName>', methods=['POST'])
def update_image(selectedGameName):
    global messages
    # Path to the game's data.json file
    data_file_path = os.path.join('static', 'games', selectedGameName, 'data.json')
    

    # Get the update data from the request
    update_data = request.json

    with open(data_file_path, 'r+') as f:
        data = json.load(f)
        
        # Find the image to update
        image_found = False
        for image in data.get("images", []):
            if image['image_name'] == update_data['image_name']:
                image['image_size'] = update_data['image_size']
                image['isLanding'] = update_data['isLanding']
                image_found = True
                break
        

        # Ensure only one image can have isLanding set to True
        if update_data['isLanding']:
            for image in data['images']:
                if image['image_name'] != update_data['image_name']:
                    image['isLanding'] = False

        # Write updated data back to the file
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    return jsonify({"message": "Image updated successfully"}), 200




@app.route('/api/send_text', methods=['POST'])
def send_text():
    global messages
    data = request.json
    content = data.get('content')
    
    if content:
        messages = [{'type': 'text', 'content': content}]
        return jsonify({'result': True})
    return jsonify({'result': False, 'error': 'No text content'}), 400


# Endpoint to send the selected image based on updated details
@app.route('/send_image/<selectedGameName>', methods=['POST'])
def send_image(selectedGameName):
    global messages
    data = request.json
    image_name = data.get('image_name')
    image_size = data.get('image_size', '100')  # Default to 100% if not provided

    # Validate inputs
    if not image_name:
        return jsonify({'result': False, 'error': 'Missing image name'}), 400
    
    # Construct the image URL path
    image_url = url_for('static', filename=f'games/{selectedGameName}/images/{image_name}', _external=False)

    # Set the message for the consumer page
    messages = [{'type': 'image', 'content': image_name, 'size': image_size}]

    return jsonify({'result': True, 'image_url': image_url})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)