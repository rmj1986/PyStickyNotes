import sys
import json
import os
import uuid
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QTextEdit, QFrame,
    QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QTextDocument, QColor, QPalette, QBrush, QTextCharFormat, QTextCursor, QFont


# --- Configuration ---
NOTES_FILE = "sticky_notes_data.json"
TOOLBAR_WIDTH = 300  # Fixed width for the toolbar
PREVIEW_LINES = 5    # Number of lines to show in the note preview

# --- Resizing configuration for frameless windows ---
RESIZE_GRIP_SIZE = 8 # Pixels from the edge where resizing is active

# --- Note Data Structure ---
# Each note will be stored as a dictionary:
# {
#   "id": "uuid",
#   "title": "First line of note for preview/identification",
#   "content": "HTML content from QTextEdit",
#   "x": int, # Last known X position of the sticky note window
#   "y": int, # Last known Y position of the sticky note window
#   "width": int, # Last known width of the sticky note window
#   "height": int # Last known height of the sticky note window
# }


class DraggableTitleBar(QWidget):
    """
    A custom title bar widget that allows the window to be dragged.
    Includes the note title and custom minimize/close buttons.
    """
    def __init__(self, parent=None, note_id="", note_title=""):
        super().__init__(parent)
        self.parent_window = parent # Reference to the QMainWindow (StickyNoteWindow)
        self.old_pos = None

        self.setFixedHeight(35) # Slightly increased height for the title bar
        self.setStyleSheet("background-color: #CCCCFF; border-top-left-radius: 5px; border-top-right-radius: 5px;")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True) # Ensure stylesheet is applied

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 0, 8, 0) # Increased horizontal margins
        self.layout.setSpacing(8) # Increased spacing between elements

        # Note Title Label
        self.title_label = QLabel(note_title)
        self.title_label.setStyleSheet("color: black; font-weight: bold; font-size: 11pt;") # Slightly larger font
        self.layout.addWidget(self.title_label)
        self.layout.addStretch() # Pushes buttons to the right

        # Minimize Button
        self.minimize_button = QPushButton("—") # Unicode minus sign for minimize
        self.minimize_button.setFixedSize(30, 30) # Increased button size
        self.minimize_button.setStyleSheet(
            "QPushButton { background-color: #7777CC; border: 1px solid #5555AA; border-radius: 5px; color: white; font-weight: bold; font-size: 12pt; }"
            "QPushButton:hover { background-color: #5555AA; }"
        )
        self.minimize_button.clicked.connect(self.parent_window.showMinimized)
        self.layout.addWidget(self.minimize_button)

        # Close Button
        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(30, 30) # Increased button size
        self.close_button.setStyleSheet(
            "QPushButton { background-color: #CC3333; border: 1px solid #990000; border-radius: 5px; color: white; font-weight: bold; font-size: 12pt; }"
            "QPushButton:hover { background-color: #990000; }"
        )
        self.close_button.clicked.connect(self.parent_window.close)
        self.layout.addWidget(self.close_button)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.parent_window.move(self.parent_window.x() + delta.x(), self.parent_window.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None
        super().mouseReleaseEvent(event)

    def set_note_title(self, title):
        self.title_label.setText(title)


class StickyNoteWindow(QMainWindow):
    """
    A separate window for a single sticky note, allowing rich text editing.
    """
    note_updated = pyqtSignal(str, dict) # Signal: note_id, note_data
    note_deleted = pyqtSignal(str)       # Signal: note_id

    def __init__(self, note_id, note_data, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.note_data = note_data
        
        # original_content_html is no longer needed as there's no internal filter
        # self.original_content_html = self.note_data.get("content", "")

        # Set window flags to be frameless and always on top.
        # Custom title bar will provide minimize/close functionality.
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(200, 150) # Set a minimum size for the sticky note window

        self.setGeometry(
            self.note_data.get("x", 100),
            self.note_data.get("y", 100),
            self.note_data.get("width", 400),
            self.note_data.get("height", 300)
        )

        # Resizing state variables
        self.resizing = False
        self.resizing_from = None
        self.start_pos = None
        self.start_geometry = None

        # Create a container widget to hold the custom title bar and content
        self.container_widget = QWidget()
        self.setCentralWidget(self.container_widget)
        self.main_layout = QVBoxLayout(self.container_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Custom Draggable Title Bar
        self.title_bar = DraggableTitleBar(self, note_id=note_id, note_title=self.note_data.get("title", f"Note {note_id[:8]}"))
        self.main_layout.addWidget(self.title_bar)

        # Content area (QFrame to allow background and border styling)
        self.content_widget = QFrame()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10) # Padding inside content frame
        self.content_widget.setStyleSheet("background-color: #FFFF99; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;")
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True) # Ensure stylesheet is applied

        # Removed Filter input for this specific sticky note
        # self.note_filter_input = QLineEdit()
        # self.note_filter_input.setPlaceholderText("Filter lines in this note...")
        # self.note_filter_input.textChanged.connect(self._filter_note_content)
        # self.content_layout.addWidget(self.note_filter_input)


        # Rich text editor
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True) # Allow HTML, images, tables
        self.text_edit.setHtml(self.note_data.get("content", "")) # Set original content from note_data
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.content_layout.addWidget(self.text_edit)

        # Delete button at the bottom
        self.delete_button_layout = QHBoxLayout()
        self.delete_button = QPushButton("Delete Note")
        self.delete_button.clicked.connect(self._confirm_delete)
        self.delete_button.setStyleSheet("background-color: #ffcccc; border: 1px solid #ff9999; border-radius: 3px;") # Reddish delete button
        self.delete_button_layout.addStretch() # Push button to the right
        self.delete_button_layout.addWidget(self.delete_button)
        self.content_layout.addLayout(self.delete_button_layout)

        self.main_layout.addWidget(self.content_widget) # Add the content frame to the main layout

        # Apply rounded corners and a subtle border to the entire container widget
        self.container_widget.setStyleSheet(
            "QWidget { background-color: #FFFF99; border-radius: 5px; border: 1px solid #AAAAAA; }"
        )
        self.container_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Enable mouse tracking for cursor changes
        self.setMouseTracking(True)
        self.container_widget.setMouseTracking(True)
        self.content_widget.setMouseTracking(True)
        self.text_edit.setMouseTracking(True)


    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            self.start_geometry = self.geometry()

            # Check if mouse is on a border for resizing
            pos = event.position().toPoint() # Position relative to the widget
            w, h = self.width(), self.height() # Current window dimensions

            on_left = pos.x() <= RESIZE_GRIP_SIZE
            on_right = pos.x() >= w - RESIZE_GRIP_SIZE
            on_top = pos.y() <= RESIZE_GRIP_SIZE
            on_bottom = pos.y() >= h - RESIZE_GRIP_SIZE

            if on_top and on_left:
                self.resizing_from = 'top_left'
            elif on_top and on_right:
                self.resizing_from = 'top_right'
            elif on_bottom and on_left:
                self.resizing_from = 'bottom_left'
            elif on_bottom and on_right:
                self.resizing_from = 'bottom_right'
            elif on_left:
                self.resizing_from = 'left'
            elif on_right:
                self.resizing_from = 'right'
            elif on_top:
                self.resizing_from = 'top'
            elif on_bottom:
                self.resizing_from = 'bottom'

            if self.resizing_from:
                self.resizing = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.resizing and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.start_pos
            rect = self.start_geometry

            new_x, new_y, new_w, new_h = rect.x(), rect.y(), rect.width(), rect.height()

            if 'right' in self.resizing_from:
                new_w = max(self.minimumWidth(), rect.width() + delta.x())
            if 'bottom' in self.resizing_from:
                new_h = max(self.minimumHeight(), rect.height() + delta.y())
            if 'left' in self.resizing_from:
                new_x = rect.x() + delta.x()
                new_w = max(self.minimumWidth(), rect.width() - delta.x())
                # Adjust new_x if new_w hits minimum
                if new_w <= self.minimumWidth() and rect.width() > self.minimumWidth():
                    new_x = self.start_geometry.x() + (self.start_geometry.width() - self.minimumWidth())
            if 'top' in self.resizing_from:
                new_y = rect.y() + delta.y()
                new_h = max(self.minimumHeight(), rect.height() - delta.y())
                # Adjust new_y if new_h hits minimum
                if new_h <= self.minimumHeight() and rect.height() > self.minimumHeight():
                    new_y = self.start_geometry.y() + (self.start_geometry.height() - self.minimumHeight())

            self.setGeometry(new_x, new_y, new_w, new_h)

        elif not self.resizing: # Change cursor shape when hovering
            pos = event.position().toPoint()
            w, h = self.width(), self.height()

            on_left = pos.x() <= RESIZE_GRIP_SIZE
            on_right = pos.x() >= w - RESIZE_GRIP_SIZE
            on_top = pos.y() <= RESIZE_GRIP_SIZE
            on_bottom = pos.y() >= h - RESIZE_GRIP_SIZE

            if (on_top and on_left) or (on_bottom and on_right):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif (on_top and on_right) or (on_bottom and on_left):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif on_left or on_right:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif on_top or on_bottom:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.unsetCursor() # Reset to default cursor

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.resizing = False
        self.resizing_from = None
        self.start_pos = None
        self.start_geometry = None
        self.unsetCursor() # Ensure cursor is reset
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        # Reset cursor when mouse leaves the window, in case it was a resize cursor
        if not self.resizing: # Only unset if not currently dragging
            self.unsetCursor()
        super().leaveEvent(event)

    def _on_text_changed(self):
        """
        Called when the text in the QTextEdit changes due to user input.
        Updates the note data and emits a signal.
        """
        # Get the current HTML content from the text_edit
        current_html = self.text_edit.toHtml()
        self.note_data["content"] = current_html

        # Extract the first few lines for the title preview
        doc = QTextDocument()
        doc.setHtml(current_html)
        title_text = doc.toPlainText().split('\n')
        new_title = "\n".join(title_text[:PREVIEW_LINES]).strip()
        if not new_title:
            new_title = f"New Note {self.note_id[:8]}" # Fallback if text is empty

        self.note_data["title"] = new_title
        self.title_bar.set_note_title(new_title) # Update title in custom title bar

        # Emit signal to notify parent (SideToolbarApp) about the update
        self.note_updated.emit(self.note_id, self.note_data)

    # Removed _filter_note_content method

    def _confirm_delete(self):
        """Asks for confirmation before deleting the note."""
        reply = QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete this sticky note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_note()

    def _delete_note(self):
        """Deletes the current note and closes the window."""
        self.note_deleted.emit(self.note_id)
        self.close() # Close the window after signaling deletion

    def closeEvent(self, event):
        """
        Overrides the close event to save the window's position and size.
        """
        self.note_data["x"] = self.x()
        self.note_data["y"] = self.y()
        self.note_data["width"] = self.width()
        self.note_data["height"] = self.height()
        self.note_updated.emit(self.note_id, self.note_data) # Ensure state is saved on close
        event.accept() # Accept the close event, hiding the window


class NotePreviewWidget(QFrame):
    """
    A clickable widget for displaying a preview of a note in the toolbar.
    """
    open_note_signal = pyqtSignal(str) # Signal: note_id
    delete_note_signal = pyqtSignal(str) # Signal: note_id

    def __init__(self, note_id, note_title, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.note_title = note_title

        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setStyleSheet("border: 1px solid #ccc; border-radius: 5px; padding: 5px; background-color: #f9f9f9;")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5) # Smaller margins inside preview

        # Title/preview label
        self.title_label = QLabel(self.note_title)
        self.title_label.setWordWrap(True) # Ensure long titles wrap
        self.layout.addWidget(self.title_label)

        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setFixedSize(QSize(60, 25)) # Smaller delete button
        self.delete_button.clicked.connect(self._confirm_delete)
        self.delete_button.setStyleSheet("background-color: #ffcccc; border: 1px solid #ff9999; border-radius: 3px;") # Reddish delete button

        # Add delete button to a horizontal layout to push it to the right
        button_h_layout = QHBoxLayout()
        button_h_layout.addStretch()
        button_h_layout.addWidget(self.delete_button)
        self.layout.addLayout(button_h_layout)

    def mousePressEvent(self, event: QMouseEvent):
        """
        Emits a signal when the preview widget is clicked (to open the note).
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_note_signal.emit(self.note_id)
        super().mousePressEvent(event) # Call base class event handler

    def _confirm_delete(self):
        """Asks for confirmation before deleting the note."""
        reply = QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete this note from the toolbar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_note_signal.emit(self.note_id)


class SideToolbarApp(QMainWindow):
    """
    The main toolbar application that sits on the side of the screen.
    Manages loading, saving, and displaying note previews.
    """
    def __init__(self):
        super().__init__()
        # Removed the fixed window title here, as we're adding a custom title bar
        # self.setWindowTitle("Sticky Notes Toolbar")
        self.notes = {}  # Stores all note data: {note_id: note_data}
        self.open_sticky_notes = {} # Stores references to open StickyNoteWindow instances: {note_id: StickyNoteWindow}

        self._setup_ui()
        self._load_notes()
        self._display_notes()

        # Set window flags to be frameless and always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(TOOLBAR_WIDTH, QApplication.primaryScreen().size().height())
        self._position_toolbar() # Position it to the right edge of the screen

        # Optional: Make toolbar draggable if frameless, but user didn't ask for it
        # self.old_pos = None

    # def mousePressEvent(self, event: QMouseEvent):
    #     if event.button() == Qt.MouseButton.LeftButton:
    #         self.old_pos = event.globalPosition().toPoint()
    #     super().mousePressEvent(event)

    # def mouseMoveEvent(self, event: QMouseEvent):
    #     if event.buttons() == Qt.MouseButton.LeftButton and self.old_pos is not None:
    #         delta = event.globalPosition().toPoint() - self.old_pos
    #         self.move(self.x() + delta.x(), self.y() + delta.y())
    #         self.old_pos = event.globalPosition().toPoint()
    #     super().mouseMoveEvent(event)

    # def mouseReleaseEvent(self, event: QMouseEvent):
    #     self.old_pos = None
    #     super().mouseReleaseEvent(event)

    def _setup_ui(self):
        """Sets up the main toolbar GUI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0) # Removed margins for main layout to allow full custom title bar

        # Custom Title Bar for the Toolbar itself
        self.toolbar_title_bar = QFrame() # Using QFrame for the title bar to apply styles
        self.toolbar_title_bar.setFixedHeight(35)
        self.toolbar_title_bar.setStyleSheet("background-color: #A0A0A0; border-top-left-radius: 5px; border-top-right-radius: 5px;")
        self.toolbar_title_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.toolbar_title_bar_layout = QHBoxLayout(self.toolbar_title_bar)
        self.toolbar_title_bar_layout.setContentsMargins(8, 0, 8, 0)
        self.toolbar_title_bar_layout.setSpacing(8)

        self.toolbar_title_label = QLabel("Sticky Notes Toolbar")
        self.toolbar_title_label.setStyleSheet("color: black; font-weight: bold; font-size: 11pt;")
        self.toolbar_title_bar_layout.addWidget(self.toolbar_title_label)
        self.toolbar_title_bar_layout.addStretch()

        # Minimize Button for Toolbar
        self.toolbar_minimize_button = QPushButton("—")
        self.toolbar_minimize_button.setFixedSize(30, 30)
        self.toolbar_minimize_button.setStyleSheet(
            "QPushButton { background-color: #7777CC; border: 1px solid #5555AA; border-radius: 5px; color: white; font-weight: bold; font-size: 12pt; }"
            "QPushButton:hover { background-color: #5555AA; }"
        )
        self.toolbar_minimize_button.clicked.connect(self.showMinimized)
        self.toolbar_title_bar_layout.addWidget(self.toolbar_minimize_button)

        # Close Button for Toolbar
        self.toolbar_close_button = QPushButton("X")
        self.toolbar_close_button.setFixedSize(30, 30)
        self.toolbar_close_button.setStyleSheet(
            "QPushButton { background-color: #CC3333; border: 1px solid #990000; border-radius: 5px; color: white; font-weight: bold; font-size: 12pt; }"
            "QPushButton:hover { background-color: #990000; }"
        )
        self.toolbar_close_button.clicked.connect(self.close)
        self.toolbar_title_bar_layout.addWidget(self.toolbar_close_button)

        # Add the custom toolbar title bar widget to the main layout
        self.layout.addWidget(self.toolbar_title_bar)


        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter notes...")
        self.filter_input.textChanged.connect(self._filter_notes)
        # Wrap filter_input and add_note_button in a separate layout for consistent margins
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(10, 10, 10, 10) # Apply internal padding
        controls_layout.addWidget(self.filter_input)

        # Add Note Button
        self.add_note_button = QPushButton("Add New Note")
        self.add_note_button.clicked.connect(self._add_new_note)
        controls_layout.addWidget(self.add_note_button)
        self.layout.addLayout(controls_layout)


        # Scrollable area for notes list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.notes_list_widget = QWidget()
        self.notes_list_layout = QVBoxLayout(self.notes_list_widget)
        self.notes_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align items to the top
        self.notes_list_layout.setSpacing(10) # Spacing between note previews
        self.notes_list_layout.setContentsMargins(10, 10, 10, 10) # Add margins for the list content

        self.scroll_area.setWidget(self.notes_list_widget)
        self.layout.addWidget(self.scroll_area)

        # Apply rounded corners and background to the entire central widget for the toolbar
        central_widget.setStyleSheet(
            "QWidget { background-color: #E0E0E0; border-radius: 5px; border: 1px solid #AAAAAA; }"
            "QLineEdit { padding: 5px; border: 1px solid #ccc; border-radius: 3px; }"
            "QPushButton { padding: 5px; }" # Basic button styling for toolbar buttons
        )
        central_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Apply a distinct background color for the main toolbar window (topmost background)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#E0E0E0")) # Light grey
        self.setPalette(palette)
        self.setAutoFillBackground(True)


        # Make toolbar draggable by its custom title bar
        self.toolbar_title_bar.mousePressEvent = self._toolbar_mouse_press_event
        self.toolbar_title_bar.mouseMoveEvent = self._toolbar_mouse_move_event
        self.toolbar_title_bar.mouseReleaseEvent = self._toolbar_mouse_release_event
        self.old_pos = None # Initialize for dragging

    def _toolbar_mouse_press_event(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
        super(QFrame, self.toolbar_title_bar).mousePressEvent(event) # Call base QFrame handler

    def _toolbar_mouse_move_event(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
        super(QFrame, self.toolbar_title_bar).mouseMoveEvent(event)

    def _toolbar_mouse_release_event(self, event: QMouseEvent):
        self.old_pos = None
        super(QFrame, self.toolbar_title_bar).mouseReleaseEvent(event)


    def _position_toolbar(self):
        """Positions the toolbar at the right edge of the primary screen."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry() # Use availableGeometry to avoid taskbar overlap
        x = screen_geometry.width() - self.width()
        y = screen_geometry.y() # Align with top of available screen area
        self.move(x, y)

    def _load_notes(self):
        """Loads notes from the JSON file."""
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                    loaded_notes_list = json.load(f)
                    self.notes = {note["id"]: note for note in loaded_notes_list}
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {NOTES_FILE}. Starting with empty notes.")
                self.notes = {}
            except Exception as e:
                print(f"Error loading notes: {e}")
                self.notes = {}
        else:
            self.notes = {}

    def _save_notes(self):
        """Saves current notes to the JSON file."""
        try:
            with open(NOTES_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self.notes.values()), f, indent=4)
        except Exception as e:
            print(f"Error saving notes: {e}")

    def _display_notes(self):
        """Clears and re-populates the notes list in the toolbar."""
        # Clear existing widgets
        for i in reversed(range(self.notes_list_layout.count())):
            widget_to_remove = self.notes_list_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        filter_text = self.filter_input.text().lower()

        # Add notes, filtered if necessary
        # Sort notes by title for consistent display
        sorted_note_ids = sorted(self.notes.keys(), key=lambda note_id: self.notes[note_id].get("title", "").lower())

        for note_id in sorted_note_ids:
            note_data = self.notes[note_id]
            note_title = note_data.get("title", f"New Note {note_id[:8]}").strip()

            if filter_text and filter_text not in note_title.lower():
                continue # Skip if not matching filter

            preview_widget = NotePreviewWidget(note_id, note_title)
            preview_widget.open_note_signal.connect(self._open_sticky_note)
            preview_widget.delete_note_signal.connect(self._delete_note_from_toolbar)
            self.notes_list_layout.addWidget(preview_widget)

    def _filter_notes(self, text):
        """Re-displays notes based on the filter text."""
        self._display_notes()

    def _add_new_note(self):
        """Creates a new empty note and opens it."""
        new_note_id = str(uuid.uuid4())
        new_note_data = {
            "id": new_note_id,
            "title": "New Note",
            "content": "",
            "x": 100, "y": 100, "width": 400, "height": 300 # Default size and position
        }
        self.notes[new_note_id] = new_note_data
        self._save_notes()
        self._display_notes() # Update toolbar with new note
        self._open_sticky_note(new_note_id) # Open the new note immediately

    def _open_sticky_note(self, note_id):
        """Opens an existing sticky note window or brings it to front."""
        if note_id in self.open_sticky_notes and self.open_sticky_notes[note_id].isVisible():
            # If already open and visible, just bring it to front
            self.open_sticky_notes[note_id].activateWindow()
            self.open_sticky_notes[note_id].raise_()
        else:
            note_data = self.notes.get(note_id)
            if note_data:
                sticky_note_window = StickyNoteWindow(note_id, note_data)
                sticky_note_window.note_updated.connect(self._handle_note_update)
                sticky_note_window.note_deleted.connect(self._handle_note_deletion)
                self.open_sticky_notes[note_id] = sticky_note_window
                sticky_note_window.show()
            else:
                QMessageBox.warning(self, "Error", "Note not found!")

    def _handle_note_update(self, note_id, note_data):
        """Receives updates from a StickyNoteWindow and saves them."""
        self.notes[note_id] = note_data
        self._save_notes()
        self._display_notes() # Refresh toolbar in case title changed

    def _handle_note_deletion(self, note_id):
        """Handles deletion initiated from a StickyNoteWindow."""
        if note_id in self.notes:
            del self.notes[note_id]
            self._save_notes()
            self._display_notes() # Refresh toolbar
            if note_id in self.open_sticky_notes:
                self.open_sticky_notes[note_id].close() # Ensure window is closed
                del self.open_sticky_notes[note_id]

    def _delete_note_from_toolbar(self, note_id):
        """Handles deletion initiated from a NotePreviewWidget."""
        if note_id in self.notes:
            del self.notes[note_id]
            self._save_notes()
            self._display_notes() # Refresh toolbar
            if note_id in self.open_sticky_notes:
                # If the sticky note is open, close it
                self.open_sticky_notes[note_id].close()
                del self.open_sticky_notes[note_id]

    def closeEvent(self, event):
        """
        Overrides the close event for the main toolbar.
        Ensures all open sticky notes are closed and data is saved.
        """
        # Ensure all open sticky notes save their state before closing the app
        for note_id, sticky_note_window in list(self.open_sticky_notes.items()):
            if sticky_note_window.isVisible():
                sticky_note_window.close() # This will trigger note_updated signal and save state

        self._save_notes() # Final save just in case
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Optional: Set a default font for the application for better consistency
    font = QFont("Inter", 10)
    app.setFont(font)

    toolbar = SideToolbarApp()
    toolbar.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
