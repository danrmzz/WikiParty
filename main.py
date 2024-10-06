import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QMovie, QIcon
import threading
import time
from bs4 import BeautifulSoup
import os
import wikipediaapi
import threading
import json
import string
from PyQt5.QtNetwork import QTcpSocket, QAbstractSocket

# Server IP and port (must match server settings)
SERVER_IP = "34.171.41.219"  # Replace with the actual server's IP address
SERVER_PORT = 3389

start_url = ""
end_url = ""
end_title = ""
winner = ""
game_over_message = ""
winner_num_clicks = 0
winner_time_taken = ""

# Stats
num_clicks = -1
start_time = 0
end_time = 0
timer = 300
time_taken = 0

class Window(QStackedWidget):
    update_timer_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("WikiParty")
        self.resize(800, 650)  # Initial resolution before expanding

        # Create the start screen
        self.start_screen = QWidget()
        start_layout = QVBoxLayout(self.start_screen)

        # Set margins for start screen layout
        start_layout.setContentsMargins(40, 40, 40, 40)  # Set margins (left, top, right, bottom)
        start_layout.setSpacing(10)  # Optional: Adjust spacing between widgets

        # Create and add an image
        self.image_label = QLabel(self.start_screen)
        pixmap = QPixmap("wikiparty_logo.png")  # Use full path for Windows

        # Check if the image loads successfully
        if pixmap.isNull():
            print("Failed to load image.")
        else:
            self.image_label.setPixmap(pixmap.scaled(400, 300, Qt.KeepAspectRatio))  # Set a fixed size for the image
            self.image_label.setAlignment(Qt.AlignCenter)
            start_layout.addWidget(self.image_label)

        # Create a QLabel to add text
        self.start_label = QLabel("Welcome to <b>WikiParty</b>! You are given a random Wikipedia page with the goal of reaching a destination page using only the hyperlinks present on each page. <br>You have <b>5 minutes</b> to get there!<br><br> Enter your username:")
        self.start_label.setAlignment(Qt.AlignCenter)
        self.start_label.setWordWrap(True)  # Enable word wrapping
        start_layout.addWidget(self.start_label)  # Add the label to the button screen layout

        # Create a QLineEdit for username input
        self.username_input = QLineEdit(self.start_screen)
        self.username_input.setAlignment(Qt.AlignCenter)
        start_layout.addWidget(self.username_input)

        # Clear focus from the input field
        self.username_input.clearFocus()

        # Set focus to another widget to ensure the placeholder text shows
        self.start_screen.setFocus()

        # Connect the returnPressed signal to the show_waiting_room method
        self.username_input.returnPressed.connect(self.show_waiting_room)


        # Create a horizontal layout for the buttons
        button_h_layout = QHBoxLayout()

        # Create a drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(Qt.gray)

        # Create the "Join" button
        self.join_button = QPushButton("Join", self.start_screen)  # type: ignore
        # Style the button: Blue, rounded corners, larger size
        self.join_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;  /* Blue color */
                color: white;
                border-radius: 15px;  /* Rounded corners */
                padding: 20px 40px;   /* Larger padding */
                font-size: 16pt;      /* Larger font size */
                font-family: 'Poppins ExtraBold';
                margin-top: 0px;
                }
                QPushButton:hover {
                    background-color: #0056b3;  /* Darker blue when hovered */
                    cursor: pointer;
                }
        """)

        self.join_button.setCursor(Qt.PointingHandCursor)

        # Apply the drop shadow effect to the button
        self.join_button.setGraphicsEffect(shadow)

        # Add the "Join Room" button to the horizontal layout
        button_h_layout.addWidget(self.join_button, alignment=Qt.AlignCenter)

        # Set the same width for both buttons
        self.join_button.setFixedWidth(250)

        # Add the horizontal layout to the main button layout
        start_layout.addLayout(button_h_layout)

        # Create the waiting room screen
        self.waiting_room = QWidget()
        waiting_layout = QVBoxLayout(self.waiting_room)

         # Add a title label to the waiting room
        self.waiting_title_label = QLabel("Waiting Room")
        self.waiting_title_label.setAlignment(Qt.AlignCenter)
        waiting_title_font = QFont("Poppins", 20, QFont.Bold)  # Set the font size to 20
        self.waiting_title_label.setFont(waiting_title_font)
        waiting_layout.addWidget(self.waiting_title_label)

         # Add a list label to the waiting room
        self.waiting_list_label = QLabel("user")
        self.waiting_list_label.setAlignment(Qt.AlignCenter)
        waiting_list_font = QFont("Poppins", 16)  # Set the font size to 16
        self.waiting_list_label.setFont(waiting_list_font)
        waiting_layout.addWidget(self.waiting_list_label)

        # Create the "Start" button
        self.start_button = QPushButton("Start", self.waiting_room)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;  /* Blue color */
                color: white;
                border-radius: 15px;  /* Rounded corners */
                padding: 20px 40px;   /* Larger padding */
                font-size: 16pt;      /* Larger font size */
                font-family: 'Poppins ExtraBold';
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;  /* Darker blue when hovered */
                cursor: pointer;
            }
        """)
        self.start_button.setCursor(Qt.PointingHandCursor)
        waiting_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        # Install event filter on the waiting room
        self.waiting_room.installEventFilter(self)

        # Create the web view screen
        self.web_view_screen = QWidget()
        web_view_layout = QVBoxLayout(self.web_view_screen)

        # Create a QWidget at the top of the web view screen
        self.top_label = QWidget(self.web_view_screen)  # Use QWidget instead of QLabel
        self.top_label_layout = QHBoxLayout(self.top_label)
        self.top_label_layout.setContentsMargins(0, 20, 0, 0)  # Add margin-bottom

        # Create labels for left, center, and right text
        self.left_label = QLabel("Clicks: 0")
        self.left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        left_font = QFont("Poppins", 16)
        self.left_label.setFont(left_font)
        self.left_label.setStyleSheet("color: #2159ff;")

        self.center_label = QLabel("")
        self.center_label.setAlignment(Qt.AlignCenter)
        center_font = QFont("Poppins", 18, QFont.Bold)  # Set font weight to bold
        self.center_label.setFont(center_font)
        self.center_label.setStyleSheet("color: #2159ff;")

        self.right_label = QLabel("00:00")
        self.right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        right_font = QFont("Poppins", 16)
        self.right_label.setFont(right_font)
        self.right_label.setStyleSheet("color: #2159ff;")

        # Add labels to the layout
        self.top_label_layout.addWidget(self.left_label)
        self.top_label_layout.addWidget(self.center_label)
        self.top_label_layout.addWidget(self.right_label)

        self.top_label.setFixedHeight(80)  # Set a fixed height for the top label
        web_view_layout.addWidget(self.top_label)  # Add the top label to the web view layout

        self.bottom_label = QLabel("")
        self.bottom_label.setWordWrap(True)
        self.bottom_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.bottom_label.setFixedHeight(80)
        web_view_layout.addWidget(self.bottom_label)

        # Use the custom WebEngineView class
        self.web_view = QWebEngineView()
        web_view_layout.addWidget(self.web_view)
        self.web_view.urlChanged.connect(self.on_url_changed)

        # Add screens to the QStackedWidget
        self.addWidget(self.start_screen)
        self.addWidget(self.waiting_room)
        self.addWidget(self.web_view_screen)

        # Set the font for the whole window
        poppins_font = QFont("Poppins", 12)
        self.setFont(poppins_font)

        # Connect the buttons to switch screens
        self.join_button.clicked.connect(self.show_waiting_room)
        self.start_button.clicked.connect(self.show_web_view_helper)

        self.victory_screen_widget = QWidget()
        self.victory_layout = QVBoxLayout(self.victory_screen_widget)

        # Create a congratulatory message
        self.congratulations_label = QLabel("")
        self.congratulations_label.setAlignment(Qt.AlignCenter)
        self.congratulations_label.setStyleSheet("font-size: 24pt; color: black;")
        self.congratulations_label.setWordWrap(True)  # Enable word wrapping
        self.congratulations_label.setMaximumWidth(600)  # Set a maximum width for the label
        self.victory_layout.addWidget(self.congratulations_label, alignment=Qt.AlignCenter)  # Center the label in the layout

        # Add the victory screen to the stacked widget
        self.addWidget(self.victory_screen_widget)

        self.update_timer_signal.connect(self.update_timer_display)

        self.losing_screen_widget = QWidget()
        self.losing_layout = QVBoxLayout(self.losing_screen_widget)

        # Create and add the losing label
        self.losing_label = QLabel("You lose!")
        self.losing_label.setAlignment(Qt.AlignCenter)
        self.losing_label.setStyleSheet("color: #cf0a0a; font-size: 48pt; font-family: Poppins ExtraBold;")
        self.losing_layout.addWidget(self.losing_label, alignment=Qt.AlignCenter)

        # Create and add the sad GIF
        self.sad_gif_label = QLabel(self.losing_screen_widget)
        self.sad_gif_label.setAlignment(Qt.AlignCenter)
        sad_movie = QMovie("sad.gif")  # Update this with the path to your GIF file

        # Set the desired size for the sad GIF
        desired_size = QSize(500, 500)  # Adjust the width and height as needed
        sad_movie.setScaledSize(desired_size)

        self.sad_gif_label.setMovie(sad_movie)
        sad_movie.start()

        # Add the sad GIF label to the layout and align it to the bottom center
        self.losing_layout.addWidget(self.sad_gif_label, alignment=Qt.AlignBottom | Qt.AlignCenter)

        self.losing_layout.setContentsMargins(0, 0, 0, 50)

        # Add the losing screen to the stacked widget
        self.addWidget(self.losing_screen_widget)

    def eventFilter(self, obj, event):
            if obj == self.waiting_room and event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    self.start_button.click()
                    return True
            return super(Window, self).eventFilter(obj, event)

    def show_waiting_room(self):
        # Create a TCP socket
        self.socket = QTcpSocket(self)
        # Connect signals
        self.socket.readyRead.connect(self.read_data)
        self.socket.errorOccurred.connect(self.socket_error)
        # Connect to server
        self.connect_to_server()
        username = self.username_input.text()
        message = json.dumps({"command": "Join", "username": username, "winner": "", "time": "", num_clicks: 0})
        self.send_message(message)
        self.setCurrentWidget(self.waiting_room)
   
    def connect_to_server(self):
        self.socket.connectToHost(SERVER_IP, SERVER_PORT)

        if not self.socket.waitForConnected(3000):  # 3 seconds timeout
            print("Error: Could not connect to server.")
        else:
            print("Connected to server.")

    def send_message(self, message: str):
        if self.socket.state() == QAbstractSocket.ConnectedState:
            self.socket.write(message.encode())
            self.socket.flush()
            print(f"Sent: {message}")
        else:
            print("Not connected to the server.")

    def read_data(self):
        print("called")
        # This is called when data is available to read from the server
        while self.socket.bytesAvailable():
            data = self.socket.readAll()
            if data:
               data = json.loads(data.data().decode())
               print(data)
               if data["command"] == "Player Joined":
                  self.waiting_list_label.setText("<br>".join(dict(data["usernames"]).values()))
               elif data["command"] == "Start Game":
                  self.initialize_from_server(data)
               elif data["command"] == "Game Over":
                   global winner
                   global winner_time_taken
                   global winner_num_clicks
                   global game_over_message
                   winner = data["winner"]
                   winner_time_taken = data["time"]
                   winner_num_clicks = data["num_clicks"]
                   if (self.username_input.text() == winner):
                       game_over_message = '<span style = "color: #008000; font-size: 64px;"><b>Congratulations!</b></span>'
                       # Create a widget to hold the two GIFs
                       self.gif_widget = QWidget(self.victory_screen_widget)
                       gif_layout = QHBoxLayout(self.gif_widget)
                       # Add the first GIF
                       self.congratulations_gif_left = QLabel(self.gif_widget)
                       self.congratulations_gif_left.setAlignment(Qt.AlignCenter)
                       movie_left = QMovie("congrats.gif")  # Update this with the path to your GIF file
                       # Set the desired size for the left GIF
                       desired_size_left = QSize(400, 400)  # Adjust the width and height as needed
                       movie_left.setScaledSize(desired_size_left)
                       self.congratulations_gif_left.setMovie(movie_left)
                       movie_left.start()
                       # Add the left GIF label to the layout
                       gif_layout.addWidget(self.congratulations_gif_left)
                       # Add the second GIF
                       self.congratulations_gif_right = QLabel(self.gif_widget)
                       self.congratulations_gif_right.setAlignment(Qt.AlignCenter)
                       movie_right = QMovie("congrats_flipped.gif")  # Update this with the path to your GIF file
                       # Set the desired size for the right GIF
                       desired_size_right = QSize(400, 400)  # Adjust the width and height as needed
                       movie_right.setScaledSize(desired_size_right)
                       self.congratulations_gif_right.setMovie(movie_right)
                       movie_right.start()
                       # Add the right GIF label to the layout
                       gif_layout.addWidget(self.congratulations_gif_right)
                       # Add the GIF widget to the main layout and align it to the bottom center
                       self.victory_layout.addWidget(self.gif_widget, alignment=Qt.AlignBottom | Qt.AlignCenter)
                   else:
                       game_over_message = '<span style = "color: #FF0000; font-size: 64px;"><b>You Lose!</b></span>'
                       # Create a widget to hold the two GIFs
                       self.gif_widget = QWidget(self.victory_screen_widget)
                       gif_layout = QHBoxLayout(self.gif_widget)
                       # Add the first GIF
                       self.congratulations_gif_left = QLabel(self.gif_widget)
                       self.congratulations_gif_left.setAlignment(Qt.AlignCenter)
                       movie_left = QMovie("sad.gif")  # Update this with the path to your GIF file
                       # Set the desired size for the left GIF
                       desired_size_left = QSize(400, 400)  # Adjust the width and height as needed
                       movie_left.setScaledSize(desired_size_left)
                       self.congratulations_gif_left.setMovie(movie_left)
                       movie_left.start()
                       # Add the left GIF label to the layout
                       gif_layout.addWidget(self.congratulations_gif_left)
                       # Add the GIF widget to the main layout and align it to the bottom center
                       self.victory_layout.addWidget(self.gif_widget, alignment=Qt.AlignBottom | Qt.AlignCenter)
                   self.victory_screen()

    def socket_error(self):
        # Handle socket error
        print(f"Socket error: {self.socket.errorString()}")

    def initialize_from_server(self, data):
        global start_url
        global end_url
        global end_title
        start_url = data["start_url"]
        end_url = data["end_url"]
        end_title = data["end_title"]
        self.show_web_view()

    def show_web_view_helper(self):
        self.socket.readyRead.connect(self.read_data)
        message = json.dumps({"command": "Start", "username": "", "winner": "", "time": "", num_clicks: 0})
        self.send_message(message)

    def show_web_view(self):
        # Switch to the web view screen
        self.web_view.setUrl(QUrl(start_url))
        self.center_label.setText('<span style = "color: #6666ff">Target page:⠀</span>'+f'<span style = "color: #3399ff">{end_title}</span>')
        self.bottom_label.setText(page_summary())
        global start_time, end_time, timer
        start_time = time.time()
        # 300 seconds for 5 minutes of game time for now
        end_time = int(start_time) + timer

        # Maximize the window when showing the web view
        self.timing_thread = threading.Thread(target=self.timer)
        self.timing_thread.daemon = True
        self.timing_thread.start()

        self.setCurrentWidget(self.web_view_screen)
        self.showNormal()
        self.showMaximized()

    def victory_screen(self):
        # Switch to the victory screen widget
        self.setCurrentWidget(self.victory_screen_widget)
        self.showMaximized()
        self.congratulations_label.setText(f'{game_over_message} <br><br>It took {winner} <span style="color: #2159ff"><b>{winner_num_clicks}</b></span> clicks in <span style="color: #2159ff"><b>{winner_time_taken}</b></span> to reach the <span style="color: #2159ff"><b>{end_title}</b></span> page')

    def losing_screen(self):
        # Switch to the losing screen widget
        self.setCurrentWidget(self.losing_screen_widget)
        self.showMaximized()
        self.losing_layout.setContentsMargins(0, 0, 0, 500)

    def on_url_changed(self, url):
         global num_clicks
         num_clicks += 1
         self.left_label.setText(f"Clicks: {str(num_clicks)}")
         if url.url() == end_url:
               global time_taken
               time_taken = self.right_label.text()
               message = json.dumps({"command": "Game Over", "username": "", "winner": self.username_input.text(), "time": time_taken, "num_clicks": num_clicks})
               self.send_message(message)
         elif end_time != 0 and time.time() >= end_time:
               self.losing_screen()

    def timer(self):
        start_time = time.time()  # Record the start time

        while True:
            time_elapsed = time.time() - start_time  # Calculate elapsed time
            minutes = int(time_elapsed // 60)  # Get the total minutes
            seconds = int(time_elapsed % 60)  # Get the remaining seconds
            formatted_time = f"{minutes:02}:{seconds:02}"  # Format as MM:SS
            self.update_timer_signal.emit(formatted_time)
            time.sleep(1)

    def update_timer_display(self, time_string):
        # Split the string on ':'
        minutes, seconds = map(int, time_string.split(':'))

        # Convert to total seconds
        total_seconds = minutes * 60 + seconds
        percent_elapsed = int(total_seconds * 100 / timer)
        red = int(min(int(percent_elapsed * 2.56), 255))
        green = int(max(int((100 - percent_elapsed) * 2.56), 0))
        color_string = f'rgb({max(0, min(red, 255))}, {max(0, min(green, 255))}, 0)'
        self.right_label.setText(f'<span style="color: {color_string}">{time_string}</span>')

def page_summary():
    wiki_wiki = wikipediaapi.Wikipedia('wikigame','en')
    tester = wiki_wiki.page(end_title)
    summary = tester.summary[0:300]
    # Truncate the summary at the last period
    last_period_index = summary.rfind('.')

    if last_period_index != -1:
        truncated_summary = summary[:last_period_index + 1]  # Include the last period
    else:
        truncated_summary = summary  # If no period, keep the whole text
    return truncated_summary

def main():
    app = QApplication(sys.argv)

    # Get the current working directory and build the full path to the fonts
    font_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
    regular_font_path = os.path.join(font_dir, "Poppins-Regular.ttf")
    bold_font_path = os.path.join(font_dir, "Poppins-ExtraBold.ttf")

    # Load the Poppins Regular font
    poppins_regular_id = QFontDatabase.addApplicationFont("Poppins-Regular.ttf")
    if poppins_regular_id == -1:
        print(f"Failed to load Poppins Regular font from {regular_font_path}.")
        poppins_regular_id = QFontDatabase.addApplicationFont(regular_font_path)
    else:
        print("Poppins Regular font loaded successfully.")

    # Load the Poppins Bold font
    poppins_bold_id = QFontDatabase.addApplicationFont("Poppins-ExtraBold.ttf")
    if poppins_bold_id == -1:
        print(f"Failed to load Poppins Bold font from {bold_font_path}.")
        poppins_bold_id = QFontDatabase.addApplicationFont(bold_font_path)
    else:
        print("Poppins Bold font loaded successfully.")

    # Ensure that at least one font family is available
    if poppins_regular_id != -1:
        poppins_families = QFontDatabase.applicationFontFamilies(poppins_regular_id)
        if poppins_families:
            poppins_family = poppins_families[0]
            app.setFont(QFont(poppins_family, 12))
        else:
            print("No font families available for Poppins Regular.")
    else:
        print("Skipping setting global font as Poppins Regular failed to load.")

    window = Window()
    window.show()
    os._exit(app.exec_())

if __name__ == "__main__":
    main()