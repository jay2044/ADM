import json
import os
import random
import time
import pickle
from plyer import notification
import schedule
import threading
from datetime import datetime, timedelta

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint, QDate
from PyQt5.QtGui import QDrag


class Task:
    def __init__(self, name, pending=True, priority=0, due_date="", due_time=""):
        self.name = name
        self.pending = pending
        self.priority = priority
        self.due_date = due_date
        self.due_time = due_time
        self.is_important = False  # You can add more properties as needed
        self.added_date_time = datetime.now()


class TaskListWidget(QListWidget):
    task_checked = pyqtSignal(Task)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("tasks")
        self.setSpacing(4)  # Set spacing between tasks.
        self.setDragDropMode(QAbstractItemView.InternalMove)  # Enable dragging and dropping of items
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.start()

    def run_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def show_context_menu(self, position):
        # Get the task item on which the user clicked
        item = self.itemAt(position)
        if item is None:  # No item under the cursor
            return

        # Create a QMenu
        menu = QMenu(self)

        # Add actions to the menu
        edit_name_action = QAction('Edit Name', self)
        edit_name_action.triggered.connect(lambda: self.edit_name(item))
        menu.addAction(edit_name_action)

        # Create a QWidgetAction for the QDateTimeEdit widget
        datetime_action = QWidgetAction(self)
        datetime_edit = QDateTimeEdit()
        datetime_edit.setDate(QDate.currentDate())  # Set the default value to current date
        datetime_action.setDefaultWidget(datetime_edit)
        menu.addAction(datetime_action)

        # Create a variable to keep track of whether the time has been changed
        self.time_changed = False
        # Connect the timeChanged signal to a lambda function that sets self.time_changed to True
        datetime_edit.timeChanged.connect(lambda: setattr(self, 'time_changed', True))

        # Connect the dateTimeChanged signal to the change_due_date method
        datetime_edit.dateTimeChanged.connect(lambda: self.change_due_date(item, datetime_edit))

        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(lambda: self.delete_task(item))
        menu.addAction(delete_action)

        # Show the menu
        menu.exec_(self.mapToGlobal(position))

    def edit_name(self, item):
        # Create a custom dialog
        dialog = QDialog(self, Qt.FramelessWindowHint)  # The FramelessWindowHint flag removes the title bar
        dialog.setObjectName("edit_name_dialog")  # Set the object name for CSS

        # Create a layout for the dialog
        layout = QVBoxLayout(dialog)

        # Create a QLineEdit for the user to enter the new task name
        line_edit = QLineEdit()
        line_edit.setObjectName("edit_name_line_edit")  # Set the object name for CSS
        layout.addWidget(line_edit)

        # Create a QPushButton for the user to confirm the new task name
        button = QPushButton('OK')
        button.setObjectName("edit_name_button")  # Set the object name for CSS
        layout.addWidget(button)

        # Connect the QPushButton's clicked signal to the QDialog's accept slot
        button.clicked.connect(dialog.accept)

        # Show the dialog and wait for the user to close it
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_name = line_edit.text()
            if new_name:
                # Get the task object from the item
                task = item.data(Qt.UserRole)
                # Update the task name
                task.name = new_name
                # Update the checkbox text
                checkbox = self.itemWidget(item).findChild(QCheckBox, "task_checkbox")
                checkbox.setText(new_name)

    def change_due_date(self, item, datetime_edit):
        # Get the new due date from the QDateTimeEdit widget
        new_due_date = datetime_edit.date().toString("yyyy-MM-dd")

        # If the time has been changed, get the new due time; otherwise, set it to an empty string
        if self.time_changed:
            new_due_time = datetime_edit.time().toString("hh:mm ap")
        else:
            new_due_time = ""

        # Get the task object from the item
        task = item.data(Qt.UserRole)
        # Update the task due date and due time
        task.due_date = new_due_date
        task.due_time = new_due_time

        # Update the due date label text
        due_date_label = self.itemWidget(item).findChild(QLabel, "due_date_label")
        due_date_label.setText(f"{new_due_date} {new_due_time if new_due_time else ''}")

    def delete_task(self, item):
        # Ask the user to confirm deletion
        reply = QMessageBox.question(self, 'Delete Task', 'Are you sure you want to delete this task?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Get the task object from the item
            task = item.data(Qt.UserRole)
            # Remove the task
            self.remove_task(task)

    def startDrag(self, supportedActions):
        drag = QDrag(self)
        mimeData = self.mimeData(self.selectedItems())
        drag.setMimeData(mimeData)
        drag.exec_(Qt.MoveAction)

    def dropMimeData(self, index, data, action):
        dropPos = self.viewport().mapFromGlobal(QCursor.pos())

        if self.viewport().rect().contains(dropPos):
            return super().dropMimeData(index, data, action)
        else:
            return False

    def sort_tasks(self, reverse=False):
        # Get the number of tasks
        task_count = self.count()
        # Get all tasks
        tasks = [self.item(i).data(Qt.UserRole) for i in range(task_count)]
        # Separate the tasks into important tasks and other tasks
        important_tasks = [task for task in tasks if task.is_important]
        other_tasks = [task for task in tasks if not task.is_important]
        # Sort each list by added_date_time
        important_tasks = sorted(important_tasks, key=lambda task: task.added_date_time, reverse=reverse)
        other_tasks = sorted(other_tasks, key=lambda task: task.added_date_time, reverse=reverse)
        # Concatenate the two lists with important tasks at the top
        sorted_tasks = important_tasks + other_tasks
        # Clear the current task list
        self.clear()
        # Add the sorted tasks to the task list
        for task in sorted_tasks:
            self.add_task(task)

    def add_task(self, task_obj):
        try:
            item = QListWidgetItem()
            widget = QWidget()
            widget.setObjectName("task_item")
            layout = QHBoxLayout(widget)

            checkbox = QCheckBox(task_obj.name)
            checkbox.setObjectName("task_checkbox")
            checkbox.setChecked(False)  # Set the checkbox state to unchecked
            checkbox.stateChanged.connect(lambda state, t=task_obj: self.handle_checkbox_state(state, t))
            layout.addWidget(checkbox, alignment=Qt.AlignLeft)

            due_date = QLabel(f"{task_obj.due_date} {task_obj.due_time}")
            due_date.setObjectName("due_date_label")
            due_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            # Check if the task is due today
            if task_obj.due_date and datetime.strptime(task_obj.due_date, '%Y-%m-%d').date() == datetime.now().date():
                # Change the color of the label to red
                due_date.setStyleSheet("color: red;")
            layout.addWidget(due_date)

            # Create a QPushButton for the star button
            star_button = QCheckBox()  # You can use any icon/text for the star button
            star_button.setObjectName("star_button")
            if task_obj.is_important:
                star_button.setChecked(True)  # Set the star button state to unchecked
            else:
                star_button.setChecked(False)
            star_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            star_button.stateChanged.connect(lambda checked, t=task_obj: self.handle_star_button(checked, t))
            layout.addWidget(star_button)

            layout.setSpacing(5)
            item.setSizeHint(widget.sizeHint())

            # Set the task object as a custom property of the QListWidgetItem
            item.setData(Qt.UserRole, task_obj)

            self.addItem(item)
            self.setItemWidget(item, widget)
            print(f"{task_obj.name} is added")
            print(task_obj.due_date)

            # Schedule a notification for 5 minutes before the task's due time
            due_datetime_str = task_obj.due_date + ' ' + task_obj.due_time
            due_datetime = datetime.strptime(due_datetime_str, '%Y-%m-%d %I:%M %p')
            notification_time = due_datetime - timedelta(minutes=5)

            if notification_time > datetime.now():
                schedule.every().day.at(notification_time.strftime('%H:%M')).do(
                    self.send_notification,
                    task_obj.name,
                    'is due in 5 minutes.'
                )

            # Schedule a notification for the task's due time
            if due_datetime > datetime.now():
                schedule.every().day.at(due_datetime.strftime('%H:%M')).do(
                    self.send_notification,
                    task_obj.name,
                    'is now due.'
                )

        except Exception as e:
                print(f"An error occurred while adding a task: {e}")

    def send_notification(self, task_name, message):
        notification.notify(
            title='Task Due',
            message=f'Task {task_name} {message}',
            app_name='Task Manager',
            # add a path to your icon file here if you have one
            app_icon=None
        )

    def remove_task(self, task_obj):
        try:
            for index in range(self.count()):
                item = self.item(index)
                stored_task_obj = item.data(Qt.UserRole)

                if stored_task_obj == task_obj:
                    self.takeItem(index)
                    print(f"{task_obj.name} is removed")
                    break

        except Exception as e:
            print(f"An error occurred while removing a task: {e}")

    def handle_checkbox_state(self, state, task):
        try:
            if state == 2:  # Checked state
                self.task_checked.emit(task)  # Emit the Task object instead of task name (string)
                if task.pending:
                    task.pending = False
                else:
                    task.pending = True

        except Exception as e:
            print(f"An error occurred while handling checkbox state: {e}")

    def handle_star_button(self, checked, task_obj):
        try:
            task_obj.is_important = checked
            if checked:
                print(f"Task '{task_obj.name}' is marked as important.")
                task_obj.is_important = True
            else:
                print(f"Task '{task_obj.name}' is no longer important.")
                task_obj.is_important = False
            # Sort the tasks after changing the importance of a task
            self.sort_tasks(reverse=False)

        except Exception as e:
            print(f"An error occurred while handling star button click: {e}")

    def save_tasks_to_pickle(self, file_path):
        """Save all tasks to a pickle file."""
        task_list = [self.item(i).data(Qt.UserRole) for i in range(self.count())]
        with open(file_path, 'wb') as file:
            pickle.dump(task_list, file)

    def load_tasks_from_pickle(self, file_path):
        """Load tasks from a pickle file and add them to the task list."""
        with open(file_path, 'rb') as file:
            task_list = pickle.load(file)
        for task in task_list:
            self.add_task(task)
