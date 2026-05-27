import shutil
from pathlib import Path
from datetime import datetime
import sys
import logging


# ------ Categories -------
CATEGORIES = {
    'Images':     ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
    'Videos':     ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'],
    'Audio':      ['.mp3', '.wav', '.aac', '.flac', '.ogg'],
    'Documents':  ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
    'Archives':   ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Code':       ['.py', '.js', '.html', '.css', '.json', '.xml', '.ts', '.jsx'],
    'Executables':['.exe', '.msi', '.bat', '.sh'],
}

# ------ Logging -------
logging.basicConfig(
    handlers = [
    logging.FileHandler('organizer.log'),
    logging.StreamHandler()
    ],
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)


# ----Getting Category of the file  ----

def get_category(extension):
    extension = extension.lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return 'Miscellaneous'

# ------ Organizing -------

def organize_folder(folder_path):
    folder = Path(folder_path)
    if not folder.exists():
        log.error(f'Path {folder_path} does not exist.')
        sys.exit(1)
    if not folder.is_dir():
        log.error(f'Give a folder path')
        sys.exit(1)
    
    log.info(f'Starting Organizing folder {folder_path}')

    moved = 0
    skipped = 0

    for item in folder.iterdir():
        
        if item.is_dir():
            log.info(f'Skipping folder: {item.name}')
            skipped+=1
            continue

        if item.name == 'organizer.log':
            log.info(f'Skipping log file: {item.name}')
            skipped+=1
            continue

        category = get_category(item.suffix)
        dest_folder = folder / category
        dest_folder.mkdir(exist_ok=True)
        dest_path = dest_folder / item.name

        if dest_path.exists():
            time_stamp = datetime.now().strftime('%d%m%y_%H%M')
            new_name = f'{item.stem}_{time_stamp}_{item.suffix}'
            dest_path = dest_folder / new_name

            log.info(f'File {item.name} already exists, renaming to {new_name}')

        else:
            shutil.move(item, dest_path)
            log.info(f'File {item.name} moved to {dest_path}')
            moved+=1
    log.info(f'Organized: moved {moved} files, skipped {skipped} files.')

if __name__ == '__main__':
    if len(sys.argv)<2:
        log.error('Please provide a folder path.')
        print("Usage: python organizer.py <folder_path>")
        print('Example: python organizer.py "C:\\Users\\Krishna\\Downloads"')
        sys.exit(1)
    
    organize_folder(sys.argv[1])


            

        

