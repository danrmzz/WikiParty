import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QMovie
import threading
import time
import os
import wikipediaapi
import threading
import json
from PyQt5.QtNetwork import QTcpSocket, QAbstractSocket

# Server info
SERVER_IP = "34.171.41.219"
SERVER_PORT = 3389

# Server stats tracking
start_url = ""
end_url = ""
end_title = ""
winner = ""
game_over_message = ""
winner_num_clicks = 0
winner_time_taken = ""

# Local stats tracking
num_clicks = -1
start_time = 0
end_time = 0
timer = 300
time_taken = 0

# Defining GUI
class Window(QStackedWidget):
    update_timer_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        # Setup window title and initial size
        super(Window, self).__init__(parent)
        self.setWindowTitle("WikiParty")
        self.resize(800, 650)

        # Set default font
        poppins_font = QFont("Poppins", 12)
        self.setFont(poppins_font)

        # Connects GUI to asynchronous timer thread
        self.update_timer_signal.connect(self.update_timer_display)

        # Create the start screen
        self.start_screen = QWidget()
        start_layout = QVBoxLayout(self.start_screen)
        start_layout.setContentsMargins(40, 40, 40, 40)
        start_layout.setSpacing(10)
        self.image_label = QLabel(self.start_screen)
        pixmap = QPixmap("wikiparty_logo.png")
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(400, 300, Qt.KeepAspectRatio))
            self.image_label.setAlignment(Qt.AlignCenter)
            start_layout.addWidget(self.image_label)
        self.start_label = QLabel("Welcome to <b>WikiParty</b>! You are given a random Wikipedia page with the goal of reaching a destination page using only the hyperlinks present on each page. <br>You have <b>5 minutes</b> to get there!<br><br> Enter your username:")
        self.start_label.setAlignment(Qt.AlignCenter)
        self.start_label.setWordWrap(True)
        start_layout.addWidget(self.start_label)
        self.username_input = QLineEdit(self.start_screen)
        self.username_input.setAlignment(Qt.AlignCenter)
        start_layout.addWidget(self.username_input)
        self.username_input.clearFocus()
        self.start_screen.setFocus()
        self.username_input.returnPressed.connect(self.show_waiting_room)
        button_h_layout = QHBoxLayout()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(Qt.gray)
        self.join_button = QPushButton("Join", self.start_screen)
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
        self.join_button.setGraphicsEffect(shadow)
        button_h_layout.addWidget(self.join_button, alignment=Qt.AlignCenter)
        self.join_button.setFixedWidth(250)
        self.join_button.clicked.connect(self.show_waiting_room)
        start_layout.addLayout(button_h_layout)

        # Create the waiting room screen
        self.waiting_room = QWidget()
        waiting_layout = QVBoxLayout(self.waiting_room)
        self.waiting_title_label = QLabel("Waiting Room")
        self.waiting_title_label.setAlignment(Qt.AlignCenter)
        waiting_title_font = QFont("Poppins", 20, QFont.Bold)
        self.waiting_title_label.setFont(waiting_title_font)
        waiting_layout.addWidget(self.waiting_title_label)
        self.waiting_list_label = QLabel("user")
        self.waiting_list_label.setAlignment(Qt.AlignCenter)
        waiting_list_font = QFont("Poppins", 16)
        self.waiting_list_label.setFont(waiting_list_font)
        waiting_layout.addWidget(self.waiting_list_label)
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
        self.start_button.clicked.connect(self.show_web_view_helper)
        self.waiting_room.installEventFilter(self)

        # Create the main game screen
        self.web_view_screen = QWidget()
        web_view_layout = QVBoxLayout(self.web_view_screen)
        self.top_label = QWidget(self.web_view_screen)
        self.top_label_layout = QHBoxLayout(self.top_label)
        self.top_label_layout.setContentsMargins(0, 20, 0, 0)
        self.left_label = QLabel("Clicks: 0")
        self.left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        left_font = QFont("Poppins", 16)
        self.left_label.setFont(left_font)
        self.left_label.setStyleSheet("color: #2159ff;")
        self.center_label = QLabel("")
        self.center_label.setAlignment(Qt.AlignCenter)
        center_font = QFont("Poppins", 18, QFont.Bold)
        self.center_label.setFont(center_font)
        self.center_label.setStyleSheet("color: #2159ff;")
        self.right_label = QLabel("00:00")
        self.right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        right_font = QFont("Poppins", 16)
        self.right_label.setFont(right_font)
        self.right_label.setStyleSheet("color: #2159ff;")
        self.top_label_layout.addWidget(self.left_label)
        self.top_label_layout.addWidget(self.center_label)
        self.top_label_layout.addWidget(self.right_label)
        self.top_label.setFixedHeight(80)
        web_view_layout.addWidget(self.top_label)
        self.bottom_label = QLabel("")
        self.bottom_label.setWordWrap(True)
        self.bottom_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.bottom_label.setFixedHeight(80)
        web_view_layout.addWidget(self.bottom_label)
        self.web_view = QWebEngineView()
        web_view_layout.addWidget(self.web_view)
        self.web_view.urlChanged.connect(self.on_url_changed)

        # Create victory screen
        self.victory_screen_widget = QWidget()
        self.victory_layout = QVBoxLayout(self.victory_screen_widget)
        self.congratulations_label = QLabel("")
        self.congratulations_label.setAlignment(Qt.AlignCenter)
        self.congratulations_label.setStyleSheet("font-size: 24pt; color: black;")
        self.congratulations_label.setWordWrap(True)
        self.congratulations_label.setMaximumWidth(600)
        self.victory_layout.addWidget(self.congratulations_label, alignment=Qt.AlignCenter)
        
        # Create losing screen
        self.losing_screen_widget = QWidget()
        self.losing_layout = QVBoxLayout(self.losing_screen_widget)
        self.losing_label = QLabel("You lose!")
        self.losing_label.setAlignment(Qt.AlignCenter)
        self.losing_label.setStyleSheet("color: #cf0a0a; font-size: 48pt; font-family: Poppins ExtraBold;")
        self.losing_layout.addWidget(self.losing_label, alignment=Qt.AlignCenter)
        self.sad_gif_label = QLabel(self.losing_screen_widget)
        self.sad_gif_label.setAlignment(Qt.AlignCenter)
        sad_movie = QMovie("sad.gif")
        desired_size = QSize(500, 500)
        sad_movie.setScaledSize(desired_size)
        self.sad_gif_label.setMovie(sad_movie)
        sad_movie.start()
        self.losing_layout.addWidget(self.sad_gif_label, alignment=Qt.AlignBottom | Qt.AlignCenter)
        self.losing_layout.setContentsMargins(0, 0, 0, 50)

        # Add all screens to GUI
        self.addWidget(self.start_screen)
        self.addWidget(self.waiting_room)
        self.addWidget(self.web_view_screen)
        self.addWidget(self.victory_screen_widget)
        self.addWidget(self.losing_screen_widget)

    # Properly handle pressing Enter key event
    def eventFilter(self, obj, event):
            if obj == self.waiting_room and event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    self.start_button.click()
                    return True
            return super(Window, self).eventFilter(obj, event)
   
    # Connects to server
    def connect_to_server(self):
        self.socket.connectToHost(SERVER_IP, SERVER_PORT)
        if not self.socket.waitForConnected(3000):
            print("Error: Could not connect to server.")
    
    # Handles server connection issue
    def socket_error(self):
        print(f"Socket error: {self.socket.errorString()}")

    # Send message to server
    def send_message(self, message: str):
        if self.socket.state() == QAbstractSocket.ConnectedState:
            self.socket.write(message.encode())
            self.socket.flush()

    # Read message from server and update data accordingly
    def read_data(self):
        while self.socket.bytesAvailable():
            data = self.socket.readAll()
            if data:
               data = json.loads(data.data().decode())
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
                       self.gif_widget = QWidget(self.victory_screen_widget)
                       gif_layout = QHBoxLayout(self.gif_widget)
                       self.congratulations_gif_left = QLabel(self.gif_widget)
                       self.congratulations_gif_left.setAlignment(Qt.AlignCenter)
                       movie_left = QMovie("congrats.gif")
                       desired_size_left = QSize(400, 400)
                       movie_left.setScaledSize(desired_size_left)
                       self.congratulations_gif_left.setMovie(movie_left)
                       movie_left.start()
                       gif_layout.addWidget(self.congratulations_gif_left)
                       self.congratulations_gif_right = QLabel(self.gif_widget)
                       self.congratulations_gif_right.setAlignment(Qt.AlignCenter)
                       movie_right = QMovie("congrats_flipped.gif")
                       desired_size_right = QSize(400, 400)
                       movie_right.setScaledSize(desired_size_right)
                       self.congratulations_gif_right.setMovie(movie_right)
                       movie_right.start()
                       gif_layout.addWidget(self.congratulations_gif_right)
                       self.victory_layout.addWidget(self.gif_widget, alignment=Qt.AlignBottom | Qt.AlignCenter)
                   else:
                       game_over_message = '<span style = "color: #FF0000; font-size: 64px;"><b>You Lose!</b></span>'
                       self.gif_widget = QWidget(self.victory_screen_widget)
                       gif_layout = QHBoxLayout(self.gif_widget)
                       self.congratulations_gif_left = QLabel(self.gif_widget)
                       self.congratulations_gif_left.setAlignment(Qt.AlignCenter)
                       movie_left = QMovie("sad.gif")
                       desired_size_left = QSize(400, 400)
                       movie_left.setScaledSize(desired_size_left)
                       self.congratulations_gif_left.setMovie(movie_left)
                       movie_left.start()
                       gif_layout.addWidget(self.congratulations_gif_left)
                       self.victory_layout.addWidget(self.gif_widget, alignment=Qt.AlignBottom | Qt.AlignCenter)
                   self.victory_screen()

    # Intialize main game screen data from server
    def initialize_from_server(self, data):
        global start_url
        global end_url
        global end_title
        start_url = data["start_url"]
        end_url = data["end_url"]
        end_title = data["end_title"]
        self.show_web_view()
    
    # Switch to waiting room screen
    def show_waiting_room(self):
        self.socket = QTcpSocket(self)
        self.socket.readyRead.connect(self.read_data)
        self.socket.errorOccurred.connect(self.socket_error)
        self.connect_to_server()
        username = self.username_input.text()
        message = json.dumps({"command": "Join", "username": username, "winner": "", "time": "", num_clicks: 0})
        self.send_message(message)
        self.setCurrentWidget(self.waiting_room)
    
    # Preload data for main game screen
    def show_web_view_helper(self):
        self.socket.readyRead.connect(self.read_data)
        message = json.dumps({"command": "Start", "username": "", "winner": "", "time": "", num_clicks: 0})
        self.send_message(message)

    # Switch to main game screen
    def show_web_view(self):
        self.web_view.setUrl(QUrl(start_url))
        self.center_label.setText('<span style = "color: #6666ff">Target page:⠀</span>'+f'<span style = "color: #3399ff">{end_title}</span>')
        self.bottom_label.setText(self.page_summary())
        global start_time, end_time, timer
        start_time = time.time()
        end_time = int(start_time) + timer
        self.timing_thread = threading.Thread(target=self.timer)
        self.timing_thread.daemon = True
        self.timing_thread.start()
        self.setCurrentWidget(self.web_view_screen)
        self.showNormal()
        self.showMaximized()

    # Switch to the victory screen
    def victory_screen(self):
        self.setCurrentWidget(self.victory_screen_widget)
        self.showMaximized()
        self.congratulations_label.setText(f'{game_over_message} <br><br>It took {winner} <span style="color: #2159ff"><b>{winner_num_clicks}</b></span> clicks in <span style="color: #2159ff"><b>{winner_time_taken}</b></span> to reach the <span style="color: #2159ff"><b>{end_title}</b></span> page')

    # Switch to the losing screen
    def losing_screen(self):
        self.setCurrentWidget(self.losing_screen_widget)
        self.showMaximized()
        self.losing_layout.setContentsMargins(0, 0, 0, 500)

    # Handle when new link is clicked
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

    # Background timer thread
    def timer(self):
        start_time = time.time()
        while True:
            time_elapsed = time.time() - start_time
            minutes = int(time_elapsed // 60)
            seconds = int(time_elapsed % 60)
            formatted_time = f"{minutes:02}:{seconds:02}"
            self.update_timer_signal.emit(formatted_time)
            time.sleep(1)

    # Updates time displayed to user
    def update_timer_display(self, time_string):
        minutes, seconds = map(int, time_string.split(':'))
        total_seconds = minutes * 60 + seconds
        percent_elapsed = int(total_seconds * 100 / timer)
        red = int(min(int(percent_elapsed * 2.56), 255))
        green = int(max(int((100 - percent_elapsed) * 2.56), 0))
        color_string = f'rgb({max(0, min(red, 255))}, {max(0, min(green, 255))}, 0)'
        self.right_label.setText(f'<span style="color: {color_string}">{time_string}</span>')

    # Returns short summary of desired Wikipedia page
    def page_summary(self):
        wiki_wiki = wikipediaapi.Wikipedia('wikigame','en')
        tester = wiki_wiki.page(end_title)
        summary = tester.summary[0:300]
        last_period_index = summary.rfind('.')
        if last_period_index != -1:
            truncated_summary = summary[:last_period_index + 1]
        else:
            truncated_summary = summary
        return truncated_summary

# Get Poppins fonts to apply to GUI
def get_fonts(app):
    font_dir = os.path.dirname(os.path.abspath(__file__))
    regular_font_path = os.path.join(font_dir, "Poppins-Regular.ttf")
    bold_font_path = os.path.join(font_dir, "Poppins-ExtraBold.ttf")
    poppins_regular_id = QFontDatabase.addApplicationFont("Poppins-Regular.ttf")
    if poppins_regular_id == -1:
        poppins_regular_id = QFontDatabase.addApplicationFont(regular_font_path)
    poppins_bold_id = QFontDatabase.addApplicationFont("Poppins-ExtraBold.ttf")
    if poppins_bold_id == -1:
        poppins_bold_id = QFontDatabase.addApplicationFont(bold_font_path)
    if poppins_regular_id != -1:
        poppins_families = QFontDatabase.applicationFontFamilies(poppins_regular_id)
        if poppins_families:
            poppins_family = poppins_families[0]
            app.setFont(QFont(poppins_family, 12))

# Run app
def main():
    app = QApplication(sys.argv)
    get_fonts(app)
    window = Window()
    window.show()
    os._exit(app.exec_())

main()
