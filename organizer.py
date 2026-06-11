"""
organizer.py - File Organization Engine
========================================
This module contains the core logic for scanning, categorizing,
and moving files into organized subfolders based on their extensions.

Author: Karthick Raja B
Project: Automated File Organizer
"""

import os
import shutil
import logging
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# File Category Definitions
# ─────────────────────────────────────────────────────────────
# Each category maps to a list of supported file extensions.
# Files not matching any category fall into "Others".

FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv", ".rtf", ".odt"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Programs": [".exe", ".msi", ".deb", ".dmg", ".apk"],
    "Others": []  # Catch-all for unrecognized extensions
}


class FileOrganizer:
    """
    Core engine that handles scanning a directory, categorizing files
    by extension, creating category folders, and moving files safely.

    Attributes:
        source_folder (str): The folder path to organize.
        log_file_path (str): Path to the log file for recording actions.
        logger (logging.Logger): Logger instance for file and console output.
        file_count (dict): Tracks how many files were moved per category.
        total_files (int): Total number of files found to organize.
        processed_files (int): Number of files processed so far.
        activity_log (list): In-memory log of all actions for GUI display.
    """

    def __init__(self, source_folder, log_file_path=None):
        """
        Initialize the FileOrganizer with a source folder.

        Args:
            source_folder (str): Path to the folder to organize.
            log_file_path (str, optional): Path for the log file.
                Defaults to 'organizer_log.txt' inside the source folder.
        """
        self.source_folder = source_folder

        # Default log file location is inside the source folder
        if log_file_path is None:
            self.log_file_path = os.path.join(source_folder, "organizer_log.txt")
        else:
            self.log_file_path = log_file_path

        # Tracking counters
        self.file_count = {category: 0 for category in FILE_CATEGORIES}
        self.total_files = 0
        self.processed_files = 0
        self.activity_log = []

        # Set up logging to file
        self._setup_logger()

    def _setup_logger(self):
        """
        Configure the logging module to write actions to a log file.
        Each run appends a new session header with a timestamp.
        """
        self.logger = logging.getLogger("FileOrganizer")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicate logs
        self.logger.handlers.clear()

        # Create file handler that appends to the log file
        file_handler = logging.FileHandler(self.log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Define log message format
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Write session header
        self.logger.info("=" * 60)
        self.logger.info(f"  New Organization Session Started")
        self.logger.info(f"  Source Folder: {self.source_folder}")
        self.logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)

    def _log_action(self, message, level="info"):
        """
        Log an action both to the file logger and the in-memory activity log.

        Args:
            message (str): The message to log.
            level (str): Log level - 'info', 'warning', or 'error'.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.activity_log.append(log_entry)

        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)

    def get_category(self, file_extension):
        """
        Determine which category a file belongs to based on its extension.

        Args:
            file_extension (str): The file extension (e.g., '.jpg').

        Returns:
            str: The category name (e.g., 'Images', 'Documents', 'Others').
        """
        ext_lower = file_extension.lower()

        for category, extensions in FILE_CATEGORIES.items():
            if ext_lower in extensions:
                return category

        # If no match found, categorize as "Others"
        return "Others"

    def scan_files(self):
        """
        Scan the source folder for all files (not subdirectories).
        Only scans the top-level directory, not recursively.

        Returns:
            list: A list of filenames found in the source folder.
        """
        try:
            all_items = os.listdir(self.source_folder)

            # Filter only files (exclude directories and the log file itself)
            files = [
                item for item in all_items
                if os.path.isfile(os.path.join(self.source_folder, item))
                and item != "organizer_log.txt"
            ]

            self.total_files = len(files)
            self._log_action(f"Scanned folder: Found {self.total_files} file(s) to organize.")
            return files

        except PermissionError:
            self._log_action(f"Permission denied: Cannot access '{self.source_folder}'", "error")
            raise
        except FileNotFoundError:
            self._log_action(f"Folder not found: '{self.source_folder}'", "error")
            raise

    def create_category_folders(self):
        """
        Create all category subfolders inside the source folder if they
        don't already exist. Skips folders that are already present.
        """
        for category in FILE_CATEGORIES:
            folder_path = os.path.join(self.source_folder, category)

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self._log_action(f"Created folder: '{category}/'")
            else:
                self._log_action(f"Folder already exists: '{category}/'")

    def _get_safe_filename(self, destination_folder, filename):
        """
        Generate a safe filename to prevent overwriting existing files.
        If a file with the same name exists, appends a counter (e.g., '_1', '_2').

        Args:
            destination_folder (str): The target folder path.
            filename (str): The original filename.

        Returns:
            str: A unique filename that doesn't conflict with existing files.
        """
        name, extension = os.path.splitext(filename)
        counter = 1
        new_filename = filename

        # Keep incrementing the counter until a unique name is found
        while os.path.exists(os.path.join(destination_folder, new_filename)):
            new_filename = f"{name}_{counter}{extension}"
            counter += 1

        if new_filename != filename:
            self._log_action(
                f"Duplicate detected: '{filename}' → renamed to '{new_filename}'",
                "warning"
            )

        return new_filename

    def move_file(self, filename):
        """
        Move a single file to its appropriate category folder.

        Args:
            filename (str): The name of the file to move.

        Returns:
            tuple: (success: bool, category: str, message: str)
        """
        try:
            source_path = os.path.join(self.source_folder, filename)

            # Determine file category from extension
            _, extension = os.path.splitext(filename)
            category = self.get_category(extension)

            # Build destination path
            dest_folder = os.path.join(self.source_folder, category)
            safe_name = self._get_safe_filename(dest_folder, filename)
            dest_path = os.path.join(dest_folder, safe_name)

            # Move the file
            shutil.move(source_path, dest_path)

            # Update counters
            self.file_count[category] += 1
            self.processed_files += 1

            self._log_action(f"Moved: '{filename}' → '{category}/{safe_name}'")
            return True, category, f"Moved '{filename}' to '{category}/'"

        except PermissionError:
            msg = f"Permission denied: Cannot move '{filename}'"
            self._log_action(msg, "error")
            self.processed_files += 1
            return False, None, msg

        except Exception as e:
            msg = f"Error moving '{filename}': {str(e)}"
            self._log_action(msg, "error")
            self.processed_files += 1
            return False, None, msg

    def organize(self, progress_callback=None):
        """
        Execute the full organization pipeline:
        1. Scan for files
        2. Create category folders
        3. Move each file to its category

        Args:
            progress_callback (callable, optional): A function called after
                each file is processed, receiving (processed_count, total_count,
                filename, category) as arguments. Used for GUI progress updates.

        Returns:
            dict: A summary dictionary with counts per category and totals.
        """
        self._log_action("─" * 40)
        self._log_action("Starting file organization...")
        self._log_action("─" * 40)

        # Step 1: Scan files
        files = self.scan_files()

        if not files:
            self._log_action("No files found to organize.")
            return self.get_summary()

        # Step 2: Create category folders
        self.create_category_folders()

        # Step 3: Move each file
        errors = 0
        for filename in files:
            success, category, message = self.move_file(filename)

            if not success:
                errors += 1

            # Notify GUI of progress
            if progress_callback:
                progress_callback(
                    self.processed_files,
                    self.total_files,
                    filename,
                    category if success else "Error"
                )

        # Log completion summary
        self._log_action("─" * 40)
        self._log_action("Organization Complete!")
        self._log_action(f"Total files processed: {self.processed_files}")
        self._log_action(f"Errors encountered: {errors}")
        self._log_action("─" * 40)

        # Log per-category breakdown
        for category, count in self.file_count.items():
            if count > 0:
                self._log_action(f"  {category}: {count} file(s)")

        self.logger.info("=" * 60 + "\n")

        return self.get_summary()

    def get_summary(self):
        """
        Generate a summary dictionary of the organization results.

        Returns:
            dict: Contains 'categories' (count per category),
                  'total' (total files processed), and
                  'source' (source folder path).
        """
        return {
            "categories": dict(self.file_count),
            "total": self.processed_files,
            "source": self.source_folder
        }

    def cleanup_empty_folders(self):
        """
        Remove any empty category folders that were created but
        received no files. Keeps the directory clean.
        """
        for category in FILE_CATEGORIES:
            folder_path = os.path.join(self.source_folder, category)

            if os.path.exists(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)
                self._log_action(f"Removed empty folder: '{category}/'")
