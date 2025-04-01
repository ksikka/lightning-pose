import subprocess
import json
import shlex
import sys

def ffprobe(file_path):
    """
    Retrieves video resolution, frame rate, and codec using ffprobe.

    Args:
        file_path (str): The path to the video file.

    Returns:
        dict: A dictionary containing 'width', 'height', 'frame_rate',
              and 'codec_name'. Returns None if ffprobe fails or the
              file doesn't contain a video stream.

    Raises:
        FileNotFoundError: If ffprobe command is not found.
        subprocess.CalledProcessError: If ffprobe returns a non-zero exit code.
        Exception: For other potential errors during processing.
    """
    # Check if ffprobe exists in PATH
    # Use sys.executable to find the python interpreter and run ffprobe via it
    # This helps find ffprobe if it's installed in the same environment
    ffprobe_cmd = "ffprobe"
    try:
        # Basic check to see if ffprobe exists and is executable
        subprocess.run([ffprobe_cmd, "-version"], check=True, capture_output=True)
    except FileNotFoundError:
        print(f"Error: '{ffprobe_cmd}' command not found.")
        print("Please ensure FFmpeg (which includes ffprobe) is installed and in your system's PATH.")
        raise
    except subprocess.CalledProcessError as e:
        print(f"Error: '{ffprobe_cmd} -version' failed.")
        print(f"Stderr: {e.stderr.decode()}")
        raise

    # Construct the ffprobe command to get specific stream info as JSON
    # -v quiet: Suppress logging unless there's an error.
    # -print_format json: Output in JSON format.
    # -show_streams: Get information about media streams.
    # -select_streams v:0: Select only the first video stream.
    command = [
        ffprobe_cmd,
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "v:0", # Select the first video stream
        file_path
    ]

    print(f"Running command: {' '.join(shlex.quote(str(c)) for c in command)}") # Log the command being run

    try:
        # Execute the command
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # Parse the JSON output
        output_data = json.loads(result.stdout)

        # Check if any video streams were found
        if not output_data.get("streams"):
            print(f"Warning: No video streams found in '{file_path}'.")
            return None

        video_stream = output_data["streams"][0] # Get the first video stream info

        # Extract required information
        width = video_stream.get("width")
        height = video_stream.get("height")
        codec_name = video_stream.get("codec_name")
        frame_rate_str = video_stream.get("r_frame_rate") # e.g., "30/1" or "2997/100"

        # Calculate frame rate as a float
        frame_rate = None
        if frame_rate_str:
            try:
                num, den = map(int, frame_rate_str.split('/'))
                if den != 0:
                    frame_rate = num / den
                else:
                    print(f"Warning: Invalid frame rate denominator '0' in '{frame_rate_str}'.")
            except (ValueError, ZeroDivisionError) as e:
                 print(f"Warning: Could not parse frame rate '{frame_rate_str}': {e}")
                 # Try avg_frame_rate as a fallback if r_frame_rate fails
                 avg_frame_rate_str = video_stream.get("avg_frame_rate")
                 if avg_frame_rate_str and avg_frame_rate_str != "0/0":
                     try:
                         num, den = map(int, avg_frame_rate_str.split('/'))
                         if den != 0:
                             frame_rate = num / den
                             print(f"Using avg_frame_rate: {frame_rate:.2f} fps")
                         else:
                             print(f"Warning: Invalid avg_frame_rate denominator '0' in '{avg_frame_rate_str}'.")
                     except (ValueError, ZeroDivisionError) as e_avg:
                         print(f"Warning: Could not parse avg_frame_rate '{avg_frame_rate_str}': {e_avg}")


        # Ensure essential info is present
        if width is None or height is None or frame_rate is None or codec_name is None:
             print(f"Warning: Could not extract all required video info from '{file_path}'.")
             # Return partial info if available, or None if critical info missing
             return {
                "width": width,
                "height": height,
                "frame_rate": frame_rate,
                "codec_name": codec_name,
            } if width and height else None


        return {
            "width": int(width),
            "height": int(height),
            "frame_rate": float(frame_rate),
            "codec_name": codec_name,
        }

    except subprocess.CalledProcessError as e:
        # Handle errors from the ffprobe command itself
        print(f"Error running ffprobe for '{file_path}':")
        print(f"Command: {' '.join(shlex.quote(str(c)) for c in command)}")
        print(f"Return code: {e.returncode}")
        # Decode stderr for better error messages
        stderr_output = e.stderr.decode(errors='ignore') if e.stderr else "No stderr output."
        print(f"Stderr: {stderr_output}")
        # Re-raise the exception so the caller knows ffprobe failed
        raise
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON output from ffprobe for '{file_path}'.")
        print(f"Output was: {result.stdout}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise # Re-raise other unexpected errors