import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QTextEdit, QSizePolicy, QListWidget,
    QScrollArea, QListWidgetItem, QLineEdit, QComboBox, QMenu,QWidgetAction,QDateEdit, QInputDialog, QDialog, QStackedWidget,QCalendarWidget,QStyle,QStyleFactory,
    QGraphicsDropShadowEffect,QFileDialog,QMessageBox
)
from PyQt6.QtGui import QIcon, QPainter, QColor, QLinearGradient, QBrush, QFont, QPixmap, QPalette, QMovie, QTextOption, QAction, QPen
from PyQt6.QtCore import Qt, QSize, QPoint, QDate, QDateTime, QTimer, QThread, pyqtSignal,QLocale, QRect
from collections import defaultdict
import requests
import json
import uuid
import os

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу, работает как в разработке, так и в собранном .exe"""
    try:
        # PyInstaller создаёт временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WeatherWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = "7843212f383821f21575d4b2526e4634"  # Замените на реальный ключ
        self.settings_file = "settings.json"
        # Загружаем город из настроек
        self.city = self.load_city() or "Москва"
        self.weather_data = None

        self.setStyleSheet("""
            background: rgba(255,255,255,0.8);
            border-radius: 15px;
            padding: 10px;
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(10, 8, 10, 8)

        # --- Поле для ввода города и кнопка ---
        city_layout = QHBoxLayout()
        city_layout.setSpacing(6)
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Введите город")
        self.city_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.5);
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 12px;
                padding: 4px 10px;
                color: #98a1bc;
                font-size: 20px;
            }
        """)
        self.city_input.returnPressed.connect(self.update_weather_by_city)
        city_layout.addWidget(self.city_input, stretch=1)

        self.update_city_btn = QPushButton("Обновить")
        self.update_city_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.5);
                border: none;
                border-radius: 12px;
                padding: 5px 12px;
                color: #98a1bc;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.4); }
        """)
        self.update_city_btn.clicked.connect(self.update_weather_by_city)
        city_layout.addWidget(self.update_city_btn)

        main_layout.addLayout(city_layout)

        # --- Дата ---
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #98a1bc; font-size: 20px; font-weight: 300;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.date_label)

        # --- Температура ---
        self.temp_label = QLabel("--°C")
        self.temp_label.setStyleSheet("color: #98a1bc; font-size: 38px; font-weight: 300;")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.temp_label)

        # --- Feels like ---
        self.feels_label = QLabel("Ощущается как --°")
        self.feels_label.setStyleSheet("color: #98a1bc; font-size: 20px;")
        self.feels_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.feels_label)

        # --- Прогноз на 7 дней (короткие названия) ---
        forecast_layout = QHBoxLayout()
        forecast_layout.setSpacing(6)
        forecast_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Дни недели на русском (коротко)
        self.days_ru = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
        self.forecast_labels = []
        for day in self.days_ru:
            label = QLabel(day)
            label.setStyleSheet("color: #98a1bc; font-size: 20px; font-weight: 300;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            forecast_layout.addWidget(label)
            self.forecast_labels.append(label)

        main_layout.addLayout(forecast_layout)

        # --- Кнопка обновления (в правом верхнем углу) ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(24, 24)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.4); }
        """)
        self.refresh_btn.clicked.connect(self.update_weather)
        btn_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(btn_layout)

        # Таймер обновления (каждые 10 минут)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_weather)
        self.timer.start(600000)  # 10 минут

        # Первое обновление
        self.update_weather()

    def load_city(self):
        """Загружает сохранённый город из файла settings.json."""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("city")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def save_city(self, city):
        """Сохраняет город в файл settings.json."""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump({"city": city}, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def update_weather_by_city(self):
        city = self.city_input.text().strip()
        if city:
            self.city = city
            # Сохраняем город в настройки
            self.save_city(city)
            self.update_weather()

    def update_weather(self):
        """Запрос к OpenWeatherMap и обновление интерфейса."""
        if not self.api_key or self.api_key == "ВАШ_API_КЛЮЧ":
            self.temp_label.setText("Ошибка: нет API ключа")
            return

        url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}&units=metric&lang=ru"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.weather_data = data
                self.update_display(data)
                self.update_forecast(self.city)
            else:
                error_msg = response.json().get("message", "Неизвестная ошибка")
                self.temp_label.setText(f"Ошибка: {error_msg}")
        except requests.exceptions.RequestException as e:
            self.temp_label.setText(f"Ошибка сети: {str(e)}")

    def update_display(self, data):
        """Обновляет все виджеты на основе данных погоды."""
        # Основные данные
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        temp_min = data['main']['temp_min']
        temp_max = data['main']['temp_max']
        description = data['weather'][0]['description']  # уже на русском, т.к. lang=ru

        # Дата и время (локальное)
        locale = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)
        now = QDateTime.currentDateTime()
        self.date_label.setText(locale.toString(now, "dddd, dd MMMM yyyy"))

        # Температура
        self.temp_label.setText(f"{int(round(temp))}°C")
        self.feels_label.setText(f"Ощущается как {int(round(feels_like))}°")
       

        # Заголовок (добавим описание)
        self.temp_label.setToolTip(f"{description}, {self.city}")

    def update_forecast(self, city):
        if not self.api_key or self.api_key == "ВАШ_API_КЛЮЧ":
            return

        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.api_key}&units=metric&lang=ru"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.update_forecast_display(data)
            else:
                # Если прогноз не загрузился, покажем заглушку
                for label in self.forecast_labels:
                    label.setText("--")
        except Exception as e:
            for label in self.forecast_labels:
                label.setText("--")
    
    def update_forecast_display(self, data):
        from collections import defaultdict
        import random

        # Группируем данные по дням (без времени)
        daily_data = defaultdict(list)
        for item in data['list']:
            dt = QDateTime.fromSecsSinceEpoch(item['dt'])
            date_str = dt.toString("yyyy-MM-dd")
            daily_data[date_str].append({
                'temp': item['main']['temp'],
                'description': item['weather'][0]['description'],
                'icon': item['weather'][0]['icon']
            })

        # Сортируем дни
        sorted_dates = sorted(daily_data.keys())
        # Берём максимум 7 дней (доступно 5, но оставим запас)
        max_days = min(len(sorted_dates), 7)

        # Очищаем все метки
        for label in self.forecast_labels:
            label.setText("")

        # Заполняем первые max_days меток
        for i in range(max_days):
            date_str = sorted_dates[i]
            items = daily_data[date_str]
            # Вычисляем среднюю температуру за день
            avg_temp = sum(item['temp'] for item in items) / len(items)
            # Берем описание из первого элемента (или можно выбрать наиболее частое)
            desc = items[0]['description']
            # Иконка (можно использовать эмодзи или скачивать картинки, но для простоты оставим эмодзи)
            # Сопоставляем код иконки с эмодзи
            icon_code = items[0]['icon']
            emoji_map = {
                '01d': '☀️', '01n': '🌙',
                '02d': '⛅', '02n': '☁️',
                '03d': '☁️', '03n': '☁️',
                '04d': '☁️', '04n': '☁️',
                '09d': '🌧️', '09n': '🌧️',
                '10d': '🌦️', '10n': '🌧️',
                '11d': '⛈️', '11n': '⛈️',
                '13d': '❄️', '13n': '❄️',
                '50d': '🌫️', '50n': '🌫️'
            }
            emoji = emoji_map.get(icon_code, '🌤️')

            # Формируем текст: эмодзи + температура
            label = self.forecast_labels[i]
            label.setText(f"{emoji}\n{int(round(avg_temp))}°")
            label.setToolTip(desc)  # подсказка с описанием

        # Остальные метки (если дней меньше 7) оставляем пустыми или скрываем
        for i in range(max_days, len(self.forecast_labels)):
            self.forecast_labels[i].setVisible(False)
    
class CenteredTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._placeholder_text = ""

    def set_my_placeholder(self, text):
        self._placeholder_text = text

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        fm = self.fontMetrics()
        line_h = fm.height()
        if h > 0:
            margin = max(0, (h - line_h) // 2)
            self.document().setDocumentMargin(margin)

    def paintEvent(self, event):
        if self.toPlainText() == "" and self._placeholder_text:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QColor("#9297b0"))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self._placeholder_text)
        super().paintEvent(event)

class StyledEditDialog(QDialog):
    def __init__(self, parent=None, title="Редактировать задачу", label="Новый текст:", initial_text=""):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setFixedSize(350, 200)

        # Общий стиль диалога — без рамки
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 20px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #b0b0b0;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                color: #555;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 0.2);
            }
            QPushButton#ok_btn {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#ok_btn:hover {
                background-color: #45a049;
            }
            QPushButton#cancel_btn {
                background-color: transparent;
                color: #555;
            }
            QPushButton#cancel_btn:hover {
                background-color: rgba(255, 0, 0, 0.15);
                color: #d32f2f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; color: #929bb7;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.text_edit = QLineEdit(initial_text)
        self.text_edit.setPlaceholderText("Введите новый текст...")
        self.text_edit.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
                color: #929bb7;
            }
            QLineEdit:focus {
                border: 2px solid #b0b0b0;
            }
        """)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.ok_btn = QPushButton("Сохранить")
        self.ok_btn.setObjectName("ok_btn")
        self.ok_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.setPen(QPen(QColor(255, 255, 255), 5))
        painter.drawRoundedRect(self.rect(), 30, 30)
        super().paintEvent(event)

    def get_text(self):
        return self.text_edit.text().strip()

    @staticmethod
    def get_text_dialog(parent, title, label, initial_text=""):
        dialog = StyledEditDialog(parent, title, label, initial_text)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.get_text(), True
        return "", False

class StyledDateEditDialog(QDialog):
    def __init__(self, parent=None, title="Изменить дату", initial_date=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setFixedSize(350, 220)

        self.setStyleSheet("""
            QDialog {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 20px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
            QDateEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
                color: #333;
            }
            QDateEdit:focus {
                border: 2px solid #b0b0b0;
            }
            QDateEdit::drop-down {
                border: none;
                width: 24px;
                background: transparent;
            }
            QDateEdit::down-arrow {
                image: none;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                color: #555;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 0.2);
            }
            QPushButton#ok_btn {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#ok_btn:hover {
                background-color: #45a049;
            }
            QPushButton#cancel_btn {
                background-color: transparent;
                color: #555;
            }
            QPushButton#cancel_btn:hover {
                background-color: rgba(255, 0, 0, 0.15);
                color: #d32f2f;
            }
            /* Стили для календаря */
            QCalendarWidget {
                background-color: white;
                border-radius: 12px;
                padding: 5px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f0f0f0;
                border-radius: 12px 12px 0 0;
            }
            QCalendarWidget QToolButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: #555;
                padding: 4px 8px;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: rgba(200, 200, 200, 0.3);
            }
            QCalendarWidget QToolButton:checked,
            QCalendarWidget QToolButton:pressed {
                background-color: rgba(200, 200, 200, 0.5);
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 4px;
            }
            QCalendarWidget QMenu::item {
                padding: 6px 20px;
                border-radius: 6px;
                color: #333;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QCalendarWidget QTableView {
                background-color: white;
                border: none;
                selection-background-color: #4CAF50;
                selection-color: white;
                alternate-background-color: #f9f9f9;
            }
            QCalendarWidget QTableView::item {
                padding: 8px;
                border-radius: 8px;
                border: none;
                color: #333;
            }
            QCalendarWidget QTableView::item:hover {
                background-color: rgba(200, 200, 200, 0.2);
            }
            QCalendarWidget QTableView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QCalendarWidget QHeaderView::section {
                background-color: #f5f5f5;
                color: #555;
                padding: 6px;
                border: none;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
            }
            QCalendarWidget QHeaderView {
                background-color: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; color: #929bb7;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.date_edit = QDateEdit()
        if initial_date is None:
            initial_date = QDate.currentDate()
        self.date_edit.setDate(initial_date)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setCalendarPopup(True)
        # Красивая иконка календаря вместо стрелки
        self.date_edit.setStyleSheet("""
            QDateEdit::drop-down {
                image: url(:/icons/calendar.png);  /* или используем эмодзи через QSS нельзя, но можно задать текст или иконку */
                width: 24px;
                height: 24px;
                border: none;
            }
        """)
        # Поскольку нельзя вставить эмодзи через QSS, сделаем это через QIcon
        # Можно оставить без иконки, т.к. popup работает по клику на поле

        layout.addWidget(self.date_edit)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.ok_btn = QPushButton("Сохранить")
        self.ok_btn.setObjectName("ok_btn")
        self.ok_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRoundedRect(self.rect(), 20, 20)
        super().paintEvent(event)

    def get_date(self):
        return self.date_edit.date()

    @staticmethod
    def get_date_dialog(parent, title="Изменить дату", initial_date=None):
        dialog = StyledDateEditDialog(parent, title, initial_date)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.get_date(), True
        return None, False

class TaskWidget(QFrame):
    def __init__(self, task_id, text, date_str, parent=None):
        super().__init__(parent)
        self._task_id = task_id
        self._original_text = text
        self._current_date = date_str
        self._target_layout = None   # будет установлен при добавлении в layout

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMinimumWidth(0)
        self.setStyleSheet("background-color: white; border-radius: 20px; padding: 5px;")

        # Основной HLayout
        task_layout = QHBoxLayout(self)
        task_layout.setContentsMargins(10, 8, 10, 8)
        task_layout.setSpacing(10)

        # Вертикальный лейаут для текста и даты
        v_layout = QVBoxLayout()
        v_layout.setSpacing(2)

        # Текст задачи
        self._label = QTextEdit()
        self._label.setReadOnly(True)
        self._label.setText(text)
        self._label.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._label.setMinimumWidth(0)
        self._label.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 0px;
                color: #9297b0;
                font-size: 14px;
            }
        """)
        v_layout.addWidget(self._label)

        # Дата (маленькая подпись)
        self._date_label = QLabel(date_str)
        self._date_label.setStyleSheet("color: #b0b0b0; font-size: 10px; padding: 0px;")
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        v_layout.addWidget(self._date_label)

        task_layout.addLayout(v_layout, stretch=1)

        # Кнопка "Выполнено"
        self._done_btn = QPushButton("")
        self._done_btn.setFixedSize(24, 24)
        self._done_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: gray;
                border: 2px solid gray;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: gray;
                color: white;
            }
        """)
        task_layout.addWidget(self._done_btn)

        # Контекстное меню
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos)   # мы передадим обработку в контейнер позже
        )

    # ------ Методы для управления данными ------
    def set_text(self, new_text):
        self._original_text = new_text
        self._label.setText(new_text)

    def set_date(self, new_date_str):
        self._current_date = new_date_str
        self._date_label.setText(new_date_str)

    def get_text(self):
        return self._original_text

    def get_date(self):
        return self._current_date

    def get_task_id(self):
        return self._task_id

    def set_target_layout(self, layout):
        self._target_layout = layout

    def get_target_layout(self):
        return self._target_layout

    # ------ Метод для отображения контекстного меню (вызывается из TaskContainer) ------
    def show_context_menu(self, pos):
        # Мы будем вызывать метод контейнера, передавая себя
        # Для этого нужно хранить ссылку на контейнер
        # Самое простое – установить родителя, и через parent() получить TaskContainer
        parent = self.parent()
        while parent is not None and not isinstance(parent, TaskContainer):
            parent = parent.parent()
        if parent is not None:
            parent.show_context_menu(pos, self)

class TaskManager:
    def __init__(self, storage_file="tasks.json"):
        self.storage_file = storage_file
        self.tasks = []          # список словарей задач
        self.next_id = 1         # для простоты используем числовой ID (можно заменить на uuid)

    def load(self):
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tasks = []
            return

        self.tasks = data.get("tasks", [])
        # Если ID нет, генерируем
        for task in self.tasks:
            if "id" not in task:
                task["id"] = self._generate_id()

    def save(self):
        data = {"tasks": self.tasks}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_id(self):
        # просто инкремент, или можно использовать uuid.uuid4().hex
        new_id = self.next_id
        self.next_id += 1
        return new_id

    def add_task(self, text, column=0, date=None):
        if date is None:
            date = QDate.currentDate().toString("dd.MM.yyyy")
        task = {
            "id": self._generate_id(),
            "text": text,
            "column": column,
            "done": False,
            "original_text": text,
            "date": date
        }
        self.tasks.append(task)
        self.save()
        return task

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save()

    def edit_task(self, task_id, new_text):
        for task in self.tasks:
            if task["id"] == task_id:
                task["text"] = new_text
                task["original_text"] = new_text
                self.save()
                return True
        return False

    def move_task(self, task_id, new_column):
        for task in self.tasks:
            if task["id"] == task_id and not task["done"]:
                task["column"] = new_column
                self.save()
                return True
        return False

    def mark_done(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id and not task["done"]:
                task["done"] = True
                # сохраняем оригинальный текст для возврата
                task["original_text"] = task["text"]
                task["text"] = f"{task['original_text']}  ({QDateTime.currentDateTime().toString('dd.MM.yyyy hh:mm')})"
                self.save()
                return True
        return False

    def restore_task(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id and task["done"]:
                task["done"] = False
                task["text"] = task["original_text"]
                self.save()
                return True
        return False

    def get_active_tasks(self):
        return [t for t in self.tasks if not t["done"]]

    def get_done_tasks(self):
        return [t for t in self.tasks if t["done"]]

    def get_task_text(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                return task["text"]
        return ""
    def get_task_date(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                return task.get("date", QDate.currentDate().toString("dd.MM.yyyy"))
        return QDate.currentDate().toString("dd.MM.yyyy")

class ClickableLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self._menu = None

    def set_menu(self, menu):
        self._menu = menu

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._menu:
            self._menu.exec(self.mapToGlobal(QPoint(0, self.height())))
        super().mousePressEvent(event)

class AllTasksPage(QWidget):
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(20, 20, 20, 20)
        self.h_layout.setSpacing(20)

        self.left_widget = QWidget()
        self.left_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.left_widget.setStyleSheet("background: transparent;")
        self.left_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = QLabel("Все активные задачи")
        title.setStyleSheet("""
            background: rgba(255,255,255,0.7);
            border-radius: 15px;
            color: #98a1bc;
            font-size: 24px;
            font-weight: bold;
            padding: 8px 15px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title, stretch=1)

        self.sort_btn = _SortButton()
        self.sort_btn.setText("Сортировка")
        self.sort_btn.setStyleSheet("background-color: rgba(255,255,255,0.7); color: #98a1bc; border-radius: 12px; font-size: 14px;")
        self.sort_btn.setFixedWidth(140)
        self.sort_btn.setFixedHeight(30)
        self.sort_btn.clicked.connect(self.show_sort_menu)

        self.sort_menu = QMenu()
        self.sort_menu.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.sort_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.sort_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border-radius: 12px;
                padding: 5px;
                border: 1px solid #ddd;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 6px;
                color: #98a1bc;
                font-size: 14px;
                background: transparent;
            }
            QMenu::item:selected {
                background-color: rgba(200,200,200,0.3);
            }
        """)
        self.sort_menu.addAction("По дате", lambda: self.set_sort(0))
        self.sort_menu.addAction("По приоритету", lambda: self.set_sort(1))

        self.sort_mode = 0

        header_layout.addWidget(self.sort_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addLayout(header_layout)

        self.list_widget = QListWidget()
        self.list_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.list_widget.setMinimumHeight(100)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.4);
                border-radius: 30px;
                border: none;
                padding: 15px;
                font-size: 16px;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 6px 0px;
                margin: 0px;
            }
            QScrollBar:vertical {
                width: 0px;
                background: transparent;
            }
        """)
        left_layout.addWidget(self.list_widget)

        self.right_panel = QWidget()
        self.right_panel.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.right_panel.setStyleSheet("background: transparent;")
        self.right_panel.setVisible(False)
        self.right_panel.setMinimumWidth(0)
        self.right_panel.setMaximumWidth(580)
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        title_done = QLabel("Выполненные")
        title_done.setStyleSheet("""
            background: rgba(255,255,255,0.7);
            color: #98a1bc;
            font-size: 24px;
            border-radius: 15px;
            padding: 5px;
        """)
        title_done.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(title_done)

        self.done_list = QListWidget()
        self.done_list.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.done_list.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.7);
                border-radius: 30px;
                border: none;
                color: #98a1bc;
                font-size: 16px;
                padding: 10px;
            }
            QListWidget::item {
                background: rgba(255,255,255,1);
                border-radius: 15px;
                padding: 8px 12px;
                margin: 3px 0px;
            }
            QScrollBar:vertical {
                width: 0px;
                background: transparent;
            }
        """)
        right_layout.addWidget(self.done_list, stretch=3)

        self.h_layout.addWidget(self.left_widget, stretch=1)
        self.h_layout.addWidget(self.right_panel, stretch=1)

        self.load_tasks()
        self.load_done_tasks()

        self.done_list.itemDoubleClicked.connect(self.restore_done_task)
        self.done_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.done_list.customContextMenuRequested.connect(self.show_done_context_menu)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.drawRoundedRect(rect, 30, 30)

    def show_sort_menu(self):
        pos = self.sort_btn.mapToGlobal(QPoint(0, self.sort_btn.height()))
        self.sort_menu.exec(pos)

    def set_sort(self, mode):
        self.sort_mode = mode
        self.sort_btn.setText(["По дате ▼", "По приоритету ▼"][mode])
        self.load_tasks()

    def load_tasks(self):
        self.list_widget.clear()
        tasks = self.task_manager.get_active_tasks()
        if not tasks:
            item = QListWidgetItem("Нет активных задач")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_widget.addItem(item)
            return

        if self.sort_mode == 0:
            tasks.sort(key=lambda t: QDate.fromString(t.get('date', '01.01.2000'), 'dd.MM.yyyy'))
        else:
            tasks.sort(key=lambda t: t.get('column', 0))

        for task in tasks:
            widget = self._create_task_widget(task)
            item = QListWidgetItem()
            # Устанавливаем фиксированную высоту 150 для всех элементов
            item.setSizeHint(QSize(0, 100))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _get_priority_color(self, column):
        colors = {
            0: "#fdd5cf",
            1: "#fee5b7",
            2: "#cbe5d8",
        }
        return colors.get(column, "#b0b0b0")

    def _create_task_widget(self, task):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                padding: 6px 10px;
            }
        """)
        # Устанавливаем фиксированную высоту 150 пикселей
        container.setFixedHeight(100)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        container.setGraphicsEffect(shadow)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        marker = QFrame()
        marker.setFixedWidth(8)
        marker.setFixedHeight(30)
        marker.setStyleSheet(f"""
            border-radius: 4px;
            background-color: {self._get_priority_color(task.get('column', 0))};
        """)
        layout.addWidget(marker, alignment=Qt.AlignmentFlag.AlignVCenter)

        label = QLabel(task["text"])
        label.setWordWrap(True)
        label.setStyleSheet("""
            color: #969eb9;
            font-size: 16px;
            font-weight: 500;
            background: transparent;
            padding: 0px;
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addWidget(label, stretch=1)

        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        date_str = task.get('date', QDate.currentDate().toString('dd.MM.yyyy'))
        date_label = QLabel(date_str)
        date_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right_layout.addWidget(date_label)

        done_btn = QPushButton()
        done_btn.setFixedSize(24, 24)
        done_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #c0c0d0;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
        """)
        done_btn.clicked.connect(lambda: self.mark_task_done(task["id"]))
        right_layout.addWidget(done_btn)

        layout.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

        return container

    def mark_task_done(self, task_id):
        if self.task_manager.mark_done(task_id):
            self.load_tasks()
            self.load_done_tasks()

    def load_done_tasks(self):
        self.done_list.clear()
        for task in self.task_manager.get_done_tasks():
            item = QListWidgetItem(task["text"])
            item.setData(Qt.ItemDataRole.UserRole, task["original_text"])
            item.setSizeHint(QSize(0, 150))
            self.done_list.addItem(item)

    def restore_done_task(self, item):
        original_text = item.data(Qt.ItemDataRole.UserRole)
        if not original_text:
            display_text = item.text()
            idx = display_text.rfind("  (")
            if idx != -1:
                original_text = display_text[:idx]
            else:
                original_text = display_text

        task_id = None
        for task in self.task_manager.tasks:
            if task.get("original_text") == original_text and task.get("done"):
                task_id = task["id"]
                break

        if task_id is not None:
            self.task_manager.restore_task(task_id)
            self.load_tasks()
            self.load_done_tasks()

    def delete_done_task(self, item):
        original_text = item.data(Qt.ItemDataRole.UserRole)
        if not original_text:
            display_text = item.text()
            idx = display_text.rfind("  (")
            if idx != -1:
                original_text = display_text[:idx]
            else:
                original_text = display_text

        task_id = None
        for task in self.task_manager.tasks:
            if task.get("original_text") == original_text and task.get("done"):
                task_id = task["id"]
                break

        if task_id is not None:
            self.task_manager.delete_task(task_id)

        row = self.done_list.row(item)
        self.done_list.takeItem(row)

    def show_done_context_menu(self, pos):
        item = self.done_list.itemAt(pos)
        if item is None:
            return

        menu = QMenu()
        menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border-radius: 20px;
                border: none;
                padding: 5px;
            }
            QMenu::item {
                padding: 0px;
                margin: 0px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(200,200,200,0.15);
                border-radius: 8px;
            }
            QPushButton:focus {
                outline: none;
            }
        """)

        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        btn_restore = QPushButton()
        btn_restore.setIcon(QIcon(resource_path("restore.png")))
        btn_restore.setIconSize(QSize(24, 24))
        btn_restore.setFixedSize(40, 40)
        btn_restore.setToolTip("Восстановить")
        btn_restore.clicked.connect(lambda: self.restore_done_task(item))
        btn_restore.clicked.connect(menu.close)

        btn_delete = QPushButton()
        btn_delete.setIcon(QIcon(resource_path("delete.png")))
        btn_delete.setIconSize(QSize(24, 24))
        btn_delete.setFixedSize(40, 40)
        btn_delete.setToolTip("Удалить навсегда")
        btn_delete.clicked.connect(lambda: self.delete_done_task(item))
        btn_delete.clicked.connect(menu.close)

        layout.addWidget(btn_restore)
        layout.addWidget(btn_delete)

        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(container)
        menu.addAction(widget_action)

        menu.exec(self.done_list.mapToGlobal(pos))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total_width = self.width()
        if total_width > 1230:
            self.right_panel.setVisible(True)
        else:
            self.right_panel.setVisible(False)

class _SortButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #98a1bc;
                font-size: 14px;
                padding: 5px 10px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.5);
            }
        """)

class CalendarGrid(QWidget):
    dateSelected = pyqtSignal(QDate)

    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.current_date = QDate.currentDate()
        self.selected_date = self.current_date
        self.setMinimumSize(350, 250)
        self.setMouseTracking(True)
        self.hovered_date = QDate()
        self.setStyleSheet("background: transparent;")

    def set_date(self, date):
        self.current_date = date
        self.update()

    def previous_month(self):
        self.current_date = self.current_date.addMonths(-1)
        self.update()

    def next_month(self):
        self.current_date = self.current_date.addMonths(1)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 20, 20)

        margin = 12
        top_offset = 30
        day_width = (rect.width() - 2 * margin) // 7
        day_height = (rect.height() - top_offset - margin) // 6

        # Дни недели (русские)
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(150, 150, 170))
        days_of_week = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
        for i, day_name in enumerate(days_of_week):
            cell_rect = QRect(margin + i * day_width, 0, day_width, top_offset)
            painter.drawText(cell_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, day_name)

        # Определяем первый день месяца
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        start_weekday = first_day.dayOfWeek()
        start_offset = start_weekday - 1 if start_weekday != 7 else 6
        days_in_month = first_day.daysInMonth()

        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)

        for day in range(1, days_in_month + 1):
            row = (start_offset + day - 1) // 7
            col = (start_offset + day - 1) % 7
            cell_rect = QRect(margin + col * day_width, top_offset + row * day_height, day_width, day_height)

            date = QDate(self.current_date.year(), self.current_date.month(), day)
            is_today = date == QDate.currentDate()
            is_selected = date == self.selected_date

            text = str(day)
            text_rect = painter.boundingRect(cell_rect, Qt.AlignmentFlag.AlignCenter, text)
            text_center = text_rect.center()

            # Смещаем центр круга на 1 пиксель вправо и на 2 вниз
            circle_center = text_center + QPoint(1, 2)

            radius = min(day_width, day_height) // 2 - 2

            if is_selected:
                painter.setBrush(QColor(255, 255, 255))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(circle_center, radius, radius)
                painter.setPen(QColor(60, 60, 90))
                painter.setBrush(Qt.BrushStyle.NoBrush)
            elif is_today:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QColor(253, 213, 207))
                painter.drawEllipse(circle_center, radius, radius)
                painter.setPen(QColor(60, 60, 90))
            else:
                painter.setPen(QColor(60, 60, 90))

            painter.drawText(cell_rect, Qt.AlignmentFlag.AlignCenter, text)

            # Точки приоритетов
            date_str = date.toString("dd.MM.yyyy")
            tasks = self.task_manager.tasks
            day_tasks = [t for t in tasks if t.get("date") == date_str and not t.get("done", False)]
            if day_tasks:
                priorities = set()
                for t in day_tasks:
                    col_priority = t.get("column", 0)
                    priorities.add(col_priority)
                colors = {
                    0: "#fdd5cf",
                    1: "#fee5b7",
                    2: "#cbe5d8"
                }
                painter.save()
                dot_size = 4
                spacing = 2
                total_dots = len(priorities)
                if total_dots > 0:
                    total_width = total_dots * dot_size + (total_dots - 1) * spacing
                    start_x = text_center.x() - total_width // 2
                    dot_y = text_center.y() + day_height // 2 - 8
                    for i, col_prio in enumerate(sorted(priorities)):
                        color = colors.get(col_prio, "#b0b0b0")
                        painter.setBrush(QColor(color))
                        painter.setPen(Qt.PenStyle.NoPen)
                        dot_rect = QRect(start_x + i * (dot_size + spacing), dot_y, dot_size, dot_size)
                        painter.drawEllipse(dot_rect)
                painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            rect = self.rect()
            margin = 12
            top_offset = 30
            day_width = (rect.width() - 2 * margin) // 7
            day_height = (rect.height() - top_offset - margin) // 6
            click_x = event.position().x()
            click_y = event.position().y()

            if click_x > margin and click_x < rect.width() - margin and click_y > top_offset and click_y < rect.height() - margin:
                col = int((click_x - margin) // day_width)
                row = int((click_y - top_offset) // day_height)
                first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
                start_weekday = first_day.dayOfWeek()
                start_offset = start_weekday - 1 if start_weekday != 7 else 6
                day_number = row * 7 + col - start_offset + 1
                if 1 <= day_number <= first_day.daysInMonth():
                    date = QDate(self.current_date.year(), self.current_date.month(), day_number)
                    self.selected_date = date
                    self.update()
                    self.dateSelected.emit(date)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        rect = self.rect()
        margin = 12
        top_offset = 30
        day_width = (rect.width() - 2 * margin) // 7
        day_height = (rect.height() - top_offset - margin) // 6
        pos = event.position()
        if pos.x() > margin and pos.x() < rect.width() - margin and pos.y() > top_offset and pos.y() < rect.height() - margin:
            col = int((pos.x() - margin) // day_width)
            row = int((pos.y() - top_offset) // day_height)
            first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
            start_weekday = first_day.dayOfWeek()
            start_offset = start_weekday - 1 if start_weekday != 7 else 6
            day_number = row * 7 + col - start_offset + 1
            if 1 <= day_number <= first_day.daysInMonth():
                date = QDate(self.current_date.year(), self.current_date.month(), day_number)
                if date != self.hovered_date:
                    self.hovered_date = date
                    self.update()
                return
        if self.hovered_date.isValid():
            self.hovered_date = QDate()
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_date = QDate()
        self.update()
        super().leaveEvent(event)

class CustomCalendar(QCalendarWidget):
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border-radius: 30px;
                padding: 10px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: transparent;
            }
            QCalendarWidget QToolButton {
                color: #98a1bc;
                font-size: 16px;
                border: none;
                background: transparent;
                padding: 5px;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: rgba(255,255,255,0.5);
            }
            QCalendarWidget QToolButton:pressed {
                background-color: rgba(200,200,200,0.3);
            }
            QCalendarWidget QTableView {
                background: transparent;
                selection-background-color: #7a6bc4;
                selection-color: white;
                alternate-background-color: #f9f9f9;
            }
            QCalendarWidget QTableView::item {
                padding: 8px;
                border-radius: 8px;
                border: none;
            }
            QCalendarWidget QTableView::item:hover {
                background-color: rgba(200,200,200,0.2);
            }
            QCalendarWidget QTableView::item:selected {
                background-color: #7a6bc4;
                color: white;
            }
            QCalendarWidget QHeaderView::section {
                background-color: transparent;
                color: #98a1bc;
                padding: 6px;
                border: none;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
            }
            QCalendarWidget QHeaderView {
                background-color: transparent;
                border: none;
            }
        """)

    def paintCell(self, painter, rect, date):
        # Стандартная отрисовка ячейки
        super().paintCell(painter, rect, date)

        date_str = date.toString("dd.MM.yyyy")
        tasks = self.task_manager.tasks
        day_tasks = [t for t in tasks if t.get("date") == date_str and not t.get("done", False)]
        if not day_tasks:
            return

        # Собираем уникальные приоритеты (column)
        priorities = set()
        for task in day_tasks:
            col = task.get("column", 0)
            priorities.add(col)

        colors = {
            0: "#fdd5cf",   # красный
            1: "#fee5b7",   # жёлтый
            2: "#cbe5d8"    # зелёный
        }

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Центр нижней части ячейки
        x = rect.x() + rect.width() // 2
        y = rect.y() + rect.height() - 8

        dot_size = 6
        spacing = 4
        sorted_priorities = sorted(priorities)
        total_dots = len(sorted_priorities)
        if total_dots == 0:
            painter.restore()
            return

        total_width = total_dots * dot_size + (total_dots - 1) * spacing
        start_x = x - total_width // 2

        for i, col in enumerate(sorted_priorities):
            color = colors.get(col, "#b0b0b0")
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            dot_rect = QRect(start_x + i * (dot_size + spacing), y - dot_size//2, dot_size, dot_size)
            painter.drawEllipse(dot_rect)

        painter.restore()

class CalendarPage(QWidget):
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(10)

        # ---- Фрейм с месяцем и стрелками ----
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            background: rgba(255,255,255,0.7);
            border-radius: 20px;
            padding: 5px;
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #98a1bc;
                font-size: 18px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.5);
                border-radius: 10px;
            }
        """)
        self.prev_btn.clicked.connect(self.on_prev_month)

        self.month_label = QLabel()
        self.month_label.setStyleSheet("color: #99a1bb; border-radius: 15px; font-size: 18px;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("▶")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #98a1bc;
                font-size: 18px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.5);
                border-radius: 10px;
            }
        """)
        self.next_btn.clicked.connect(self.on_next_month)

        header_layout.addWidget(self.prev_btn)
        header_layout.addWidget(self.month_label, stretch=1)
        header_layout.addWidget(self.next_btn)

        layout.addWidget(header_frame)

        # ---- Кастомный календарь ----
        self.calendar = CalendarGrid(self.task_manager)
        self.calendar.dateSelected.connect(self.on_date_selected)
        layout.addWidget(self.calendar)

        # ---- Блок задач для выбранной даты ----
        self.tasks_frame = QFrame()
        self.tasks_frame.setStyleSheet("""
            background: rgba(255,255,255,0.7);
            border-radius: 20px;
            padding: 10px;
        """)
        tasks_layout = QVBoxLayout(self.tasks_frame)
        tasks_layout.setSpacing(8)

        date_header = QHBoxLayout()
        self.date_label = QLabel("Выберите дату")
        self.date_label.setStyleSheet("color: #98a1bc; font-size: 16px; font-weight: bold;")
        date_header.addWidget(self.date_label)

        add_btn = QPushButton("+ Добавить")
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.7);
                border: none;
                border-radius: 12px;
                padding: 4px 10px;
                color: #98a1bc;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.9);
            }
        """)
        add_btn.clicked.connect(self.add_task_for_selected_date)
        date_header.addWidget(add_btn)
        tasks_layout.addLayout(date_header)

        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.2);
                border-radius: 15px;
                border: none;
                color: #98a1bc;
                font-size: 13px;
                padding: 8px;
            }
            QListWidget::item {
                background: rgba(255,255,255,0.8);
                border-radius: 10px;
                padding: 6px;
                margin: 2px 0px;
            }
            QScrollBar:vertical { width: 0px; background: transparent; }
        """)
        tasks_layout.addWidget(self.tasks_list)

        layout.addWidget(self.tasks_frame, stretch=1)

        self.current_date = QDate.currentDate()
        self.calendar.set_date(self.current_date)
        self.update_month_label()
        self.on_date_selected(self.current_date)

    def update_month_label(self):
        # Именительный падеж для месяцев
        month_names = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
            5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
            9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        month = self.calendar.current_date.month()
        self.month_label.setText(month_names[month])

    def on_prev_month(self):
        self.calendar.previous_month()
        self.update_month_label()

    def on_next_month(self):
        self.calendar.next_month()
        self.update_month_label()

    def on_date_selected(self, date):
        self.current_date = date
        date_str = date.toString("dd.MM.yyyy")
        self.date_label.setText(date_str)

        tasks = self.task_manager.tasks
        filtered = [t for t in tasks if t.get("date") == date_str and not t.get("done", False)]
        self.tasks_list.clear()
        if filtered:
            for task in filtered:
                self.tasks_list.addItem(task["text"])
        else:
            self.tasks_list.addItem("Нет активных задач на эту дату")

    def add_task_for_selected_date(self):
        date_str = self.current_date.toString("dd.MM.yyyy")
        text, ok = StyledEditDialog.get_text_dialog(
            self,
            title="Новая задача",
            label="Введите текст задачи для {}".format(date_str),
            initial_text=""
        )
        if ok and text:
            self.task_manager.add_task(text, column=0, date=date_str)
            self.calendar.update()
            self.on_date_selected(self.current_date)

    def refresh(self):
        if hasattr(self, 'current_date'):
            self.calendar.update()
            self.on_date_selected(self.current_date)

class SettingsPage(QWidget):
    def __init__(self, task_manager, main_window, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.main_window = main_window
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        settings_frame = QFrame()
        settings_frame.setStyleSheet("background: rgba(255,255,255,0.4); border-radius: 30px; padding: 20px;")
        settings_layout = QVBoxLayout(settings_frame)

        # --- Выбор фонового изображения ---
        bg_label = QLabel("Фоновое изображение:")
        bg_label.setStyleSheet("color: #98a1bc; font-size: 16px;")
        settings_layout.addWidget(bg_label)

        self.bg_path_label = QLabel("Не выбрано")
        self.bg_path_label.setStyleSheet("color: #98a1bc; font-size: 14px; padding: 5px; background: rgba(255,255,255,0.3); border-radius: 8px;")
        settings_layout.addWidget(self.bg_path_label)

        bg_btn_layout = QHBoxLayout()
        self.select_bg_btn = QPushButton("Выбрать изображение")
        self.select_bg_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.7);
                border: none;
                border-radius: 12px;
                padding: 8px;
                color: #98a1bc;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.9); }
        """)
        self.select_bg_btn.clicked.connect(self.select_background)
        bg_btn_layout.addWidget(self.select_bg_btn)

        self.apply_bg_btn = QPushButton("Применить")
        self.apply_bg_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.7);
                border: none;
                border-radius: 12px;
                padding: 8px;
                color: #98a1bc;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.9); }
        """)
        self.apply_bg_btn.clicked.connect(self.apply_background)
        bg_btn_layout.addWidget(self.apply_bg_btn)

        self.reset_bg_btn = QPushButton("Сбросить")
        self.reset_bg_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.7);
                border: none;
                border-radius: 12px;
                padding: 8px;
                color: #98a1bc;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.9); }
        """)
        self.reset_bg_btn.clicked.connect(self.reset_background)
        bg_btn_layout.addWidget(self.reset_bg_btn)

        settings_layout.addLayout(bg_btn_layout)

        # --- Настройка города ---
        city_label = QLabel("Город для погоды:")
        city_label.setStyleSheet("color: #98a1bc; font-size: 16px; margin-top: 10px;")
        settings_layout.addWidget(city_label)

        city_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Введите город")
        self.city_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.7);
                border: none;
                border-radius: 12px;
                padding: 6px;
                color: #98a1bc;
                font-size: 14px;
            }
        """)
        city_layout.addWidget(self.city_input)

        self.save_city_btn = QPushButton("Сохранить город")
        self.save_city_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.7);
                border: none;
                border-radius: 12px;
                padding: 8px;
                color: #98a1bc;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.9); }
        """)
        self.save_city_btn.clicked.connect(self.save_city)
        city_layout.addWidget(self.save_city_btn)

        settings_layout.addLayout(city_layout)

        # --- Здесь можно добавить другие настройки ---

        layout.addWidget(settings_frame)

        self.selected_bg_path = None
        self.load_settings()

    def load_settings(self):
        """Загружает текущие настройки (город) в поля."""
        # Загружаем город из настроек
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                city = data.get("city", "")
                if city:
                    self.city_input.setText(city)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_city(self):
        city = self.city_input.text().strip()
        if not city:
            QMessageBox.warning(self, "Ошибка", "Введите название города")
            return

        # Сохраняем город в файл
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data["city"] = city
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {e}")
            return

        # Обновляем город в WeatherWidget
        if self.main_window and hasattr(self.main_window, 'task_card'):
            weather_widget = self.main_window.task_card.weather_widget
            if weather_widget:
                weather_widget.city = city
                weather_widget.city_input.setText(city)
                weather_widget.update_weather()

        QMessageBox.information(self, "Успех", f"Город '{city}' сохранён")

    def select_background(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фоновое изображение",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.selected_bg_path = file_path
            self.bg_path_label.setText(file_path)

    def apply_background(self):
        if self.selected_bg_path and self.main_window:
            self.main_window.set_background_image(self.selected_bg_path)
            print(f"Фон применён: {self.selected_bg_path}")

    def reset_background(self):
        if self.main_window:
            self.main_window.reset_background()
            self.bg_path_label.setText("Не выбрано")
            self.selected_bg_path = None
            print("Фон сброшен")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(800, 600)

        # ---- Фоновый гиф ----
        self.bg_movie = QMovie(resource_path("Sleepy_cat.gif"))
        self.bg_label = QLabel(self)
        self.bg_label.setMovie(self.bg_movie)
        self.bg_movie.start()
        self.bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.bg_label.lower()
        self.bg_label.setScaledContents(True)

        saved_bg = self.load_background_path()
        if saved_bg:
            self.set_background_image(saved_bg)

        self.bg_pixmap = QPixmap()
        self.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding

        # Главный контейнер (прозрачный)
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- Заголовок ----
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 1),stop:1 rgba(255, 255, 255, 0))"
        )
        title_bar_layout = QHBoxLayout(self.title_bar)
        welcome = QLabel("Добро пожаловать!")
        welcome.setStyleSheet("font-size: 20px; color: #9197b1;")
        title_bar_layout.addWidget(welcome)
        title_bar_layout.addStretch()

        self.btn_minimize = QPushButton("—")
        self.btn_maximize = QPushButton("□")
        self.btn_close = QPushButton("✕")
        btn_style = """
            QPushButton {
                background-color: transparent;
                color: #9197b1;
                border: none;
                font-size: 16px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: white;
                border-radius: 5px;
                color: #9197b1;
            }
        """
        for btn in (self.btn_minimize, self.btn_maximize, self.btn_close):
            btn.setStyleSheet(btn_style)
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_close.clicked.connect(self.close)

        title_bar_layout.addWidget(self.btn_minimize)
        title_bar_layout.addWidget(self.btn_maximize)
        title_bar_layout.addWidget(self.btn_close)
        title_bar_layout.setContentsMargins(10, 0, 10, 0)

        main_layout.addWidget(self.title_bar)

        # ---- Тело (сайдбар + контент) ----
        body = QWidget()
        body.setStyleSheet("background-color: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ---- Сайдбар ----
        sidebar = QWidget()
        sidebar.setFixedWidth(80)
        sidebar.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 1),stop:1 rgba(255, 255, 255, 0))"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setSpacing(15)

        items = [
            ("home.png", "Home"),
            ("list.png", "List"),
            ("calendar.png", "Calendar"),
            ("settings.png", "Settings")
        ]
        self.sidebar_buttons = []
        for icon_path, tooltip in items:
            btn = QPushButton()
            btn.setIcon(QIcon(resource_path(icon_path)))
            btn.setIconSize(QSize(40, 40))
            btn.setFixedSize(60, 60)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: white;
                    border-radius: 10px;
                }
            """)
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        sidebar_layout.addStretch()

                # ---- Контент (QStackedWidget) ----
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.stacked_widget.setStyleSheet("background: transparent;")

        # Создаём главную страницу (TaskContainer)
        self.task_card = TaskContainer()
        # Получаем общий менеджер задач (чтобы все страницы работали с одними данными)
        self.task_manager = self.task_card.task_manager

        # Создаём остальные страницы
        self.page_list = AllTasksPage(self.task_manager)
        self.page_calendar = CalendarPage(self.task_manager)
        self.page_settings = SettingsPage(self.task_manager, self)

        # Добавляем страницы в стек
        self.stacked_widget.addWidget(self.task_card)      # индекс 0
        self.stacked_widget.addWidget(self.page_list)      # индекс 1
        self.stacked_widget.addWidget(self.page_calendar)  # индекс 2
        self.stacked_widget.addWidget(self.page_settings)  # индекс 3

        self.stacked_widget.currentChanged.connect(self.on_page_changed)

        content_layout.addWidget(self.stacked_widget, stretch=1)

        # ---- Сборка body ----
        body_layout.addWidget(sidebar)
        body_layout.addWidget(content)

        main_layout.addWidget(body)

        # ---- Привязка кнопок сайдбара к страницам ----
        self.sidebar_buttons[0].clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.sidebar_buttons[1].clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.sidebar_buttons[2].clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.sidebar_buttons[3].clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))

        # ---- Логика изменения размера окна ----
        self.setMouseTracking(True)
        self._resize_margin = 10
        self._resizing = False
        self._resize_direction = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self.drag_pos = None

        self.default_gif_path = "Sleepy_cat.gif"

    def save_background_path(self, path):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data["background_path"] = path
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_background_path(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("background_path")
        except (FileNotFoundError, json.JSONDecodeError):
            return None


    def set_background_image(self, path):
        # Останавливаем и очищаем предыдущий GIF, если он был
        if self.bg_label.movie() is not None:
            self.bg_label.movie().stop()
            self.bg_label.setMovie(None)

        # Проверяем, является ли файл GIF
        if path.lower().endswith('.gif'):
            # Загружаем анимированный GIF
            movie = QMovie(path)
            if movie.isValid():
                self.bg_label.setMovie(movie)
                movie.start()
                self.bg_label.setScaledContents(True)
                self.bg_label.show()
                # Очищаем статичный фон, чтобы он не рисовался поверх
                self.bg_pixmap = QPixmap()
                self.update()
                self.save_background_path(path)
                return
            else:
                # Если GIF не загрузился, показываем сообщение или ничего не делаем
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить GIF-файл")
                return
  
        # Если не GIF – загружаем статичное изображение
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.bg_pixmap = pixmap
            self.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding
            self.bg_label.hide()  # скрываем метку (она теперь не используется)
            self.update()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")
     
    def reset_background(self):
         # Останавливаем и удаляем текущий GIF (если есть)
        if self.bg_label.movie() is not None:
            self.bg_label.movie().stop()
            self.bg_label.setMovie(None)
    
        # Возвращаем стандартного кота
        try:
            movie = QMovie(resource_path(self.default_gif_path))
            if movie.isValid():
                self.bg_label.setMovie(movie)
                movie.start()
                self.bg_label.setScaledContents(True)
                self.bg_label.show()
            else:
                # Если файл кота не найден, просто показываем пустой фон
                self.bg_label.hide()
        except Exception:
            self.bg_label.hide()
   
        # Очищаем статичный фон
        self.bg_pixmap = QPixmap()
        self.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding
        self.save_background_path("")
        self.update()

    def on_page_changed(self, index):
        if index == 0:  # Главная страница (TaskContainer)
            self.task_card.rebuild_ui()
        elif index == 1:  # Страница списка (AllTasksPage)
            self.page_list.load_tasks()
            self.page_list.load_done_tasks()
        elif index == 2:  # Страница календаря (CalendarPage)
            self.page_calendar.refresh()
        # index == 3 (Настройки) – обновление не требуется


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(),
                self.bg_scaling_mode,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        super().paintEvent(event)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            self.btn_maximize.setText("❐")

    def _get_resize_direction(self, pos):
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        margin = self._resize_margin
        left = x < margin
        right = x > w - margin
        top = y < margin
        bottom = y > h - margin
        if left and top:
            return 'top-left'
        if right and top:
            return 'top-right'
        if left and bottom:
            return 'bottom-left'
        if right and bottom:
            return 'bottom-right'
        if left:
            return 'left'
        if right:
            return 'right'
        if top:
            return 'top'
        if bottom:
            return 'bottom'
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            direction = self._get_resize_direction(event.position().toPoint())
            if direction:
                self._resizing = True
                self._resize_direction = direction
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry().getRect()
                return
            if self.title_bar.geometry().contains(event.pos()):
                self.drag_pos = event.globalPosition().toPoint()
            else:
                self.drag_pos = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_start_pos is not None:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            x, y, w, h = self._resize_start_geometry
            new_x, new_y, new_w, new_h = x, y, w, h
            if 'left' in self._resize_direction:
                new_w = w - delta.x()
                new_x = x + delta.x()
            if 'right' in self._resize_direction:
                new_w = w + delta.x()
            if 'top' in self._resize_direction:
                new_h = h - delta.y()
                new_y = y + delta.y()
            if 'bottom' in self._resize_direction:
                new_h = h + delta.y()
            min_w, min_h = 600, 450
            if new_w < min_w:
                if 'left' in self._resize_direction:
                    new_x = x + w - min_w
                new_w = min_w
            if new_h < min_h:
                if 'top' in self._resize_direction:
                    new_y = y + h - min_h
                new_h = min_h
            self.setGeometry(new_x, new_y, new_w, new_h)
            self.setCursor(self._cursor_for_direction(self._resize_direction))
        elif self.drag_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.pos() + delta)
            self.drag_pos = event.globalPosition().toPoint()
        else:
            direction = self._get_resize_direction(event.position().toPoint())
            self.setCursor(self._cursor_for_direction(direction))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._resizing = False
            self._resize_direction = None
            self._resize_start_pos = None
            self._resize_start_geometry = None
            self.drag_pos = None
        super().mouseReleaseEvent(event)

    def _cursor_for_direction(self, direction):
        cursor_map = {
            'left': Qt.CursorShape.SizeHorCursor,
            'right': Qt.CursorShape.SizeHorCursor,
            'top': Qt.CursorShape.SizeVerCursor,
            'bottom': Qt.CursorShape.SizeVerCursor,
            'top-left': Qt.CursorShape.SizeFDiagCursor,
            'top-right': Qt.CursorShape.SizeBDiagCursor,
            'bottom-left': Qt.CursorShape.SizeBDiagCursor,
            'bottom-right': Qt.CursorShape.SizeFDiagCursor,
        }
        return cursor_map.get(direction, Qt.CursorShape.ArrowCursor)

    def closeEvent(self, event):
        self.task_card.task_manager.save()
        event.accept()

class TaskContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent")
        self.task_manager = TaskManager()
        self.task_manager.load()
        
        # Основной вертикальный лейаут (дата + содержимое)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        self.scroll_areas = []      # список QScrollArea для колонок
        self.task_widgets = []      # список активных виджетов задач (QFrame)

        # --- Горизонтальный контейнер: левая часть (input + колонки) и правая панель ---
        self.h_layout = QHBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(20)

        # Левая часть (растягивается)
        self.left_widget = QWidget()
        self.left_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(15)

        # Правая панель (выполненные задачи) – по умолчанию скрыта
        self.right_panel = QWidget()
        self.right_panel.setVisible(False)
        # Убираем фиксированные ограничения, делаем растягивающейся
        self.right_panel.setMinimumWidth(0)
        self.right_panel.setMaximumWidth(580)
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_panel.setStyleSheet("""
            background: rgba(255,255,255,0.4);
            border-radius: 30px;
            padding: 10px;
        """)
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        self.weather_widget = WeatherWidget()
        self.weather_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_layout.addWidget(self.weather_widget, stretch=1)

        # Заголовок панели
        title = QLabel("Выполненные")
        title.setStyleSheet("background-color:rgba(255,255,255,0.7);color: #98a1bc; font-size: 30px;")
        self.right_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Список выполненных задач
        self.done_list = QListWidget()
        self.done_list.setStyleSheet("""
        QListWidget {
        background: rgba(255,255,255,0.3);
        border-radius: 30px;
        border: none;
        color: #98a1bc;
        font-size: 14px;
        }
        QListWidget::item {
        background: rgba(255,255,255,1);
        border-radius: 15px;
        padding: 8px;
        margin: 2px;
        }
        QScrollBar:vertical {
        width: 0px;
        background: transparent;
        border: none;
         }
        QScrollBar::handle:vertical {
        background: transparent;
        border: none;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
        }
        """)
        self.right_layout.addWidget(self.done_list, stretch=3)
        
        
        
        
        self.h_layout.addWidget(self.left_widget, stretch=1)
        self.h_layout.addWidget(self.right_panel, stretch=1)
        main_layout.addLayout(self.h_layout, stretch=1)

        # --- Поле ввода + дата + три цветные кнопки ---
        self.input_container = QWidget()
        self.input_container.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(161,125,228, 0.3),
                        stop:1 rgba(93,109,221, 0.3));
            border-radius: 20px;
        """)
        self.input_container.setMinimumWidth(300)
        self.input_container.setMinimumHeight(120)
        self.input_container.setMaximumWidth(1200)
        self.input_container.setMaximumHeight(300)
        self.input_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Вертикальный лейаут для контейнера (дата сверху, поле ввода снизу)
        main_input_layout = QVBoxLayout(self.input_container)
        main_input_layout.setContentsMargins(20, 20, 20, 20)
        main_input_layout.setSpacing(10)
          
        # ---- Верхняя строка: дата ----
        date_layout = QHBoxLayout()
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(0)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background: rgba(255,255,255,0.7);
                border: none;
                border-radius: 12px;
                padding: 4px 10px;
                color: #9297b0;
                font-size: 14px;
                min-width: 100px;
            }
            QDateEdit::drop-down {
                border: none;
            }
            QDateEdit::down-arrow {
                image: none;
            }
        """)
        date_layout.addWidget(self.date_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        main_input_layout.addLayout(date_layout)
 
        # ---- Нижняя строка: поле ввода + кнопки ----
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)

        self.task_input = CenteredTextEdit()
        self.task_input.set_my_placeholder("Введите текст задачи...")
        self.task_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_input.viewport().setAutoFillBackground(False)
        self.task_input.viewport().setStyleSheet("background-color: transparent;")
        self.task_input.setMinimumHeight(100)
        input_layout.addWidget(self.task_input, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)
   
        # Кнопки (красная, жёлтая, зелёная)
        self.btn_red = QPushButton()
        self.btn_yellow = QPushButton()
        self.btn_green = QPushButton()
        self.btn_red.setObjectName("btn_red")
        self.btn_yellow.setObjectName("btn_yellow")
        self.btn_green.setObjectName("btn_green")

        btn_size = 30
        for btn in (self.btn_red, self.btn_yellow, self.btn_green):
            btn.setFixedSize(btn_size, btn_size)
 
        btn_style = """
            QPushButton#btn_red {
                background-color: transparent;
                border: 2px solid rgba(253,213,208,1);
                border-radius: %dpx;
            }
            QPushButton#btn_red:hover { background-color: rgba(253,213,208,1); }
            QPushButton#btn_red:pressed { background-color: rgba(253,213,208,1); }
        
            QPushButton#btn_yellow {
                background-color: transparent;
                border: 2px solid rgba(253,228,183,1);
                border-radius: %dpx;
            }
            QPushButton#btn_yellow:hover { background-color: rgba(253,228,183,1); }
            QPushButton#btn_yellow:pressed { background-color: rgba(253,228,183,1); }
 
            QPushButton#btn_green {
                background-color: transparent;
                border: 2px solid rgba(204,229,216,1);
                border-radius: %dpx;
            }
            QPushButton#btn_green:hover { background-color: rgba(204,229,216,1); }
            QPushButton#btn_green:pressed { background-color: rgba(204,229,216,1); }
        """ % (btn_size//2, btn_size//2, btn_size//2)
 
        button_column = QVBoxLayout()
        button_column.setSpacing(8)
        for btn in (self.btn_red, self.btn_yellow, self.btn_green):
            btn.setStyleSheet(btn_style)
            button_column.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        input_layout.addLayout(button_column)
 
        main_input_layout.addLayout(input_layout)

        # Добавляем input_container в левую часть
        self.left_layout.addWidget(self.input_container)

        # --- Три колонки (виджеты-задачи) ---
        self.columns_container = QWidget()
        self.columns_container.setMinimumWidth(300)
        self.columns_container.setMaximumWidth(1200)
        self.columns_container.setMinimumHeight(180)
        self.columns_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        columns_layout = QHBoxLayout(self.columns_container)
        columns_layout.setContentsMargins(15, 15, 15, 15)
        columns_layout.setSpacing(20)

        self.col_red, self.layout_red = self._create_column("rgba(253,213,208,0.9)")
        self.col_yellow, self.layout_yellow = self._create_column("rgba(253,228,183,0.9)")
        self.col_green, self.layout_green = self._create_column("rgba(204,229,216,0.9)")

        columns_layout.addWidget(self.col_red, stretch=1)
        columns_layout.addWidget(self.col_yellow, stretch=1)
        columns_layout.addWidget(self.col_green, stretch=1)

        self.left_layout.addWidget(self.columns_container)

        # --- Сигналы кнопок ---
        self.btn_red.clicked.connect(lambda: self.add_task(self.layout_red))
        self.btn_yellow.clicked.connect(lambda: self.add_task(self.layout_yellow))
        self.btn_green.clicked.connect(lambda: self.add_task(self.layout_green))

        # Инициализация радиуса и фильтр событий для Enter
        self.update_radius()
        self.task_input.installEventFilter(self)

        self.done_list.itemDoubleClicked.connect(self.restore_task_from_done)
        self.done_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.done_list.customContextMenuRequested.connect(self.show_done_context_menu)
        QTimer.singleShot(0, self.update_radius)
        self.rebuild_ui()

    def eventFilter(self, obj, event):
        if obj == self.task_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.btn_green.click()
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_radius()
        self.update_task_widths()

        # Управление видимостью правой панели
        total_width = self.width()
        if total_width > 1230:
            self.right_panel.setVisible(True)
        else:
            self.right_panel.setVisible(False)
                

        # Вычисляем высоту прокрутки для колонок (70% от высоты контейнера)
        col_height = self.columns_container.height()
        if col_height > 0:
            target_height = int(col_height * 0.7)
            for scroll in self.scroll_areas:
                scroll.setFixedHeight(target_height)
                scroll.setViewportMargins(0, 0, 0, 0)


    def _create_column(self, color):
        wrapper = QWidget()
        wrapper.setStyleSheet("background-color: transparent; border-radius: 10px; padding: 5px;")
        wrapper.setMaximumWidth(500)
        wrapper.setMinimumWidth(0)
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        # Цветная полоска сверху
        color_bar = QFrame()
        color_bar.setFixedHeight(30)
        color_bar.setStyleSheet(f"""
            background-color: {color};
            border-radius: 10px;
            margin: 5px 10px 5px 10px;
        """)

        # Зона прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
                border-radius: 30px;
            }
            QScrollArea::viewport {
                background: transparent;
                border-radius: 30px;
            }
            QScrollBar:vertical {
                width: 0px;
                background: transparent;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: transparent;
                border: none;
                min-height: 0px;
            }
        """)
        scroll.setMinimumHeight(100)
        scroll.setMinimumWidth(0)
        self.scroll_areas.append(scroll)

        tasks_container = QWidget()
        tasks_container.setAutoFillBackground(False)
        tasks_container.setMinimumWidth(40)
        tasks_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 30px;
        """)
        tasks_layout = QVBoxLayout(tasks_container)
        tasks_layout.setContentsMargins(15, 10, 15, 10)
        tasks_layout.setSpacing(5)
        tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(tasks_container)

        layout = QVBoxLayout(wrapper)
        layout.setSpacing(8)
        layout.addWidget(color_bar)
        layout.addWidget(scroll)

        return wrapper, tasks_layout

    def add_task(self, target_layout, text=None, task_id=None):
        if text is None:
            text = self.task_input.toPlainText().strip()
        if not text:
            return

        # Берём дату из календаря
        selected_date = self.date_edit.date().toString("dd.MM.yyyy")

        if task_id is None:
            col_idx = self._get_column_index(target_layout)
            task = self.task_manager.add_task(text, col_idx, selected_date)
            task_id = task["id"]
        else:
            # Если задача уже существует (загрузка из файла), дата уже сохранена
            selected_date = self.task_manager.get_task_date(task_id)

        # Создаём виджет
        task_widget = self._create_task_widget(text, target_layout, task_id, selected_date)
        target_layout.addWidget(task_widget)
        self.task_widgets.append(task_widget)

        self.task_input.clear()
        self.update_task_widths()
    
    def _create_task_widget(self, text, target_layout, task_id, date_str):
        task_widget = TaskWidget(task_id, text, date_str)
        task_widget.set_target_layout(target_layout)
        # Подключаем кнопку "Выполнено"
        task_widget._done_btn.clicked.connect(lambda checked, w=task_widget: self.move_to_done(w))
        return task_widget
    
    def show_context_menu(self, pos, widget):
        menu = QMenu()
        menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border-radius: 20px;
                border: none;
                padding: 5px;
            }
            QMenu::item {
                padding: 0px;
                margin: 0px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 0.15);
                border-radius: 8px;
            }
            QPushButton:pressed {
                background-color: rgba(180, 180, 180, 0.2);
            }
            QPushButton:disabled {
                opacity: 0.3;
            }
            QPushButton:focus {
                outline: none;
                border: none;
            }
        """)
        current_layout = widget.get_target_layout()
        # ---- Первый ряд: кружки приоритетов ----
        container1 = QWidget()
        layout1 = QHBoxLayout(container1)
        layout1.setSpacing(10)
        layout1.setContentsMargins(10, 10, 10, 5)
    
        def create_color_icon(color, size=24):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, size, size)
            painter.end()
            return QIcon(pixmap)

        icon_red = create_color_icon("#fdd5cf")
        icon_yellow = create_color_icon("#fde4b7")
        icon_green = create_color_icon("#cce5d8")
    
        btn_red = QPushButton()
        btn_red.setIcon(icon_red)
        btn_red.setIconSize(QSize(24, 24))
        btn_red.setFixedSize(40, 40)
        btn_red.setEnabled(current_layout != self.layout_red)
        btn_red.clicked.connect(lambda: self.move_task_to_column(widget, self.layout_red))
        btn_red.clicked.connect(menu.close)
    
        btn_yellow = QPushButton()
        btn_yellow.setIcon(icon_yellow)
        btn_yellow.setIconSize(QSize(24, 24))
        btn_yellow.setFixedSize(40, 40)
        btn_yellow.setEnabled(current_layout != self.layout_yellow)
        btn_yellow.clicked.connect(lambda: self.move_task_to_column(widget, self.layout_yellow))
        btn_yellow.clicked.connect(menu.close)
    
        btn_green = QPushButton()
        btn_green.setIcon(icon_green)
        btn_green.setIconSize(QSize(24, 24))
        btn_green.setFixedSize(40, 40)
        btn_green.setEnabled(current_layout != self.layout_green)
        btn_green.clicked.connect(lambda: self.move_task_to_column(widget, self.layout_green))
        btn_green.clicked.connect(menu.close)
    
        layout1.addWidget(btn_red)
        layout1.addWidget(btn_yellow)
        layout1.addWidget(btn_green)
    
        widget_action1 = QWidgetAction(menu)
        widget_action1.setDefaultWidget(container1)
        menu.addAction(widget_action1)
    
        # ---- Второй ряд: иконки редактирования и удаления ----
        container2 = QWidget()
        layout2 = QHBoxLayout(container2)
        layout2.setSpacing(10)
        layout2.setContentsMargins(10, 5, 10, 10)
    
        # Загружаем иконки (поместите файлы edit.png и delete.png в папку с программой)
        edit_icon = QIcon(resource_path("edit.png"))
        delete_icon = QIcon(resource_path("delete.png"))
        calendar_icon = QIcon(resource_path("edit_date.png"))
        # Проверка, если файлов нет – можно использовать запасные символы
        if edit_icon.isNull():
            edit_icon = QIcon()  # или можно использовать QStyle
        if delete_icon.isNull():
            delete_icon = QIcon()
    
        btn_edit = QPushButton()
        btn_edit.setIcon(edit_icon)
        btn_edit.setIconSize(QSize(24, 24))
        btn_edit.setFixedSize(40, 40)
        btn_edit.setToolTip("Редактировать")
        btn_edit.clicked.connect(lambda: self.edit_task(widget))
        btn_edit.clicked.connect(menu.close)
    
        btn_delete = QPushButton()
        btn_delete.setIcon(delete_icon)
        btn_delete.setIconSize(QSize(24, 24))
        btn_delete.setFixedSize(40, 40)
        btn_delete.setToolTip("Удалить")
        btn_delete.clicked.connect(lambda: self.delete_task(widget))
        btn_delete.clicked.connect(menu.close)

        calendar_pixmap = QPixmap(24, 24)
        calendar_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(calendar_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Segoe UI Emoji", 16))
        painter.drawText(calendar_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "")
        painter.end()
        

        btn_calendar = QPushButton()
        btn_calendar.setIcon(calendar_icon)
        btn_calendar.setIconSize(QSize(24, 24))
        btn_calendar.setFixedSize(40, 40)
        btn_calendar.setToolTip("Изменить дату")
        btn_calendar.clicked.connect(lambda: self.change_task_date(widget))
        btn_calendar.clicked.connect(menu.close)

        layout2.addWidget(btn_calendar)
        layout2.addWidget(btn_edit)
        layout2.addWidget(btn_delete)
    
    
        widget_action2 = QWidgetAction(menu)
        widget_action2.setDefaultWidget(container2)
        menu.addAction(widget_action2)
    
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.NoDropShadowWindowHint)
        menu.exec(widget.mapToGlobal(pos))

    def edit_task(self, widget):
        task_id = widget.get_task_id()
        if task_id is None:
            return
        current_text = self.task_manager.get_task_text(task_id)
        new_text, ok = StyledEditDialog.get_text_dialog(
            self,
            title="Редактировать задачу",
            label="Новый текст:",
            initial_text=current_text
        )
        if ok and new_text:
            self.task_manager.edit_task(task_id, new_text)
            widget.set_text(new_text)

    def delete_task(self, widget):
        task_id = widget.get_task_id()
        if task_id is None:
            return
        self.task_manager.delete_task(task_id)
        layout = widget.get_target_layout()
        if layout:
            layout.removeWidget(widget)
        if widget in self.task_widgets:
            self.task_widgets.remove(widget)
        widget.deleteLater()
        self.update_task_widths()

        

    def _get_column_index(self, layout):
        if layout == self.layout_red:
            return 0
        elif layout == self.layout_yellow:
            return 1
        elif layout == self.layout_green:
            return 2
        return 0
        
    def move_task_to_column(self, widget, new_layout):
        old_layout = widget.get_target_layout()
        if old_layout is None or old_layout == new_layout:
            return
        task_id = widget.get_task_id()
        if task_id is not None:
            new_col = self._get_column_index(new_layout)
            self.task_manager.move_task(task_id, new_col)

        old_layout.removeWidget(widget)
        new_layout.addWidget(widget)
        widget.set_target_layout(new_layout)

        self.update_task_widths()
        
    def move_to_done(self, widget):
        task_id = widget.get_task_id()
        if task_id is not None:
            if not self.task_manager.mark_done(task_id):
                return

        task_text = widget.get_text()
        if not task_text:
            return

        now = QDateTime.currentDateTime()
        date_str = now.toString("dd.MM.yyyy hh:mm")
        display_text = f"{task_text}  ({date_str})"

        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, task_text)
        self.done_list.addItem(item)

        target_layout = widget.get_target_layout()
        if target_layout is not None:
            target_layout.removeWidget(widget)
        if widget in self.task_widgets:
            self.task_widgets.remove(widget)
        widget.deleteLater()
        self.update_task_widths()
    
    def restore_task_from_done(self, item):
        original_text = item.data(Qt.ItemDataRole.UserRole)
        if not original_text:
            display_text = item.text()
            idx = display_text.rfind("  (")
            if idx != -1:
                original_text = display_text[:idx]
            else:
                original_text = display_text

        task_id = None
        for task in self.task_manager.tasks:
            if task.get("original_text") == original_text and task.get("done"):
                task_id = task["id"]
                break

        if task_id is not None:
            self.task_manager.restore_task(task_id)   
            self.rebuild_ui()                         
    
    
    def update_task_widths(self):
        for w in self.task_widgets:
            parent = w.parentWidget()
            if parent is not None:
                if hasattr(parent, 'layout'):
                    layout = parent.layout()
                    if layout is not None:
                        container = layout.parentWidget()
                        if container is not None:
                            avail = container.width() - 30
                            if avail > 0:
                                w.setMaximumWidth(avail)

    def update_radius(self):
        # 1. Общий контейнер
        w = self.columns_container.width()
        h = self.columns_container.height()
        if w > 0 and h > 0:
            r = max(10, int(min(w, h) * 0.10))
            self.columns_container.setStyleSheet(f"""
                background: rgba(255, 255, 255, 0.4);
                border-radius: {r}px;
            """)

        # 2. Контейнер ввода
        w_in = self.input_container.width()
        h_in = self.input_container.height()
        if w_in > 0 and h_in > 0:
            r_cap = h_in // 2
            r_in = min(r_cap, max(10, int(min(w_in, h_in) * 0.20)))
            if self.window():
                w_total = self.window().width()
                font_size = max(18, min(35, int(w_total / 20)))
            else:
                font_size = 18
        else:
            # Если размеры ещё не определены (при первом запуске), задаём значения по умолчанию
            r_in = 20
            font_size = 18

        self.task_input.setStyleSheet(f"""
        QTextEdit {{
            background-color: rgba(255, 255, 255, 0.7);
            border: none;
            border-radius: {r_in}px;
            font-size: {font_size}px;
        }}
        QTextEdit::viewport {{
            background-color: transparent;
            border-radius: {r_in}px;
        }}
        """)

        self.input_container.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.5);
            border-radius: {r_in}px;
        """)

        # 3. Цветные колонки
        for col, col_color in [(self.col_red, "rgba(253,213,208,0.7)"),
                           (self.col_yellow, "rgba(253,228,183,0.7)"),
                           (self.col_green, "rgba(204,229,216,0.7)")]:
            w_col = col.width()
            h_col = col.height()
            if w_col > 0 and h_col > 0:
                r_col = max(10, int(min(w_col, h_col) * 0.10))
                col.setStyleSheet(f"""
                    background-color: transparent;
                    border-radius: {r_col}px;
                    padding: 5px;
                """)

    def rebuild_ui(self):
    # Очищаем колонки
        for layout in [self.layout_red, self.layout_yellow, self.layout_green]:
            while layout.count():
                widget = layout.takeAt(0).widget()
                if widget:
                    widget.deleteLater()
        self.task_widgets.clear()
        self.done_list.clear()

        # Восстанавливаем активные задачи
        for task in self.task_manager.get_active_tasks():
            self._add_task_widget(task["text"], task["column"], task_id=task["id"])

        # Восстанавливаем выполненные задачи
        for task in self.task_manager.get_done_tasks():
            item = QListWidgetItem(task["text"])
            item.setData(Qt.ItemDataRole.UserRole, task["original_text"])
            self.done_list.addItem(item)
    
    def _add_task_widget(self, text, column, task_id=None):
        target_layout = [self.layout_red, self.layout_yellow, self.layout_green][column]
        # Вызываем старый add_task, но передаём task_id, если он есть
        self.add_task(target_layout, text=text, task_id=task_id)

    def change_task_date(self, widget):
        task_id = widget.get_task_id()
        if task_id is None:
            return
        current_date_str = self.task_manager.get_task_date(task_id)
        current_date = QDate.fromString(current_date_str, "dd.MM.yyyy")
        new_date, ok = StyledDateEditDialog.get_date_dialog(
            self,
            title="Изменить дату задачи",
            initial_date=current_date
        )
        if ok and new_date is not None:
            new_date_str = new_date.toString("dd.MM.yyyy")
            for task in self.task_manager.tasks:
                if task["id"] == task_id:
                    task["date"] = new_date_str
                    self.task_manager.save()
                    break
            widget.set_date(new_date_str)

    def delete_done_task(self, item):
        original_text = item.data(Qt.ItemDataRole.UserRole)
        if not original_text:
            display_text = item.text()
            idx = display_text.rfind("  (")
            if idx != -1:
                original_text = display_text[:idx]
            else:
                original_text = display_text

        task_id = None
        for task in self.task_manager.tasks:
            if task.get("original_text") == original_text and task.get("done"):
                task_id = task["id"]
                break

        if task_id is not None:
            self.task_manager.delete_task(task_id)

        row = self.done_list.row(item)
        self.done_list.takeItem(row)

    def show_done_context_menu(self, pos):
        item = self.done_list.itemAt(pos)
        if item is None:
            return

        menu = QMenu()
        menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border-radius: 20px;
                border: none;
                padding: 5px;
            }
            QMenu::item {
                padding: 0px;
                margin: 0px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 0.15);
                border-radius: 8px;
            }
            QPushButton:pressed {
                background-color: rgba(180, 180, 180, 0.2);
            }
            QPushButton:focus {
                outline: none;
                border: none;
            }
        """)
  
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
    
        # Кнопка "Восстановить" (используем стандартную иконку сброса)
        btn_restore = QPushButton()
        btn_restore.setIcon(QIcon(resource_path("restore.png")))
        btn_restore.setIconSize(QSize(24, 24))
        btn_restore.setFixedSize(40, 40)
        btn_restore.setToolTip("Восстановить")
        btn_restore.clicked.connect(lambda: self.restore_task_from_done(item))
        btn_restore.clicked.connect(menu.close)
    
        # Кнопка "Удалить навсегда" (используем стандартную иконку корзины)
        btn_delete = QPushButton()
        btn_delete.setIcon(QIcon(resource_path("delete.png")))
        btn_delete.setIconSize(QSize(24, 24))
        btn_delete.setFixedSize(40, 40)
        btn_delete.setToolTip("Удалить навсегда")
        btn_delete.clicked.connect(lambda: self.delete_done_task(item))
        btn_delete.clicked.connect(menu.close)
   
        layout.addWidget(btn_restore)
        layout.addWidget(btn_delete)
   
        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(container)
        menu.addAction(widget_action)
  
        menu.exec(self.done_list.mapToGlobal(pos))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())