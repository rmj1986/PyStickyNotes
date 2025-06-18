# Sticky Notes Desktop Application (PyQt6)

This Python application provides a convenient desktop sticky notes solution, implemented using the PyQt6 framework. It features a discreet side toolbar for managing your notes efficiently and individual sticky note windows for detailed content. All note data is persistently saved to a local JSON file.

## Features

* **Side Toolbar:** A minimalist toolbar that sits on the right edge of your screen, always on top, for quick access to your notes.
    * **Toolbar Filter:** A search bar at the top of the toolbar allows you to filter the list of notes by text as you type.
    * **Add New Note:** A dedicated button to instantly create a fresh sticky note.
    * **Note Previews:** Each note is represented by a compact preview, displaying its first few lines, allowing for quick identification.
    * **Delete from Toolbar:** A "Delete" button on each note preview for quick removal of notes without opening them.

* **Individual Sticky Note Windows:**
    * **Draggable and Resizable:** Each sticky note opens in its own window, which you can freely drag around your desktop and resize to your preferred dimensions.
    * **Custom Window Controls:** Includes custom minimize and close buttons directly on the note's title bar for consistent behavior across different operating systems.
    * **Rich Text Editor:** Powered by `QTextEdit`, notes support:
        * Plain and rich text formatting.
        * Embedding images (e.g., by pasting from clipboard).
        * Pasting and displaying tables.
    * **Automatic Saving:** All changes to note content, position, and size are saved automatically as you make them.

* **Data Persistence:** All your notes are saved to a local `sticky_notes_data.json` file and automatically reloaded when you restart the application, ensuring your information is never lost.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rmj1986/PyStickyNotes.git
    cd sticky-notes-app
    ```
    
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install PyQt6
    ```

## How to Run

After installation, run the application from your terminal:

```bash
python stickyNotes.py

```
The toolbar will appear on the right side of your primary screen.

## Usage

1. **Add a New Note:** Click the "Add New Note" button on the toolbar. A new sticky note window will appear.

2. **Edit Content:** Type or paste text, images, or tables directly into the sticky note window. Changes are saved automatically.

3. **Move/Resize Notes:** Drag the custom title bar of a sticky note to move it. Drag the edges or corners to resize it (the cursor will change to indicate resizeable areas).

4. **Minimize/Close Notes:** Use the "—" (minimize) and "X" (close) buttons in the sticky note's custom title bar.

5. **Filter Notes (Toolbar):** Use the "Filter notes..." input on the toolbar to show only notes whose title or preview content contains the typed text.

6. **Delete Notes:**

   * From the toolbar: Click the "Delete" button next to a note preview.

   * From the sticky note window: Click the "Delete Note" button at the bottom of the sticky note window.

7. **Exit Application:** Close the main toolbar window using its "X" button. All open sticky notes will also close, and their state will be saved.

## File Structure

* `sticky_notes.py`: The main application code.

* `sticky_notes_data.json`: (Created automatically) Stores all your sticky note content and window states.

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is open-source and available under the [MIT License](LICENSE).
