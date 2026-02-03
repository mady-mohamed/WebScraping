import glob
import shutil
import os

# Define your source and destination directories
source_dir = r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app'
dest_dir = r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\notebooks'

# Create the destination folder if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Find all files ending in .csv
csv_files = glob.glob(os.path.join(source_dir, '*.ipynb'))

for file_path in csv_files:
    # shutil.move moves the file and handles the pathing automatically
    shutil.move(file_path, dest_dir)
    print(f"Moved: {os.path.basename(file_path)}")