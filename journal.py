import sys
import json
import datetime
import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, \
    QListWidget, QListWidgetItem, QScrollArea, QToolBar, QAction, QWidget, QSizePolicy, QLineEdit, QHBoxLayout
from PyQt5.QtGui import QFontDatabase, QFont, QMouseEvent
from PyQt5 import QtCore

MAX_CONTENT_LENGTH = 20
journal_window = None
screen = 0
mousePos = None

button_font_path = "fonts/entsans.ttf"


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
        toolbar = QToolBar(journal_window)
        journal_window.addToolBar(Qt.LeftToolBarArea, toolbar)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # Align toolbar buttons text beside the icon

        back_action = QAction('Back', journal_window)
        back_action.triggered.connect(back_button)
        toolbar.addAction(back_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        show_entries_action = QAction('Entries', journal_window)
        show_entries_action.triggered.connect(lambda: show_all_entries(journal_window))
        toolbar.addAction(show_entries_action)

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
        lambda: save_journal_entry(journal_window, title_entry.text(), content_entry.toPlainText(), quote_entry.text()))

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


def save_journal_entry(window, title, content, quote):
    try:
        entry = {
            "date": str(datetime.date.today()),
            "title": title,
            "content": content,
            "quote": quote
        }

        with open('journal_entries.json', 'a') as file:
            json.dump(entry, file)
            file.write('\n')

        window.close()

    except Exception as e:
        print(f"An error occurred while saving the journal entry: {e}")


def show_all_entries(window):
    global screen

    try:
        entries = []
        with open('journal_entries.json', 'r') as file:
            for line in file:
                entries.append(json.loads(line))

        # Clear the existing layout
        clear_layout(window.centralWidget().layout())

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

        # Add the search layout to the main layout
        window.centralWidget().layout().addLayout(search_layout)

        scroll_widget = QWidget(window)
        scroll_layout = QVBoxLayout(scroll_widget)

        entry_list_widget = QListWidget(scroll_widget)
        entry_list_widget.setObjectName("entries_list")
        entry_list_widget.itemClicked.connect(lambda item: open_entry_window(window, item.text()))

        for entry in entries:
            content = entry['content']
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "..."

            item = QListWidgetItem()
            item.setText(
                f"Date: {entry['date']}\nTitle: {entry['title']}\nContent:\n{content}\nWhat I Learned Today (Quote): {entry['quote']}\n")
            entry_list_widget.addItem(item)

        scroll_layout.addWidget(entry_list_widget)
        scroll_area = QScrollArea(window)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        window.centralWidget().layout().addWidget(scroll_area)

        screen = 2

    except Exception as e:
        print(f"An error occurred while showing all entries: {e}")


def filter_entries(window, search_query, entries):
    try:
        filtered_entries = []
        search_query = search_query.lower().replace(" ", "")  # Remove whitespace from search query
        for entry in entries:
            # Remove whitespace from entry fields before comparing
            entry_date = entry['date'].lower().replace(" ", "")
            entry_title = entry['title'].lower().replace(" ", "")
            entry_content = entry['content'].lower().replace(" ", "")

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
                content = entry['content']
                if len(content) > MAX_CONTENT_LENGTH:
                    content = content[:MAX_CONTENT_LENGTH] + "..."

                item = QListWidgetItem()
                item.setText(
                    f"Date: {entry['date']}\nTitle: {entry['title']}\nContent:\n{content}\nWhat I Learned Today (Quote): {entry['quote']}\n")
                entry_list_widget.addItem(item)
        else:
            item = QListWidgetItem()
            item.setText("No results found.")
            entry_list_widget.addItem(item)


def open_entry_window(window, entry_text):
    global screen

    try:
        entry_lines = entry_text.split('\n')
        entry_lines = [line.strip() for line in entry_lines if line.strip()]

        # Clear the existing layout
        clear_layout(window.centralWidget().layout())

        entry_widget = QWidget(window)
        entry_layout = QVBoxLayout(entry_widget)

        for line in entry_lines:
            label = QLabel(line, entry_widget)
            entry_layout.addWidget(label)

        window.setCentralWidget(entry_widget)
        screen = 3

    except Exception as e:
        print(f"An error occurred while opening the entry window: {e}")


def back_button():
    global screen

    screen -= 1

    if screen == 0:
        journal_window.close()
    elif screen == 1:
        save_menu()
    elif screen == 2:
        show_all_entries(journal_window)
    elif screen == 3:
        show_all_entries(journal_window)


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        open_journal()
        sys.exit(app.exec_())

    except Exception as e:
        print(f"An error occurred in the application: {e}")
