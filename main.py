"""
main.py - Automated File Organizer GUI
========================================
This module creates a modern, professional Tkinter-based graphical
user interface for the Automated File Organizer application.

Features:
    - Dark-themed modern UI with custom styling
    - Folder browsing and selection
    - Real-time progress tracking with progress bar
    - Scrollable activity log
    - Threaded file operations (non-blocking UI)
    - Success/error popups with summary

Author: Karthick Raja B
Project: Automated File Organizer
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Import the organizer engine
from organizer import FileOrganizer, FILE_CATEGORIES


# ─────────────────────────────────────────────────────────────
# Color Palette & Design Tokens
# ─────────────────────────────────────────────────────────────

COLORS = {
    "bg_primary":       "#0f0f1a",      # Deep dark background
    "bg_secondary":     "#1a1a2e",      # Card/panel background
    "bg_tertiary":      "#16213e",      # Slightly lighter panels
    "bg_input":         "#0d1117",      # Input field background
    "accent_primary":   "#6c63ff",      # Primary accent (purple)
    "accent_hover":     "#7f78ff",      # Hover state
    "accent_success":   "#00c897",      # Success green
    "accent_warning":   "#ffb74d",      # Warning orange
    "accent_error":     "#ff5252",      # Error red
    "text_primary":     "#e8e8f0",      # Main text
    "text_secondary":   "#a0a0b8",      # Muted text
    "text_dim":         "#6b6b80",      # Very dim text
    "border":           "#2a2a40",      # Border color
    "border_focus":     "#6c63ff",      # Focused border
    "progress_track":   "#1e1e32",      # Progress bar track
    "progress_fill":    "#6c63ff",      # Progress bar fill
    "log_bg":           "#0a0a14",      # Log area background
    "scrollbar_bg":     "#1a1a2e",      # Scrollbar trough
    "scrollbar_thumb":  "#3a3a55",      # Scrollbar handle
}

# Category icons (emoji) for visual flair in the log
CATEGORY_ICONS = {
    "Images":    "🖼️",
    "Documents": "📄",
    "Videos":    "🎬",
    "Audio":     "🎵",
    "Archives":  "📦",
    "Programs":  "⚙️",
    "Others":    "📁",
    "Error":     "❌",
}


class FileOrganizerApp:
    """
    Main application class for the Automated File Organizer GUI.

    This class builds the entire Tkinter interface, handles user
    interactions, and coordinates with the FileOrganizer engine
    running on a background thread.
    """

    def __init__(self, root):
        """
        Initialize the application window and build the UI.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.selected_folder = None
        self.is_organizing = False

        # Configure the main window
        self._configure_window()

        # Build the custom ttk styles
        self._configure_styles()

        # Build UI components
        self._build_header()
        self._build_folder_section()
        self._build_action_section()
        self._build_progress_section()
        self._build_log_section()
        self._build_footer()

    # ─────────────────────────────────────────────────────────
    # Window Configuration
    # ─────────────────────────────────────────────────────────

    def _configure_window(self):
        """Set up the main application window properties."""
        self.root.title("Automated File Organizer")
        self.root.configure(bg=COLORS["bg_primary"])

        # Window size and positioning
        window_width = 720
        window_height = 780

        # Center the window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Minimum size to prevent shrinking below usable dimensions
        self.root.minsize(600, 680)

        # Allow window resizing
        self.root.resizable(True, True)

        # Configure grid weights for responsive layout
        self.root.columnconfigure(0, weight=1)

    # ─────────────────────────────────────────────────────────
    # TTK Style Configuration
    # ─────────────────────────────────────────────────────────

    def _configure_styles(self):
        """
        Configure custom ttk styles for a modern dark theme.
        This overrides default widget appearance with our color palette.
        """
        self.style = ttk.Style()
        self.style.theme_use("clam")  # 'clam' is the most customizable theme

        # ── Progress Bar Style ──
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=COLORS["progress_track"],
            background=COLORS["accent_primary"],
            borderwidth=0,
            lightcolor=COLORS["accent_primary"],
            darkcolor=COLORS["accent_primary"],
        )

        # ── Separator Style ──
        self.style.configure(
            "Custom.TSeparator",
            background=COLORS["border"]
        )

    # ─────────────────────────────────────────────────────────
    # UI Builder Methods
    # ─────────────────────────────────────────────────────────

    def _build_header(self):
        """Build the application header with title and subtitle."""
        header_frame = tk.Frame(
            self.root,
            bg=COLORS["bg_primary"],
            pady=20
        )
        header_frame.pack(fill="x", padx=30)

        # Application icon/emoji
        icon_label = tk.Label(
            header_frame,
            text="📂",
            font=("Segoe UI Emoji", 32),
            bg=COLORS["bg_primary"]
        )
        icon_label.pack()

        # Application title
        title_label = tk.Label(
            header_frame,
            text="Automated File Organizer",
            font=("Segoe UI", 22, "bold"),
            fg=COLORS["text_primary"],
            bg=COLORS["bg_primary"]
        )
        title_label.pack(pady=(5, 2))

        # Subtitle description
        subtitle_label = tk.Label(
            header_frame,
            text="Organize your files into smart categories with one click",
            font=("Segoe UI", 10),
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_primary"]
        )
        subtitle_label.pack()

        # Decorative accent line
        accent_canvas = tk.Canvas(
            header_frame,
            height=3,
            bg=COLORS["bg_primary"],
            highlightthickness=0
        )
        accent_canvas.pack(fill="x", pady=(12, 0), padx=80)
        accent_canvas.create_rectangle(0, 0, 560, 3, fill=COLORS["accent_primary"], outline="")

    def _build_folder_section(self):
        """Build the folder selection panel with browse button and path display."""
        # Container card with rounded appearance
        card_frame = tk.Frame(
            self.root,
            bg=COLORS["bg_secondary"],
            padx=20,
            pady=18,
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        card_frame.pack(fill="x", padx=30, pady=(5, 8))

        # Section label
        section_label = tk.Label(
            card_frame,
            text="📁  SELECT FOLDER",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["accent_primary"],
            bg=COLORS["bg_secondary"],
            anchor="w"
        )
        section_label.pack(fill="x", pady=(0, 10))

        # Row containing the path display and browse button
        row_frame = tk.Frame(card_frame, bg=COLORS["bg_secondary"])
        row_frame.pack(fill="x")

        # Path display (read-only entry widget)
        self.folder_path_var = tk.StringVar(value="No folder selected...")
        self.path_entry = tk.Entry(
            row_frame,
            textvariable=self.folder_path_var,
            state="readonly",
            font=("Consolas", 10),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_input"],
            readonlybackground=COLORS["bg_input"],
            relief="flat",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            highlightcolor=COLORS["border_focus"],
            insertbackground=COLORS["text_primary"]
        )
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))

        # Browse button
        self.browse_btn = tk.Button(
            row_frame,
            text="  Browse  ",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=COLORS["accent_primary"],
            activeforeground="#ffffff",
            activebackground=COLORS["accent_hover"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=6,
            command=self._browse_folder
        )
        self.browse_btn.pack(side="right")

        # Bind hover effects
        self.browse_btn.bind("<Enter>", lambda e: self.browse_btn.config(bg=COLORS["accent_hover"]))
        self.browse_btn.bind("<Leave>", lambda e: self.browse_btn.config(bg=COLORS["accent_primary"]))

    def _build_action_section(self):
        """Build the main action button and category info section."""
        action_frame = tk.Frame(
            self.root,
            bg=COLORS["bg_primary"],
            pady=5
        )
        action_frame.pack(fill="x", padx=30)

        # ── Organize Button ──
        self.organize_btn = tk.Button(
            action_frame,
            text="⚡  Organize Files",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff",
            bg=COLORS["accent_primary"],
            activeforeground="#ffffff",
            activebackground=COLORS["accent_hover"],
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10,
            state="disabled",
            disabledforeground=COLORS["text_dim"],
            command=self._start_organizing
        )
        self.organize_btn.pack(fill="x", ipady=3)

        # Bind hover effects
        self.organize_btn.bind("<Enter>", self._on_organize_hover)
        self.organize_btn.bind("<Leave>", self._on_organize_leave)

        # ── Category Tags ──
        tags_frame = tk.Frame(action_frame, bg=COLORS["bg_primary"])
        tags_frame.pack(fill="x", pady=(12, 5))

        categories_label = tk.Label(
            tags_frame,
            text="Categories:  ",
            font=("Segoe UI", 8),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_primary"]
        )
        categories_label.pack(side="left")

        # Display category tags as colored badges
        tag_colors = ["#6c63ff", "#00c897", "#ff6b6b", "#ffb74d", "#4fc3f7", "#ba68c8", "#78909c"]
        for i, category in enumerate(FILE_CATEGORIES.keys()):
            tag = tk.Label(
                tags_frame,
                text=f" {CATEGORY_ICONS.get(category, '')} {category} ",
                font=("Segoe UI", 7, "bold"),
                fg="#ffffff",
                bg=tag_colors[i % len(tag_colors)],
                padx=4,
                pady=1
            )
            tag.pack(side="left", padx=2)

    def _build_progress_section(self):
        """Build the progress bar and status label section."""
        progress_frame = tk.Frame(
            self.root,
            bg=COLORS["bg_secondary"],
            padx=20,
            pady=15,
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        progress_frame.pack(fill="x", padx=30, pady=(8, 8))

        # Status row (label on left, percentage on right)
        status_row = tk.Frame(progress_frame, bg=COLORS["bg_secondary"])
        status_row.pack(fill="x", pady=(0, 8))

        # Status label
        self.status_var = tk.StringVar(value="Ready — Select a folder to begin")
        self.status_label = tk.Label(
            status_row,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_secondary"],
            anchor="w"
        )
        self.status_label.pack(side="left")

        # Percentage label
        self.percent_var = tk.StringVar(value="0%")
        self.percent_label = tk.Label(
            status_row,
            textvariable=self.percent_var,
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["accent_primary"],
            bg=COLORS["bg_secondary"],
            anchor="e"
        )
        self.percent_label.pack(side="right")

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", ipady=2)

        # File counter label
        self.counter_var = tk.StringVar(value="0 / 0 files processed")
        self.counter_label = tk.Label(
            progress_frame,
            textvariable=self.counter_var,
            font=("Segoe UI", 8),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_secondary"],
            anchor="w"
        )
        self.counter_label.pack(fill="x", pady=(6, 0))

    def _build_log_section(self):
        """Build the scrollable activity log display."""
        log_frame = tk.Frame(
            self.root,
            bg=COLORS["bg_secondary"],
            padx=20,
            pady=15,
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        log_frame.pack(fill="both", expand=True, padx=30, pady=(0, 8))

        # Section header with clear button
        header_row = tk.Frame(log_frame, bg=COLORS["bg_secondary"])
        header_row.pack(fill="x", pady=(0, 8))

        log_label = tk.Label(
            header_row,
            text="📋  ACTIVITY LOG",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["accent_primary"],
            bg=COLORS["bg_secondary"],
            anchor="w"
        )
        log_label.pack(side="left")

        # Clear log button
        self.clear_btn = tk.Button(
            header_row,
            text="Clear",
            font=("Segoe UI", 8),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_secondary"],
            activeforeground=COLORS["text_primary"],
            activebackground=COLORS["bg_tertiary"],
            relief="flat",
            cursor="hand2",
            command=self._clear_log
        )
        self.clear_btn.pack(side="right")

        # Log text area with scrollbar
        log_container = tk.Frame(log_frame, bg=COLORS["log_bg"])
        log_container.pack(fill="both", expand=True)

        # Custom scrollbar
        self.log_scrollbar = tk.Scrollbar(
            log_container,
            orient="vertical",
            bg=COLORS["scrollbar_bg"],
            troughcolor=COLORS["scrollbar_bg"],
            activebackground=COLORS["scrollbar_thumb"],
            width=10
        )
        self.log_scrollbar.pack(side="right", fill="y")

        # Log text widget
        self.log_text = tk.Text(
            log_container,
            font=("Consolas", 9),
            fg=COLORS["text_secondary"],
            bg=COLORS["log_bg"],
            relief="flat",
            wrap="word",
            state="disabled",
            cursor="arrow",
            padx=12,
            pady=10,
            spacing1=3,
            yscrollcommand=self.log_scrollbar.set
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_scrollbar.config(command=self.log_text.yview)

        # Configure text tags for colored log entries
        self.log_text.tag_configure("info", foreground=COLORS["text_secondary"])
        self.log_text.tag_configure("success", foreground=COLORS["accent_success"])
        self.log_text.tag_configure("warning", foreground=COLORS["accent_warning"])
        self.log_text.tag_configure("error", foreground=COLORS["accent_error"])
        self.log_text.tag_configure("header", foreground=COLORS["accent_primary"], font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("dim", foreground=COLORS["text_dim"])

        # Add welcome message
        self._append_log("Welcome to Automated File Organizer!", "header")
        self._append_log("Select a folder and click 'Organize Files' to begin.", "dim")

    def _build_footer(self):
        """Build the application footer with credits."""
        footer_frame = tk.Frame(
            self.root,
            bg=COLORS["bg_primary"],
            pady=8
        )
        footer_frame.pack(fill="x", padx=30, side="bottom")

        footer_label = tk.Label(
            footer_frame,
            text="Automated File Organizer v1.0  •  Built with Python & Tkinter",
            font=("Segoe UI", 8),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_primary"]
        )
        footer_label.pack()

    # ─────────────────────────────────────────────────────────
    # Event Handlers
    # ─────────────────────────────────────────────────────────

    def _on_organize_hover(self, event):
        """Handle mouse enter on the organize button."""
        if str(self.organize_btn["state"]) != "disabled":
            self.organize_btn.config(bg=COLORS["accent_hover"])

    def _on_organize_leave(self, event):
        """Handle mouse leave on the organize button."""
        if str(self.organize_btn["state"]) != "disabled":
            self.organize_btn.config(bg=COLORS["accent_primary"])

    def _browse_folder(self):
        """
        Open a folder selection dialog and update the path display.
        Enables the organize button once a valid folder is selected.
        """
        folder = filedialog.askdirectory(
            title="Select Folder to Organize",
            mustexist=True
        )

        if folder:
            self.selected_folder = folder
            self.folder_path_var.set(folder)

            # Update the entry text color to show selection
            self.path_entry.config(fg=COLORS["text_primary"])

            # Enable the organize button
            self.organize_btn.config(
                state="normal",
                bg=COLORS["accent_primary"]
            )

            # Update status
            self.status_var.set(f"Folder selected — Ready to organize")
            self._append_log(f"Selected folder: {folder}", "info")

            # Count files for preview
            try:
                file_count = len([
                    f for f in os.listdir(folder)
                    if os.path.isfile(os.path.join(folder, f))
                    and f != "organizer_log.txt"
                ])
                self._append_log(f"Found {file_count} file(s) in the folder.", "info")
            except Exception:
                pass

    def _start_organizing(self):
        """
        Begin the file organization process on a background thread.
        This prevents the GUI from freezing during file operations.
        """
        if self.is_organizing:
            return

        if not self.selected_folder:
            messagebox.showwarning(
                "No Folder Selected",
                "Please select a folder before organizing."
            )
            return

        # Confirm with the user
        file_count = len([
            f for f in os.listdir(self.selected_folder)
            if os.path.isfile(os.path.join(self.selected_folder, f))
            and f != "organizer_log.txt"
        ])

        if file_count == 0:
            messagebox.showinfo(
                "No Files Found",
                "The selected folder contains no files to organize."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Organization",
            f"This will organize {file_count} file(s) in:\n\n"
            f"{self.selected_folder}\n\n"
            "Files will be moved into categorized subfolders.\n"
            "Do you want to continue?"
        )

        if not confirm:
            return

        # Disable UI controls during organization
        self.is_organizing = True
        self.organize_btn.config(state="disabled", bg=COLORS["bg_tertiary"])
        self.browse_btn.config(state="disabled")

        # Reset progress
        self.progress_var.set(0)
        self.percent_var.set("0%")
        self.counter_var.set(f"0 / {file_count} files processed")
        self.status_var.set("Organizing files...")

        self._append_log("", "dim")
        self._append_log("━" * 45, "header")
        self._append_log("🚀 Starting file organization...", "header")
        self._append_log("━" * 45, "header")

        # Launch organization on a background thread
        thread = threading.Thread(target=self._organize_thread, daemon=True)
        thread.start()

    def _organize_thread(self):
        """
        Background thread that runs the file organization engine.
        Uses thread-safe callbacks to update the GUI.
        """
        try:
            # Create the organizer engine instance
            organizer = FileOrganizer(self.selected_folder)

            # Run the organization with progress callback
            summary = organizer.organize(progress_callback=self._on_progress)

            # Clean up empty folders
            organizer.cleanup_empty_folders()

            # Schedule the completion handler on the main thread
            self.root.after(0, self._on_complete, summary, organizer.activity_log)

        except Exception as e:
            # Handle unexpected errors gracefully
            self.root.after(0, self._on_error, str(e))

    def _on_progress(self, processed, total, filename, category):
        """
        Callback invoked by the organizer engine after each file.
        Schedules GUI updates on the main thread (thread-safe).

        Args:
            processed (int): Number of files processed so far.
            total (int): Total number of files to process.
            filename (str): Name of the file just processed.
            category (str): Category the file was moved to.
        """
        # Calculate progress percentage
        percent = (processed / total * 100) if total > 0 else 0

        # Schedule the UI update on the main Tkinter thread
        self.root.after(0, self._update_progress_ui, processed, total, percent, filename, category)

    def _update_progress_ui(self, processed, total, percent, filename, category):
        """
        Update all progress-related UI elements.
        This runs on the main thread and is safe for Tkinter.
        """
        # Update progress bar
        self.progress_var.set(percent)
        self.percent_var.set(f"{percent:.0f}%")
        self.counter_var.set(f"{processed} / {total} files processed")
        self.status_var.set(f"Moving: {filename}")

        # Add log entry with category icon
        icon = CATEGORY_ICONS.get(category, "📁")
        tag = "error" if category == "Error" else "success"
        self._append_log(f"  {icon}  {filename}  →  {category}/", tag)

    def _on_complete(self, summary, activity_log):
        """
        Handle successful completion of file organization.
        Shows a summary popup and updates the UI.

        Args:
            summary (dict): Organization results from the engine.
            activity_log (list): List of log messages from the engine.
        """
        # Update UI state
        self.progress_var.set(100)
        self.percent_var.set("100%")
        self.status_var.set("✅ Organization complete!")
        self.status_label.config(fg=COLORS["accent_success"])

        # Log completion
        self._append_log("", "dim")
        self._append_log("━" * 45, "header")
        self._append_log("✅ Organization Complete!", "success")
        self._append_log("━" * 45, "header")

        # Build and display the summary
        total = summary["total"]
        categories = summary["categories"]

        # Log per-category breakdown
        for category, count in categories.items():
            if count > 0:
                icon = CATEGORY_ICONS.get(category, "📁")
                self._append_log(f"  {icon}  {category}: {count} file(s)", "info")

        self._append_log(f"\n  📊 Total: {total} file(s) organized", "success")
        self._append_log(f"  📝 Log saved to: organizer_log.txt", "dim")

        # Build summary message for popup
        summary_lines = [f"Successfully organized {total} file(s)!\n"]
        for category, count in categories.items():
            if count > 0:
                icon = CATEGORY_ICONS.get(category, "📁")
                summary_lines.append(f"  {icon}  {category}: {count}")

        summary_lines.append(f"\nLog file saved to:\n{os.path.join(self.selected_folder, 'organizer_log.txt')}")

        messagebox.showinfo(
            "Organization Complete! ✅",
            "\n".join(summary_lines)
        )

        # Re-enable UI controls
        self._reset_ui_state()

    def _on_error(self, error_message):
        """
        Handle errors that occur during organization.

        Args:
            error_message (str): Description of the error.
        """
        self._append_log(f"❌ Error: {error_message}", "error")
        self.status_var.set("❌ An error occurred")
        self.status_label.config(fg=COLORS["accent_error"])

        messagebox.showerror(
            "Error",
            f"An error occurred during organization:\n\n{error_message}"
        )

        self._reset_ui_state()

    def _reset_ui_state(self):
        """Reset the UI controls to their default enabled state."""
        self.is_organizing = False
        self.organize_btn.config(state="normal", bg=COLORS["accent_primary"])
        self.browse_btn.config(state="normal")

    # ─────────────────────────────────────────────────────────
    # Log Utility Methods
    # ─────────────────────────────────────────────────────────

    def _append_log(self, message, tag="info"):
        """
        Append a message to the scrollable activity log.

        Args:
            message (str): The log message to display.
            tag (str): The style tag ('info', 'success', 'warning', 'error', 'header', 'dim').
        """
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n", tag)
        self.log_text.see("end")  # Auto-scroll to the latest entry
        self.log_text.config(state="disabled")

    def _clear_log(self):
        """Clear all entries from the activity log."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        self._append_log("Log cleared.", "dim")


# ─────────────────────────────────────────────────────────────
# Application Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    """Create and run the Automated File Organizer application."""
    root = tk.Tk()

    # Set the application icon (if available)
    try:
        # Attempt to load a custom icon from the assets folder
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass  # Gracefully skip if icon is not available

    # Create the application instance
    app = FileOrganizerApp(root)

    # Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()
