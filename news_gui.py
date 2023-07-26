from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QUrl
from NewsAPI import get_news  # Import your function from NewsAPI.py
import urllib

class NewsApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('NewsApp')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 800, 650)  # Set the window size

        self.list_widget = QListWidget()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.list_widget)
        self.setLayout(self.layout)

        self.list_widget.itemClicked.connect(self.open_url)

        self.count = 1
        self.load_news()

        self.mousePos = None

    def load_news(self):
        response = get_news('business')  # Call your function to get news data
        news_items = response['articles']  # Access the 'articles' list from the response
        for item in news_items:
            list_item = QListWidgetItem()

            cell = QHBoxLayout()  # This is the main layout
            widget = QWidget()
            widget.setLayout(cell)

            layout = QVBoxLayout()  # This layout is for the text
            title = QLabel()
            title.setObjectName('news_title')
            title.setText(f"<b>{self.count}. {item['title']}</b>")
            self.count += 1
            title.setWordWrap(True)
            # Set the font for the title label
            title_font = QFont("Arial", 12, QFont.Bold)  # Customize the font as needed
            title.setFont(title_font)
            layout.addWidget(title)
            desc = QLabel()
            desc.setObjectName('news_desc')
            desc.setText(item['description'])
            desc.setWordWrap(True)
            # Set the font for the description label
            desc_font = QFont("Arial", 10)  # Customize the font as needed
            desc.setFont(desc_font)
            layout.addWidget(desc)

            layout.addStretch()

            cell.addLayout(layout)  # Add the text layout to the main layout

            image_url = item.get('urlToImage')
            if image_url is not None:
                try:
                    data = urllib.request.urlopen(image_url).read()
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)
                    pixmap = pixmap.scaled(300, 250, Qt.KeepAspectRatio)  # Scale pixmap
                    image_label = QLabel()
                    image_label.setPixmap(pixmap)
                    cell.addWidget(image_label)  # Add the image to the main layout
                except Exception as e:
                    print(f"Failed to download image from {image_url} due to {e}")

            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, widget)
            list_item.setData(Qt.UserRole, item['url'])  # Store the URL in the item
            list_item.setSizeHint(widget.sizeHint())  # Set the size hint of the list item to match the widget

    def open_url(self, item):
        url = QUrl(item.data(Qt.UserRole))
        QDesktopServices.openUrl(url)

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

app = QApplication([])
window = NewsApp()
window.setObjectName('news_window')
with open('style.css', 'r') as style_file:
    window.setStyleSheet(style_file.read())
window.show()
app.exec_()
