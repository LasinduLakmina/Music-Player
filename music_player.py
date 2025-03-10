import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
                            QHBoxLayout, QListWidget, QLabel, QFileDialog, QSlider, QStyle,
                            QListWidgetItem)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QPalette, QColor
from mutagen import File
import os

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player")
        self.setMinimumSize(1000, 700)
        self.current_theme = "light"
        self.apply_theme()

    def apply_theme(self):
        light_theme = """
            QMainWindow { background-color: #f5f5f5; color: #333333; }
            QLabel { color: #333333; font-size: 14px; }
            QPushButton {
                background-color: #4a90e2;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover { background-color: #357abd; }
            QListWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 14px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4a90e2;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                border: 1px solid #e0e0e0;
                height: 8px;
                background: #f0f0f0;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a90e2;
                border: none;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """

        dark_theme = """
            QMainWindow { background-color: #1e1e1e; color: #ffffff; }
            QLabel { color: #ffffff; font-size: 14px; }
            QPushButton {
                background-color: #4a90e2;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover { background-color: #357abd; }
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-size: 14px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4a90e2;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3d3d3d;
                height: 8px;
                background: #2d2d2d;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a90e2;
                border: none;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """

        self.setStyleSheet(light_theme if self.current_theme == "light" else dark_theme)
        
        # Initialize media player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create metadata display
        self.metadata_label = QLabel("No track selected")
        self.metadata_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.metadata_label)
        
        # Create progress bar
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderMoved.connect(self.set_position)
        layout.addWidget(self.progress_slider)
        
        # Create time labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.duration_label = QLabel("0:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        layout.addLayout(time_layout)
        
        # Create playlist widget
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.playlist_widget)
        
        # Create control buttons
        # Create control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        # Theme toggle button
        self.theme_button = QPushButton("🌙 Dark" if self.current_theme == "light" else "☀️ Light")
        self.theme_button.clicked.connect(self.toggle_theme)
        controls_layout.addWidget(self.theme_button)
        
        controls_layout.addStretch()
        
        self.prev_button = QPushButton()
        self.prev_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.prev_button.clicked.connect(self.play_previous)
        controls_layout.addWidget(self.prev_button)
        
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        self.next_button = QPushButton()
        self.next_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.next_button.clicked.connect(self.play_next)
        controls_layout.addWidget(self.next_button)
        
        controls_layout.addStretch()
        
        # Volume control with icon
        volume_layout = QHBoxLayout()
        volume_icon = QLabel("🔊")
        volume_layout.addWidget(volume_icon)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)
        controls_layout.addLayout(volume_layout)
        
        self.add_button = QPushButton("Add Files")
        self.add_button.clicked.connect(self.add_files)
        controls_layout.addWidget(self.add_button)
        
        layout.addLayout(controls_layout)
        
        # Initialize playlist
        self.playlist = []
        self.current_index = -1
        
        # Connect media player signals
        self.player.playbackStateChanged.connect(self.update_play_button)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update_position)
        self.update_timer.start()
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add Music Files", "", "Audio Files (*.mp3 *.wav *.ogg *.m4a)")
        for file_path in files:
            self.playlist.append(file_path)
            file_name = os.path.basename(file_path)
            self.playlist_widget.addItem(file_name)
            
    def play_selected(self, item):
        self.current_index = self.playlist_widget.row(item)
        self.play_current()
        
    def play_current(self):
        if 0 <= self.current_index < len(self.playlist):
            current_file = self.playlist[self.current_index]
            self.player.setSource(QUrl.fromLocalFile(current_file))
            self.player.play()
            self.update_metadata(current_file)
            
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme_button.setText("🌙 Dark" if self.current_theme == "light" else "☀️ Light")
        self.apply_theme()

    def update_metadata(self, file_path):
        audio = File(file_path)
        if audio is not None:
            if hasattr(audio, 'tags'):
                title = audio.tags.get('title', [os.path.basename(file_path)])[0]
                artist = audio.tags.get('artist', ['Unknown Artist'])[0]
                album = audio.tags.get('album', ['Unknown Album'])[0]
                metadata_text = f"🎵 {title}\n👤 {artist}\n💿 {album}"
            else:
                metadata_text = f"🎵 {os.path.basename(file_path)}"
            
            # Highlight the current playing track in the playlist
            for i in range(self.playlist_widget.count()):
                item = self.playlist_widget.item(i)
                if i == self.current_index:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                else:
                    font = item.font()
                    font.setBold(False)
                    item.setFont(font)
            
            self.metadata_label.setText(metadata_text)
                
    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            if self.current_index == -1 and self.playlist_widget.count() > 0:
                self.current_index = 0
                self.play_current()
            else:
                self.player.play()
                
    def play_previous(self):
        if len(self.playlist) > 0:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_current()
            
    def play_next(self):
        if len(self.playlist) > 0:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_current()
            
    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)
    
    def set_position(self, position):
        self.player.setPosition(position)
    
    def position_changed(self, position):
        self.progress_slider.setValue(position)
        self.update_time_label(position, self.current_time_label)
    
    def duration_changed(self, duration):
        self.progress_slider.setRange(0, duration)
        self.update_time_label(duration, self.duration_label)
        self.progress_slider.setEnabled(True)
    
    def update_position(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.position_changed(self.player.position())
    
    def update_time_label(self, ms, label):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        label.setText(f"{minutes}:{seconds:02d}")
    
    def update_play_button(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

def main():
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()