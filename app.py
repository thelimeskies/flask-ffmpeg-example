from flask import Flask, request, send_file, jsonify
import subprocess
import os
import tempfile
import zipfile
import io
import shutil

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_video():
    # Ensure a file is provided
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # Save the uploaded video file to a temporary location
    input_video = request.files['file']
    input_path = os.path.join(tempfile.gettempdir(), 'input_video.mp4')
    input_video.save(input_path)

    # Create a temporary directory to store HLS output files
    output_dir = tempfile.mkdtemp()

    # Define the renditions we want to create.
    # You can add more resolutions or adjust parameters as needed.
    resolutions = {
        '480p': {'height': 480, 'bandwidth': 800000, 'resolution': '854x480'},
        '360p': {'height': 360, 'bandwidth': 500000, 'resolution': '640x360'}
    }

    # Loop over each rendition, create a subdirectory and generate HLS segments and playlist using FFmpeg.
    for label, params in resolutions.items():
        variant_dir = os.path.join(output_dir, label)
        os.makedirs(variant_dir, exist_ok=True)
        playlist_path = os.path.join(variant_dir, 'playlist.m3u8')
        height = params['height']
        command = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f'scale=-2:{height}',  # maintain aspect ratio with the given height
            '-c:a', 'aac',
            '-c:v', 'h264',
            '-f', 'hls',
            '-hls_time', '4',
            '-hls_playlist_type', 'vod',
            playlist_path
        ]
        subprocess.run(command, check=True)

    # Create a master M3U8 playlist that references each variant
    master_playlist_path = os.path.join(output_dir, 'master.m3u8')
    with open(master_playlist_path, 'w') as master:
        master.write('#EXTM3U\n')
        master.write('#EXT-X-VERSION:3\n')
        for label, params in resolutions.items():
            variant_playlist = os.path.join(label, 'playlist.m3u8')
            master.write(
                f'#EXT-X-STREAM-INF:BANDWIDTH={params["bandwidth"]},RESOLUTION={params["resolution"]}\n'
            )
            master.write(f'{variant_playlist}\n')

    # Create a ZIP archive in memory containing all the HLS files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(output_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                # Use relative paths to maintain folder structure in the zip file
                relative_path = os.path.relpath(file_path, output_dir)
                zip_file.write(file_path, arcname=relative_path)
    zip_buffer.seek(0)

    # Cleanup temporary files and folders
    try:
        os.remove(input_path)
        shutil.rmtree(output_dir)
    except Exception as e:
        # Log the error or pass if cleanup fails
        pass

    # Return the ZIP file as a download
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name='output_hls.zip',
        mimetype='application/zip'
    )

if __name__ == '__main__':
    app.run(debug=True)
