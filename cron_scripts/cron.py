import subprocess
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def run_script(script_name):
    try:
        print(f"Starting {script_name}")
        script_path = os.path.join(root_dir, 'cron_scripts', script_name)
        result = subprocess.run(['python', script_path], check=True, text=True, capture_output=True)
        print(f"Completed {script_name} successfully: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run {script_name}: {e.stderr}")

if __name__ == '__main__':
    scripts = ['user_levels.py', 'full_update.py', 'download_images.py']

    for script in scripts:
        run_script(script)