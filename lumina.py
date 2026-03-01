

import sys
import os
import json
import time
import requests
import psutil
from datetime import datetime
from dotenv import load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSystemTrayIcon, QMenu,
    QGridLayout, QScrollArea, QSizePolicy, QDesktopWidget
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPainter, QColor, QBrush, QPen, QLinearGradient, QFontDatabase

# Load environment variables
load_dotenv()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_weather():
    """Fetch weather data from OpenWeatherMap"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    city = os.getenv('CITY', 'London')
    units = os.getenv('UNITS', 'metric')
    
    if not api_key:
        return {"error": "No API key"}
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units={units}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            return {
                "temp": round(data['main']['temp']),
                "feels_like": round(data['main']['feels_like']),
                "humidity": data['main']['humidity'],
                "description": data['weather'][0]['description'].capitalize(),
                "city": data['name'],
                "country": data['sys']['country'],
                "wind": round(data['wind']['speed'] * 3.6, 1),  # Convert to km/h
                "pressure": data['main']['pressure'],
                "icon": data['weather'][0]['main'].lower()
            }
        else:
            return {"error": f"API Error: {data.get('message', 'Unknown')}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def get_news():
    """Fetch news headlines"""
    api_key = os.getenv('NEWS_API_KEY')
    
    if not api_key:
        return [{"title": "No API key configured", "source": "Please add NEWS_API_KEY to .env"}]
    
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data.get('articles'):
            articles = []
            for article in data['articles'][:5]:  # Top 5
                articles.append({
                    "title": article['title'],
                    "source": article['source']['name']
                })
            return articles
        else:
            return [{"title": "Unable to fetch news", "source": "Try again later"}]
    except Exception:
        return [{"title": "Network error", "source": "Check connection"}]

def get_quote():
    """Fetch inspirational quote"""
    try:
        url = "https://api.quotable.io/random"
        response = requests.get(url, timeout=5)
        data = response.json()
        return f"\"{data['content']}\"\n— {data['author']}"
    except:
        quotes = [
            "\"The only way to do great work is to love what you do.\"\n— Steve Jobs",
            "\"Innovation distinguishes between a leader and a follower.\"\n— Steve Jobs",
            "\"Stay hungry, stay foolish.\"\n— Steve Jobs",
            "\"Your time is limited, don't waste it living someone else's life.\"\n— Steve Jobs",
            "\"The future belongs to those who believe in the beauty of their dreams.\"\n— Eleanor Roosevelt"
        ]
        import random
        return random.choice(quotes)

def get_system_stats():
    """Get system resource usage"""
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get top processes
    processes = []
    for proc in sorted(psutil.process_iter(['name', 'cpu_percent']), 
                       key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:3]:
        try:
            if proc.info['cpu_percent'] and proc.info['cpu_percent'] > 1:
                processes.append(f"{proc.info['name'][:15]}: {proc.info['cpu_percent']:.1f}%")
        except:
            pass
    
    return {
        "cpu": cpu,
        "memory": memory.percent,
        "memory_used": memory.used / (1024**3),  # GB
        "memory_total": memory.total / (1024**3),  # GB
        "disk": disk.percent,
        "disk_free": disk.free / (1024**3),  # GB
        "disk_total": disk.total / (1024**3),  # GB
        "processes": processes[:3]
    }

# ============================================================================
# CUSTOM WIDGETS
# ============================================================================

class ModernFrame(QFrame):
    """Modern frame with hover effects"""
    def __init__(self, parent=None, gradient=True):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.hover = False
        self._opacity = 0.0
        
        # Style
        self.setMinimumHeight(120)
        self.setMaximumHeight(200)
        
    def enterEvent(self, event):
        self.hover = True
        self.update()
        
    def leaveEvent(self, event):
        self.hover = False
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        if self.hover:
            color = QColor(70, 70, 90, 200)
        else:
            color = QColor(45, 45, 55, 180)
            
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

class AnimatedValue(QLabel):
    """Label that animates when value changes"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self._scale = 1.0
        
    def setValue(self, value):
        self.setText(str(value))
        self.animate()
        
    def animate(self):
        self.anim = QPropertyAnimation(self, b'scale')
        self.anim.setDuration(300)
        self.anim.setStartValue(1.2)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutElastic)
        self.anim.start()
        
    def get_scale(self):
        return self._scale
        
    def set_scale(self, scale):
        self._scale = scale
        self.update()
        
    scale = pyqtProperty(float, get_scale, set_scale)

class ProgressRing(QFrame):
    """Custom progress ring widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(80, 80)
        self.setMaximumSize(80, 80)
        self.value = 0
        self.title = ""
        
    def setValue(self, value):
        self.value = value
        self.update()
        
    def setTitle(self, title):
        self.title = title
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        side = min(width, height)
        
        # Draw background circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(60, 60, 70)))
        painter.drawEllipse(5, 5, side-10, side-10)
        
        # Draw progress arc
        if self.value > 0:
            painter.setPen(QPen(QColor(100, 200, 255), 8, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            
            # Calculate angles (pyqt uses 1/16 of a degree)
            start_angle = 90 * 16  # Start from top
            span_angle = -int(360 * self.value / 100 * 16)  # Clockwise negative
            
            painter.drawArc(5, 5, side-10, side-10, start_angle, span_angle)
        
        # Draw text
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value}%")
        
        # Draw title
        if self.title:
            painter.setPen(QColor(180, 180, 200))
            font = QFont("Segoe UI", 8)
            painter.setFont(font)
            painter.drawText(self.rect().adjusted(0, 25, 0, 0), Qt.AlignCenter, self.title)

# ============================================================================
# MAIN WINDOW
# ============================================================================

class LuminaDashboard(QMainWindow):
    """Main dashboard window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lumina Dashboard")
        self.setMinimumSize(1200, 700)
        
        # Center window
        self.center_window()
        
        # Remove default window decorations for ultra-minimal look
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Data storage
        self.weather_data = {}
        self.news_data = []
        self.system_stats = {}
        
        # Setup UI
        self.setup_ui()
        self.setup_timers()
        self.setup_tray()
        
        # Initial data fetch
        self.refresh_all()
        
    def center_window(self):
        """Center window on screen"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def setup_ui(self):
        """Create the entire UI"""
        # Main widget with gradient background
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header (draggable area)
        self.setup_header(main_layout)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 8px; background: rgba(0,0,0,0.2); }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.3); border-radius: 4px; }
        """)
        
        # Content widget
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # Stats row (CPU, Memory, Disk)
        self.setup_stats_row(content_layout)
        
        # Weather and Quote row
        self.setup_weather_row(content_layout)
        
        # News section
        self.setup_news_section(content_layout)
        
        # System details
        self.setup_system_details(content_layout)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def setup_header(self, parent_layout):
        """Create draggable header"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background: transparent;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        # Title
        title = QLabel("LUMINA")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                letter-spacing: 4px;
            }
        """)
        title_font = QFont("Segoe UI", 24, QFont.Bold)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        # Date/Time
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 14px;")
        header_layout.addWidget(self.time_label)
        
        header_layout.addStretch()
        
        # Control buttons
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(35, 35)
        refresh_btn.setStyleSheet(self.get_button_style())
        refresh_btn.clicked.connect(self.refresh_all)
        header_layout.addWidget(refresh_btn)
        
        min_btn = QPushButton("—")
        min_btn.setFixedSize(35, 35)
        min_btn.setStyleSheet(self.get_button_style())
        min_btn.clicked.connect(self.showMinimized)
        header_layout.addWidget(min_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(35, 35)
        close_btn.setStyleSheet(self.get_button_style())
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        # Make header draggable
        header.mousePressEvent = self.mouse_press
        header.mouseMoveEvent = self.mouse_move
        
        parent_layout.addWidget(header)
        
    def get_button_style(self):
        return """
            QPushButton {
                background: rgba(255,255,255,0.1);
                color: white;
                border: none;
                border-radius: 17px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.2);
            }
            QPushButton:pressed {
                background: rgba(100,200,255,0.5);
            }
        """
        
    def setup_stats_row(self, parent_layout):
        """Create CPU, Memory, Disk rings"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setSpacing(30)
        
        # CPU
        cpu_widget = QWidget()
        cpu_layout = QVBoxLayout(cpu_widget)
        self.cpu_ring = ProgressRing()
        cpu_layout.addWidget(self.cpu_ring, 0, Qt.AlignCenter)
        cpu_label = QLabel("CPU")
        cpu_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        cpu_layout.addWidget(cpu_label, 0, Qt.AlignCenter)
        row_layout.addWidget(cpu_widget)
        
        # Memory
        mem_widget = QWidget()
        mem_layout = QVBoxLayout(mem_widget)
        self.mem_ring = ProgressRing()
        mem_layout.addWidget(self.mem_ring, 0, Qt.AlignCenter)
        mem_label = QLabel("Memory")
        mem_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        mem_layout.addWidget(mem_label, 0, Qt.AlignCenter)
        row_layout.addWidget(mem_widget)
        
        # Disk
        disk_widget = QWidget()
        disk_layout = QVBoxLayout(disk_widget)
        self.disk_ring = ProgressRing()
        disk_layout.addWidget(self.disk_ring, 0, Qt.AlignCenter)
        disk_label = QLabel("Disk")
        disk_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        disk_layout.addWidget(disk_label, 0, Qt.AlignCenter)
        row_layout.addWidget(disk_widget)
        
        parent_layout.addWidget(row)
        
    def setup_weather_row(self, parent_layout):
        """Create weather and quote widgets"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setSpacing(20)
        
        # Weather
        self.weather_frame = ModernFrame()
        weather_layout = QVBoxLayout(self.weather_frame)
        
        self.weather_city = QLabel("Loading...")
        self.weather_city.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        weather_layout.addWidget(self.weather_city)
        
        self.weather_temp = QLabel("—°C")
        self.weather_temp.setStyleSheet("color: white; font-size: 48px; font-weight: bold;")
        weather_layout.addWidget(self.weather_temp, 0, Qt.AlignCenter)
        
        weather_details = QWidget()
        details_layout = QHBoxLayout(weather_details)
        
        self.weather_humidity = QLabel("💧 —%")
        self.weather_humidity.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px;")
        details_layout.addWidget(self.weather_humidity)
        
        self.weather_wind = QLabel("🌪️ — km/h")
        self.weather_wind.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px;")
        details_layout.addWidget(self.weather_wind)
        
        weather_layout.addWidget(weather_details)
        row_layout.addWidget(self.weather_frame)
        
        # Quote
        self.quote_frame = ModernFrame()
        quote_layout = QVBoxLayout(self.quote_frame)
        
        self.quote_label = QLabel("Loading inspirational quote...")
        self.quote_label.setWordWrap(True)
        self.quote_label.setStyleSheet("color: white; font-size: 14px; font-style: italic; padding: 10px;")
        quote_layout.addWidget(self.quote_label)
        
        row_layout.addWidget(self.quote_frame)
        
        parent_layout.addWidget(row)
        
    def setup_news_section(self, parent_layout):
        """Create news headlines section"""
        self.news_frame = ModernFrame()
        news_layout = QVBoxLayout(self.news_frame)
        
        # News header
        news_header = QLabel("📰 Latest Headlines")
        news_header.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        news_layout.addWidget(news_header)
        
        # News container
        self.news_container = QWidget()
        self.news_container_layout = QVBoxLayout(self.news_container)
        self.news_container_layout.setSpacing(10)
        news_layout.addWidget(self.news_container)
        
        parent_layout.addWidget(self.news_frame)
        
    def setup_system_details(self, parent_layout):
        """Create system details section"""
        sys_frame = ModernFrame()
        sys_layout = QVBoxLayout(sys_frame)
        
        sys_header = QLabel("⚙️ System Activity")
        sys_header.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        sys_layout.addWidget(sys_header)
        
        self.processes_label = QLabel("Top processes: ")
        self.processes_label.setWordWrap(True)
        self.processes_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px;")
        sys_layout.addWidget(self.processes_label)
        
        self.disk_details = QLabel("")
        self.disk_details.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px;")
        sys_layout.addWidget(self.disk_details)
        
        parent_layout.addWidget(sys_frame)
        
    def setup_timers(self):
        """Setup update timers"""
        # Update clock every second
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()
        
        # Refresh data every 5 minutes
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(300000)  # 5 minutes
        
    def setup_tray(self):
        """Setup system tray"""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # Tray menu
        menu = QMenu()
        show_action = menu.addAction("Show Dashboard")
        show_action.triggered.connect(self.show)
        
        hide_action = menu.addAction("Hide to Tray")
        hide_action.triggered.connect(self.hide)
        
        menu.addSeparator()
        
        refresh_action = menu.addAction("Refresh Now")
        refresh_action.triggered.connect(self.refresh_all)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray.setContextMenu(menu)
        self.tray.show()
        
    def update_clock(self):
        """Update time display"""
        now = QDateTime.currentDateTime()
        self.time_label.setText(now.toString("dddd, MMMM d • hh:mm:ss AP"))
        
    def refresh_all(self):
        """Refresh all dashboard data"""
        # Weather
        self.weather_data = get_weather()
        self.update_weather()
        
        # News
        self.news_data = get_news()
        self.update_news()
        
        # Quote
        self.quote_label.setText(get_quote())
        
        # System stats
        self.system_stats = get_system_stats()
        self.update_system_stats()
        
    def update_weather(self):
        """Update weather display"""
        if 'error' in self.weather_data:
            self.weather_city.setText(self.weather_data['error'])
            self.weather_temp.setText("—")
        else:
            self.weather_city.setText(f"{self.weather_data['city']}, {self.weather_data['country']}")
            self.weather_temp.setText(f"{self.weather_data['temp']}°{'C' if os.getenv('UNITS')=='metric' else 'F'}")
            self.weather_humidity.setText(f"💧 {self.weather_data['humidity']}%")
            self.weather_wind.setText(f"🌪️ {self.weather_data['wind']} km/h")
            
    def update_news(self):
        """Update news display"""
        # Clear old news
        while self.news_container_layout.count():
            child = self.news_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new news items
        for i, article in enumerate(self.news_data):
            news_item = QWidget()
            news_item_layout = QHBoxLayout(news_item)
            
            # Number
            num = QLabel(f"{i+1}.")
            num.setStyleSheet("color: rgba(100,200,255,0.8); font-weight: bold; font-size: 12px;")
            num.setFixedWidth(25)
            news_item_layout.addWidget(num)
            
            # Title and source
            text_container = QWidget()
            text_layout = QVBoxLayout(text_container)
            text_layout.setSpacing(2)
            text_layout.setContentsMargins(0, 0, 0, 0)
            
            title = QLabel(article['title'][:70] + "..." if len(article['title']) > 70 else article['title'])
            title.setStyleSheet("color: white; font-size: 12px;")
            title.setWordWrap(True)
            text_layout.addWidget(title)
            
            source = QLabel(f"— {article['source']}")
            source.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px;")
            text_layout.addWidget(source)
            
            news_item_layout.addWidget(text_container)
            
            self.news_container_layout.addWidget(news_item)
            
    def update_system_stats(self):
        """Update system stats display"""
        stats = self.system_stats
        
        self.cpu_ring.setValue(stats.get('cpu', 0))
        self.mem_ring.setValue(stats.get('memory', 0))
        self.disk_ring.setValue(stats.get('disk', 0))
        
        # Processes
        if stats.get('processes'):
            self.processes_label.setText("Top processes: " + " | ".join(stats['processes']))
        
        # Disk details
        self.disk_details.setText(
            f"Free: {stats.get('disk_free', 0):.1f}GB / Total: {stats.get('disk_total', 0):.1f}GB"
        )
        
    def mouse_press(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            
    def mouse_move(self, event):
        """Handle mouse move for window dragging"""
        if hasattr(self, 'drag_pos') and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            
    def paintEvent(self, event):
        """Paint gradient background"""
        painter = QPainter(self.main_widget)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(20, 20, 30))
        gradient.setColorAt(1.0, QColor(40, 40, 60))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.main_widget.rect(), 20, 20)
        
    def closeEvent(self, event):
        """Handle close event - minimize to tray"""
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "Lumina Dashboard",
            "Still running in the background",
            QSystemTrayIcon.Information,
            2000
        )

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show dashboard
    dashboard = LuminaDashboard()
    dashboard.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()