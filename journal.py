import sys
import json
from datetime import datetime
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import *

MAX_CONTENT_LENGTH = 20
journal_window = None
screen = 0
mousePos = None

button_font_path = "fonts/entsans.ttf"


class JournalEntry:
    def __init__(self, title, content, quote, date=datetime.now().strftime('%Y-%m-%d %H:%M')):
        self.title = title
        self.content = content
        self.quote = quote
        self.date = date


def open_journal():
    global journal_window, screen

    try:
        # Create the journal window
        journal_window = QMainWindow()
        journal_window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        journal_window.setWindowTitle('Daily Journal')
        screen_geometry = QApplication.primaryScreen().geometry()
        window_width = 800
        window_height = 800
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        journal_window.setGeometry(x, y, window_width, window_height)

        journal_window.mousePressEvent = mousePressEvent
        journal_window.mouseMoveEvent = mouseMoveEvent
        journal_window.mouseReleaseEvent = mouseReleaseEvent

        # Create the toolbar
        global toolbar
        toolbar = QToolBar(journal_window)
        journal_window.addToolBar(Qt.LeftToolBarArea, toolbar)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # Align toolbar buttons text beside the icon

        back_action = QAction('Back', journal_window)
        back_action.triggered.connect(back_button)
        toolbar.addAction(back_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        global show_entries_action
        show_entries_action = QAction('Entries', journal_window)
        show_entries_action.triggered.connect(lambda: show_all_entries(journal_window))
        toolbar.addAction(show_entries_action)

        global sort_action
        sort_action = QAction(QIcon("icons/filter.png"), 'Sort', journal_window)
        sort_action.setCheckable(True)  # Make the action toggleable
        sort_action.setChecked(True)
        sort_action.toggled.connect(sort_entries)  # Connect the toggled signal to the sort method
        toolbar.addAction(sort_action)  # Add the action to the toolbar
        sort_action.setVisible(False)

        save_menu()

        # Apply the custom font to labels and button
        font_id = QFontDatabase.addApplicationFont(button_font_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_family)
        font.setPointSize(10)
        back_action.setFont(font)
        show_entries_action.setFont(font)

        # Load the style sheet
        with open('style.css', 'r') as style_file:
            journal_window.setStyleSheet(style_file.read())

    except Exception as e:
        print(f"An error occurred while opening the journal window: {e}")


def save_menu():
    global screen

    # Create the central widget and layout
    central_widget = QWidget(journal_window)
    layout = QVBoxLayout(central_widget)

    # Create the journal entry fields
    title_label = QLabel('Title:', central_widget)
    title_entry = QLineEdit(central_widget)

    content_label = QLabel('Content:', central_widget)
    content_entry = QTextEdit(central_widget)

    quote_label = QLabel('What I Learned Today (Quote):', central_widget)
    quote_entry = QLineEdit(central_widget)

    save_button = QPushButton('Save Entry', central_widget)
    save_button.clicked.connect(
        lambda: save_journal_entry(journal_window, title_entry, content_entry, quote_entry))

    # Create the layout
    layout.addWidget(title_label)
    layout.addWidget(title_entry)
    layout.addWidget(content_label)
    layout.addWidget(content_entry)
    layout.addWidget(quote_label)
    layout.addWidget(quote_entry)
    layout.addWidget(save_button)

    journal_window.setCentralWidget(central_widget)
    journal_window.show()
    screen = 1


def save_journal_entry(window, title_entry, content_entry, quote_entry):
    try:
        title = title_entry.text()
        content = content_entry.toPlainText()
        quote = quote_entry.text()

        entry = JournalEntry(title, content, quote)

        with open('journal_entries.json', 'a') as file:
            json.dump(entry.__dict__, file)
            file.write('\n')

        # Clear the line edits
        title_entry.clear()
        content_entry.clear()
        quote_entry.clear()

    except Exception as e:
        print(f"An error occurred while saving the journal entry: {e}")


def show_all_entries(window):
    global screen, journal_window, show_entries_action

    try:
        entries = []

        # Open the file in read mode, create it if it doesn't exist
        with open('journal_entries.json', 'a+') as file:
            file.seek(0)  # Move the cursor to the beginning of the file
            for line in file:
                entry = json.loads(line)
                entries.append(
                    JournalEntry(entry['title'], entry['content'], entry['quote'], entry['date']))

        entries.sort(key=lambda x: x.date, reverse=True)

        # Create a search bar widget
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search Entries")
        search_bar.setObjectName("search_bar")

        # Create a search button
        search_button = QPushButton("Search")
        search_button.setObjectName("search_button")
        search_button.clicked.connect(lambda: filter_entries(window, search_bar.text(), entries))
        # Connect the returnPressed signal of the search bar to the search button's click slot
        search_bar.returnPressed.connect(search_button.click)

        # Create a horizontal layout for the search bar and button
        search_layout = QHBoxLayout()
        search_layout.addWidget(search_bar)
        search_layout.addWidget(search_button)

        # Create the central widget and layout
        central_widget = QWidget(journal_window)
        layout = QVBoxLayout(central_widget)

        # Add the search layout to the main layout
        layout.addLayout(search_layout)

        entry_list_widget = QListWidget()
        entry_list_widget.setObjectName("entries_list")
        entry_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        entry_list_widget.itemClicked.connect(
            lambda item: open_entry(window, item.data(Qt.UserRole)))  # Pass the entry object to open_entry
        entry_list_widget.customContextMenuRequested.connect(
            lambda pos: show_context_menu(pos, entry_list_widget, entries))

        for entry in entries:
            if len(entry.content) > MAX_CONTENT_LENGTH:
                content = entry.content[:MAX_CONTENT_LENGTH] + "..."
            else:
                content = entry.content
            item = QListWidgetItem(
                f"Date: {entry.date}\nTitle: {entry.title}\nContent:\n{content}\nWhat I Learned Today (Quote): {entry.quote}\n"
            )
            item.setData(Qt.UserRole, entry)  # Store the entry object as the item's data
            entry_list_widget.addItem(item)

        # Add the list widget to the main layout
        layout.addWidget(entry_list_widget)

        # Set the central widget
        journal_window.setCentralWidget(central_widget)

        sort_action.setVisible(True)
        show_entries_action.setVisible(False)

        screen = 2

    except Exception as e:
        print(f"An error occurred while showing all entries: {e}")


def show_context_menu(position, list_widget, entries):
    menu = QMenu()
    with open('style.css', 'r') as style_file:
        menu.setStyleSheet(style_file.read())
    delete_action = menu.addAction("Delete")
    delete_action.triggered.connect(lambda: delete_entry(list_widget.itemAt(position), list_widget, entries))
    menu.exec_(list_widget.viewport().mapToGlobal(position))


def delete_entry(item, list_widget, entries):
    if item is None:
        return

    # Get the title of the entry to be deleted
    item_text = item.text()
    lines = item_text.split('\n')
    entry_title = ""
    for line in lines:
        if line.startswith('Title: '):
            # Extract the title from the line
            entry_title = line[len('Title: '):]
            break

    # Delete the entry from the entries list
    deleted_entry = None
    for entry in entries:
        if entry.title == entry_title:
            deleted_entry = entry
            entries.remove(entry)
            break

    if deleted_entry is None:
        print("Error: Entry not found.")
        return

    # Write the updated entries back to the JSON file
    with open('journal_entries.json', 'w') as file:
        for entry in entries:
            file.write(json.dumps(entry.__dict__) + '\n')

    # Delete the entry from the GUI
    list_widget.takeItem(list_widget.row(item))


def sort_entries(checked):
    try:
        entries = []

        # Open the file in read mode, create it if it doesn't exist
        with open('journal_entries.json', 'a+') as file:
            file.seek(0)  # Move the cursor to the beginning of the file
            for line in file:
                entry = json.loads(line)
                entries.append(
                    JournalEntry(entry['title'], entry['content'], entry['quote'], entry['date']))

        # Sort the entries by date
        entries.sort(key=lambda x: x.date, reverse=checked)

        # Update the displayed entries
        update_entry_list(journal_window, entries)

    except Exception as e:
        print(f"An error occurred while sorting the entries: {e}")


def filter_entries(window, search_query, entries):
    try:
        filtered_entries = []
        search_query = search_query.lower().replace(" ", "")  # Remove whitespace from search query
        for entry in entries:
            # Remove whitespace from entry fields before comparing
            entry_date = entry.date.replace(" ", "")
            entry_title = entry.title.lower().replace(" ", "")
            entry_content = entry.content.lower().replace(" ", "")

            if search_query in entry_date or search_query in entry_title or search_query in entry_content:
                filtered_entries.append(entry)

        # Update the displayed entries based on the filtered results
        update_entry_list(window, filtered_entries)

    except Exception as e:
        print(f"An error occurred while filtering entries: {e}")


def update_entry_list(window, entries):
    entry_list_widget = window.findChild(QListWidget, "entries_list")
    if entry_list_widget:
        entry_list_widget.clear()

        if entries:
            for entry in entries:
                if len(entry.content) > MAX_CONTENT_LENGTH:
                    content = entry.content[:MAX_CONTENT_LENGTH] + "..."
                else:
                    content = entry.content
                entry_list_widget.addItem(QListWidgetItem(
                    f"Date: {entry.date}\nTitle: {entry.title}\nContent:\n{content}\nWhat I Learned Today (Quote): {entry.quote}\n"))
        else:
            item = QListWidgetItem()
            item.setText("No results found.")
            entry_list_widget.addItem(item)



def open_entry(window, entry):
    global screen

    # Read the HTML template from the file
    with open("template.html", "r") as file:
        html_template = file.read()

    # Replace the placeholders with the entry data
    html_content = html_template.format(
        title=entry.title,
        date=entry.date,
        content=entry.content.replace("\n", "<br>"),  # Replace newlines with <br> for HTML
        quote=entry.quote
    )

    # Create a QTextBrowser and set its HTML
    text_browser = QTextBrowser()
    text_browser.setHtml(html_content)

    # Add the QTextBrowser to the window
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    layout.addWidget(text_browser)
    window.setCentralWidget(central_widget)

    sort_action.setVisible(False)
    screen = 3


def back_button():
    global screen, show_entries_action, sort_action

    screen -= 1

    if screen == 0:
        journal_window.close()
    elif screen == 1:
        show_entries_action.setVisible(True)
        sort_action.setVisible(False)
        save_menu()
    elif screen == 2:
        sort_action.setVisible(True)
        show_entries_action.setVisible(False)
        show_all_entries(journal_window)
    elif screen == 3:
        sort_action.setVisible(False)
        show_entries_action.setVisible(False)
        open_entry(journal_window)


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


def mousePressEvent(event: QMouseEvent):
    global mousePos
    if event.button() == QtCore.Qt.LeftButton:
        mousePos = event.globalPos() - journal_window.pos()
        event.accept()


def mouseMoveEvent(event: QMouseEvent):
    global mousePos
    if event.buttons() == QtCore.Qt.LeftButton:
        journal_window.move(event.globalPos() - mousePos)
        event.accept()


def mouseReleaseEvent(event: QMouseEvent):
    global mousePos
    if event.button() == QtCore.Qt.LeftButton:
        mousePos = None
        event.accept()


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        open_journal()
        sys.exit(app.exec_())

    except Exception as e:
        print(f"An error occurred in the application: {e}")
