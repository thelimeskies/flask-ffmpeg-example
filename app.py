from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_video():
    # Get the video file from the request
    file = request.files['file']
    output_format = request.form['format']

    # Save the input file, it must be '/tmp' folder
    input_path = '/tmp/input_video.mp4'
    file.save(input_path)

    # Define the output path
    output_path = f'/tmp/output_video.{output_format}'

    # Run FFmpeg to convert the video
    command = ['ffmpeg', '-i', input_path, output_path]
    subprocess.run(command, check=True)

    # Return the path to the converted file
    return jsonify({"output_file": output_path})

if __name__ == '__main__':
    app.run(debug=True)
