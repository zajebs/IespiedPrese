import subprocess
import logging
import datetime
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
log_dir = os.path.join(root_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
print(root_dir)
print(log_dir)

# Setup logging
log_filename = datetime.datetime.now().strftime(f'{log_dir}/%d_%m_%Y_cron_tasks.log')
logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_name):
    try:
        logging.info(f"Starting {script_name}")
        script_path = os.path.join(root_dir, 'cron_scripts', script_name)
        result = subprocess.run(['python', script_path], check=True, text=True, capture_output=True)
        logging.info(f"Completed {script_name} successfully: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run {script_name}: {e.stderr}")

if __name__ == '__main__':
    scripts = ['user_levels.py', 'full_update.py', 'download_images.py']

    for script in scripts:
        run_script(script)