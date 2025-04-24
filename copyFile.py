import os
import subprocess
import sys
"""
For MicroPython, This script will take in a directory and copy everything in that file to a microcontroller
ie. py/python/python3 <directoryName>
EX) py Firmware/ will copy the contents of Firmware/ onto the ESP32
NOTE: Because copying files may abruptly crash, it may take multiple calls to be able to copy all the files over
"""
def create_directory_on_device(dest_dir):
    try:
        # This line may be optional depending on the language
        dest_dir = dest_dir.rstrip("/")
        # NOTE: CHANGE THIS COMMAND LINE TO THE LANGUAGE YOU NEED ie CircuitPython or etc TO LOOK FOR A DIRECTORY
        command = f"mpremote fs ls {dest_dir}"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            return  
        # NOTE: CHANGE THIS COMMAND LINE TO THE LANGUAGE YOU NEED ie CircuitPython or etc TO MAKE A DIRECTORY
        command = f"mpremote fs mkdir {dest_dir}"
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error creating directory {dest_dir}: {e}")

def copy_files_to_device(source_dir):
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            dest_path = f"{os.path.relpath(local_path, source_dir)}"# IF YOU WANT TO PUT IT IN THE ROOT

            create_directory_on_device(source_dir)
            
            # NOTE: CHANGE THIS COMMAND LINE TO THE LANGUAGE YOU NEED ie CircuitPython or etc TO COPY A FILE OVER
            command = f"mpremote fs cp {local_path} :{dest_path}"

            try:
                subprocess.run(command, shell=True, check=True)
                print(f"Successfully copied {filename} to {local_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while copying {filename}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python copy_files.py <directory_path>")
    else:
        source_directory = sys.argv[1]

        if not os.path.isdir(source_directory):
            print(f"The provided path '{source_directory}' is not a valid directory.")
        else:
            copy_files_to_device(source_directory)
