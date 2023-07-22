import sys
import json
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from journal import *
from tasklist import *

button_font_path = "fonts/entsans.ttf"


class TitleBar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        title_label = QLabel('ADM', self)
        title_label.setAlignment(Qt.AlignRight)  # Set the alignment to center
        title_label.setObjectName("title")
        layout.addWidget(title_label)

        # Import and register the custom font
        font_id = QFontDatabase.addApplicationFont(button_font_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        # Apply the custom font to desired widgets
        font = QFont(font_family)
        font.setPointSize(10)  # Adjust the font size as needed
        title_label.setFont(font)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Set the window title and size
        self.setWindowTitle('ADM')
        self.resize(450, 650)

        # Calculate the window position dynamically
        desktop = QDesktopWidget().availableGeometry()
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()
        x = int(desktop.width() - window_width - 10)  # Add a small offset to avoid the screen edge
        y = int(desktop.height() / window_height + 10)
        self.move(x, y)

        self.mousePos = None

        try:
            # Create a central widget and layout
            self.central_widget = QWidget(self)
            self.layout = QVBoxLayout(self.central_widget)

            # Create the title bar widget
            self.title_bar = TitleBar(self)
            self.layout.addWidget(self.title_bar)

            # Create a task list widget
            self.task_list = TaskListWidget(self.central_widget)
            self.layout.addWidget(self.task_list)

            # Create a task list history widget
            self.task_list_history = TaskListWidget(self.central_widget)
            self.layout.addWidget(self.task_list_history)
            self.task_list_history.hide()

            # Connect signals for moving tasks between task list and history list
            self.task_list.task_checked.connect(self.move_task_to_history)
            self.task_list_history.task_checked.connect(self.move_task_to_tasklist)

            # Create a task entry field and button
            entry_layout = QHBoxLayout()
            self.task_entry = QLineEdit(self.central_widget)

            entry_layout.addWidget(self.task_entry)
            self.add_button = QPushButton('Add', self.central_widget)
            self.add_button.clicked.connect(self.add_task)
            self.add_button.setFixedSize(45, 30)
            entry_layout.addWidget(self.add_button)
            self.layout.addLayout(entry_layout)
            self.task_entry.returnPressed.connect(self.add_button.click)

            # date time edit widget
            self.datetime_edit = QDateTimeEdit(self.central_widget)
            self.datetime_edit.setObjectName("date_time_widget")
            self.datetime_edit.setFixedSize(190, 30)
            self.layout.addWidget(self.datetime_edit)
            # Clear the default value to display an empty field (None)
            self.datetime_edit.clear()
            self.datetime_edit.setDate(QDate.currentDate())  # Set the default value to current date and time
            self.default_datetime = self.datetime_edit.dateTime()

            # Create a toolbar and add the journal button to it
            toolbar = QToolBar(self)
            self.addToolBar(Qt.LeftToolBarArea, toolbar)  # Align the toolbar to the left

            # Close button
            close_action = QAction(QIcon("icons/Exit.png"), 'Close', self)
            close_action.setObjectName("tool")
            close_action.triggered.connect(self.close_window)
            toolbar.addAction(close_action)

            # Keep on Top button
            keep_on_top_button = QAction(QIcon("icons/keep_on_top_button.png"), 'Keep on Top', self)
            keep_on_top_button.setObjectName("tool")
            keep_on_top_button.triggered.connect(self.toggle_keep_on_top)
            toolbar.addAction(keep_on_top_button)

            # Create a QAction object for sorting
            sort_action = QAction(QIcon("icons/filter.png"), 'Sort', self)
            sort_action.setCheckable(True)  # Make the action toggleable
            sort_action.toggled.connect(self.sort)  # Connect the toggled signal to the sort method
            toolbar.addAction(sort_action)  # Add the action to the toolbar

            # History button
            history_action = QAction(QIcon("icons/history_button.png"), 'History', self)
            history_action.setObjectName("tool")
            history_action.triggered.connect(self.toggle_history)
            toolbar.addAction(history_action)

            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            toolbar.addWidget(spacer)

            # Journal button
            journal_button = QAction(QIcon("icons/journal_button.png"), 'Journal', self)
            journal_button.setObjectName("tool")
            journal_button.triggered.connect(self.open_journal)
            toolbar.addAction(journal_button)

            self.setCentralWidget(self.central_widget)

            # Exclude the "Add Task" button from CSS styling
            self.add_button.setStyleSheet("")

            # Create a slider for resizing the window
            self.resize_slider = QSlider(Qt.Horizontal, self.central_widget)
            self.resize_slider.setMinimum(200)
            self.resize_slider.setMaximum(800)
            self.resize_slider.setTickInterval(50)
            self.resize_slider.setSingleStep(10)
            self.resize_slider.setValue(450)
            self.resize_slider.valueChanged.connect(self.on_resize_slider_changed)
            self.layout.addWidget(self.resize_slider, alignment=Qt.AlignBottom)

            self.task_list.add_task(Task("Task"))  # Create a Task object when adding a task
            self.task_list_history.add_task(Task("Task", False))  # Create a Task object for history

        except Exception as e:
            print(f"An error occurred while initializing the application: {e}")

    def sort(self, checked):
        self.task_list.sort_tasks(reverse=checked)

    def close_window(self):
        self.window().close()

    def toggle_history(self):
        if self.task_list.isVisible():
            self.task_list.hide()
            self.task_entry.hide()
            self.add_button.hide()
            self.datetime_edit.hide()
            self.task_list_history.show()
        else:
            self.task_list.show()
            self.task_entry.show()
            self.add_button.show()
            self.datetime_edit.show()
            self.task_list_history.hide()

    def toggle_keep_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowStaysOnTopHint:
            flags &= ~Qt.WindowStaysOnTopHint
        else:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def mousePressEvent(self, event):
        self.mousePos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.mousePos:
            diff = event.globalPos() - self.mousePos
            newpos = self.pos() + diff
            self.move(newpos)
            self.mousePos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.mousePos = None

    def add_task(self):
        try:
            task_text = self.task_entry.text()
            # Check if the user has entered a valid date-time
            if self.datetime_edit.dateTime() != self.default_datetime:
                selected_date = self.datetime_edit.date().toString("yyyy-MM-dd")
                print(f"Due-date set: {selected_date}")
            else:
                selected_date = ""

            if self.datetime_edit.time() != self.default_datetime.time():
                selected_time = self.datetime_edit.time().toString("hh:mm ap")
            else:
                selected_time = ""

            if task_text:
                task = Task(task_text, due_date=selected_date, due_time=selected_time)  # Create a Task object
                self.task_list.add_task(task)  # Pass the Task object to the add_task method
                self.task_entry.clear()
                self.datetime_edit.setDate(QDate.currentDate())
                self.datetime_edit.setTime(self.default_datetime.time())

        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def move_task_to_history(self, task):
        # Function to move a task from task list to history list
        self.task_list.remove_task(task)
        self.task_list_history.add_task(task)

    def move_task_to_tasklist(self, task):
        # Function to move a task from history list to task list
        self.task_list_history.remove_task(task)
        self.task_list.add_task(task)

    @staticmethod
    def open_journal():
        try:
            open_journal()

        except Exception as e:
            print(f"An error occurred while opening the journal: {e}")

    def on_resize_slider_changed(self, value):
        new_width = value
        new_height = value + 200
        if value < 500:
            self.resize(new_width, new_height)
        else:
            self.resize(500, new_height)


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        # Load the style sheet
        with open('style.css', 'r') as style_file:
            window.setStyleSheet(style_file.read())
        window.show()
        sys.exit(app.exec_())

    except Exception as e:
        print(f"An error occurred in the application: {e}")
