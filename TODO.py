import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QTextEdit, QSizePolicy, QListWidget,
    QScrollArea, QListWidgetItem, QLineEdit, QComboBox, QMenu,QWidgetAction,QDateEdit, QInputDialog, QDialog, QStackedWidget,QCalendarWidget,QStyle,QStyleFactory,
    QGraphicsDropShadowEffect,QFileDialog,QMessageBox
)
from PyQt6.QtGui import QIcon, QPainter, QColor, QLinearGradient, QBrush, QFont, QPixmap, QPalette, QMovie, QTextOption, QAction, QPen, QCursor
from PyQt6.QtCore import Qt, QSize, QPoint, QDate, QDateTime, QTimer, QThread, pyqtSignal,QLocale, QRect
from collections import defaultdict
import requests
import certifi
import urllib3
import json
import uuid
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

def resource_path(relative_path):
    try:
        # PyInstaller создаёт временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ThemeManager:
    def __init__(self, main_window):
        self.main_window = main_window
        # Два стандартных кота — для светлой и тёмной темы
        self.default_gifs = {
            "light": "pixel_forest_fullscreen.gif",
            "dark": "original_cats_night_fullscreen.gif",
        }
        self.settings_file = "settings.json"
        self.current_theme = "light"
        
    def make_glass(self, widget, radius=20, alpha=0.22, border_alpha=0.45):
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        widget.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, {alpha});
            border: 1px solid rgba(255, 255, 255, {border_alpha});
            border-radius: {radius}px;
        """)
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(120, 90, 50, 60))
        shadow.setOffset(0, 6)
        widget.setGraphicsEffect(shadow)

    def _save_setting(self, key, value):
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data[key] = value
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_setting(self, key, default=None):
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(key, default)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    # ---------- Фон ----------
    def _bg_key(self, theme):
        return f"background_path_{theme}"

    def _stop_current_bg(self):
        """Останавливает текущую гифку (если была)."""
        main = self.main_window
        if main.bg_label.movie() is not None:
            main.bg_label.movie().stop()
            main.bg_label.setMovie(None)

    def _set_gif(self, gif_path):
        """Загружает и запускает GIF на bg_label."""
        main = self.main_window
        self._stop_current_bg()
        movie = QMovie(resource_path(gif_path))
        if movie.isValid():
            main.bg_label.setMovie(movie)
            movie.start()
            main.bg_label.setScaledContents(True)
            main.bg_label.show()
        else:
            main.bg_label.hide()
        main.bg_pixmap = QPixmap()
        main.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding
        main.update()

    def set_background_image(self, path, theme=None):
        """Устанавливает пользовательский фон для указанной темы."""
        if theme is None:
            theme = self.current_theme

        main = self.main_window
        self._stop_current_bg()

        # Если это GIF
        if path.lower().endswith('.gif'):
            movie = QMovie(path)
            if movie.isValid():
                main.bg_label.setMovie(movie)
                movie.start()
                main.bg_label.setScaledContents(True)
                main.bg_label.show()
                main.bg_pixmap = QPixmap()
                main.update()
                self._save_setting(self._bg_key(theme), path)
                return
            else:
                QMessageBox.warning(main, "Ошибка", "Не удалось загрузить GIF-файл")
                return

        # Обычная картинка
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            main.bg_pixmap = pixmap
            main.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding
            main.bg_label.hide()
            main.update()
            self._save_setting(self._bg_key(theme), path)
        else:
            QMessageBox.warning(main, "Ошибка", "Не удалось загрузить изображение")

    def reset_background(self, theme=None):
        if theme is None:
            theme = self.current_theme

        self._save_setting(self._bg_key(theme), "")
        self._set_gif(self.default_gifs.get(theme, self.default_gifs["light"]))

    def load_background_path(self, theme=None):
        if theme is None:
            theme = self.current_theme
        return self._load_setting(self._bg_key(theme), "")

    def apply_current_background(self):
        bg_path = self.load_background_path(self.current_theme)

        if not bg_path:
            self._set_gif(self.default_gifs.get(self.current_theme, self.default_gifs["light"]))
            return

        main = self.main_window
        self._stop_current_bg()

        if bg_path.lower().endswith('.gif'):
            movie = QMovie(bg_path)
            if movie.isValid():
                main.bg_label.setMovie(movie)
                movie.start()
                main.bg_label.setScaledContents(True)
                main.bg_label.show()
                main.bg_pixmap = QPixmap()
                main.update()
                return

        pixmap = QPixmap(bg_path)
        if not pixmap.isNull():
            main.bg_pixmap = pixmap
            main.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding
            main.bg_label.hide()
            main.update()
        else:
            self._set_gif(self.default_gifs.get(self.current_theme, self.default_gifs["light"]))

    # ---------- Курсор ----------
    def apply_cursor(self, cursor_spec):
        main = self.main_window
        if isinstance(cursor_spec, str) and cursor_spec.endswith(('.cur', '.png', '.jpg')):
            pixmap = QPixmap(cursor_spec)
            if not pixmap.isNull():
                cursor = QCursor(pixmap, 0, 0)
                main.setCursor(cursor)
                self._save_setting("cursor", cursor_spec)
                return
            else:
                QMessageBox.warning(main, "Ошибка", "Не удалось загрузить курсор")
                return

        cursor_map = {
            "arrow": Qt.CursorShape.ArrowCursor,
            "hand": Qt.CursorShape.PointingHandCursor,
            "wait": Qt.CursorShape.WaitCursor,
            "ibeam": Qt.CursorShape.IBeamCursor,
            "cross": Qt.CursorShape.CrossCursor,
            "size_all": Qt.CursorShape.SizeAllCursor,
            "size_h": Qt.CursorShape.SizeHorCursor,
            "size_v": Qt.CursorShape.SizeVerCursor,
            "forbidden": Qt.CursorShape.ForbiddenCursor,
            "open_hand": Qt.CursorShape.OpenHandCursor,
            "closed_hand": Qt.CursorShape.ClosedHandCursor,
        }
        cursor_type = cursor_map.get(cursor_spec, Qt.CursorShape.ArrowCursor)
        main.setCursor(cursor_type)
        self._save_setting("cursor", cursor_spec)

    def load_cursor_setting(self):
        return self._load_setting("cursor", "arrow")

    # ---------- Тема ----------
    def apply_theme(self, theme):
        """Применяет тему и автоматически подгружает соответствующего кота/фон."""
        main = self.main_window
        self.current_theme = theme

        if theme == "dark":
            dark_style = """
                QMainWindow, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QListWidget, QTextEdit, QLineEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555;
                }
            """
            main.setStyleSheet(dark_style)
        else:
            main.setStyleSheet("")

        self._save_setting("theme", theme)

        self.apply_current_background()

    def load_theme_setting(self):
        return self._load_setting("theme", "light")

    # ---------- Сброс всех ----------
    def reset_all_settings(self):
        try:
            os.remove(self.settings_file)
        except FileNotFoundError:
            pass

        # Сброс пользовательских фонов обеих тем
        self.current_theme = "light"
        self._save_setting("background_path_light", "")
        self._save_setting("background_path_dark", "")

        self.apply_cursor("arrow")
        self.apply_theme("light")   # это само подставит кота для светлой темы

        if hasattr(self.main_window, 'task_card'):
            weather = self.main_window.task_card.weather_widget
            if weather:
                weather.city = "Москва"
                weather.city_input.setText("")
                weather.update_weather()

        QMessageBox.information(self.main_window, "Сброс", "Все настройки сброшены к значениям по умолчанию")

class WeatherWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = "7843212f383821f21575d4b2526e4634"  # Замените на реальный ключ
        self.settings_file = "settings.json"
        # Загружаем город из настроек
        self.city = self.load_city() or "Москва"
        self.weather_data = None

        self.setStyleSheet("""
        QWidget {
            background: rgba(255, 255, 255, 0.20);
            border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 20px;
            padding: 10px;
            }
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
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: rgba(255,255,255,0.5);
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 12px;
                padding: 4px 10px;
                
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
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,255,255,0.4); }
        """)
        self.update_city_btn.clicked.connect(self.update_weather_by_city)
        city_layout.addWidget(self.update_city_btn)

        main_layout.addLayout(city_layout)

        # --- Дата ---
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.date_label)

        # --- Температура ---
        self.temp_label = QLabel("--°C")
        self.temp_label.setStyleSheet("color: white; font-size: 38px; font-weight: bold;")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.temp_label)

        # --- Feels like ---
        self.feels_label = QLabel("Ощущается как --°")
        self.feels_label.setStyleSheet("color:  white; font-size: 20px;")
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
            label.setStyleSheet("color:  white; font-size: 20px; font-weight: bold;")
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
            font = self.font()
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
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
                background: transparent;
                border-radius: 20px;
                padding: 20px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.75);
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
                color: #6b5a3a;
            }
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
                background-color: rgba(255, 255, 255, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.75);
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
                color: #6b5a3a;
            }
            QLineEdit:focus {
                border: 1px solid rgba(120, 90, 50, 0.45);
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
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(QPen(QColor(255, 255, 255, 230), 2))
        painter.drawRoundedRect(self.rect(), 25, 25)
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
                background: transparent;
                border-radius: 20px;
                padding: 20px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
            QDateEdit {
                background-color: rgba(255, 255, 255, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.75);
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
                color: #6b5a3a;
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
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid rgba(255, 255, 255, 220);
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
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(QPen(QColor(255, 255, 255, 230), 2))
        painter.drawRoundedRect(self.rect(), 25, 25)
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
        self.setStyleSheet("""
            background-color: rgba(255, 255, 255, 1);
            border: 1px solid rgba(255, 255, 255, 0.85);
            border-radius: 20px;
            padding: 5px;
        """)

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
            background: rgba(255,255,255,0.30);
            border: 1px solid rgba(255,255,255,0.45);
            border-radius: 15px;
            color: white;
            font-size: 22px;
            font-weight: bold;
            padding: 8px 15px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title, stretch=1)

        self.sort_btn = _SortButton()
        self.sort_btn.setText("Сортировка")
        self.sort_btn.setStyleSheet("background: rgba(255,255,255,0.30); border: 1px solid rgba(255,255,255,0.45);; color: white; border-radius: 12px; font-size: 14px;")
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
                background: rgba(255,255,255,0.30);
                border: 1px solid rgba(255,255,255,0.45);
                border-radius: 12px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 6px;
                color: white;
                font-weigt: bold;
                font-size: 14px;
                background: transparent;
            }
            QMenu::item:selected {
                background-color: rgba(255,255,255,0.3);
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
                background: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 30px;
                padding: 15px;
                font-size: 16px;
            }
            QListWidget::item { background: transparent; border: none; }
            QScrollBar:vertical { width: 0px; background: transparent; }
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
            background: rgba(255,255,255,0.30);
            border: 1px solid rgba(255,255,255,0.45);
            border-radius: 15px;
            color: white;
            font-size: 22px;
            font-weight: bold;
            padding: 8px;
        """)
        title_done.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(title_done)

        self.done_list = QListWidget()
        self.done_list.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.done_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.30);
                border-radius: 30px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
            QListWidget::item {
                background: rgba(255, 255, 255, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.7);
                border-radius: 15px;
                padding: 8px 12px;
                margin: 3px 0px;
            }
            QScrollBar:vertical { width: 0px; background: transparent; }
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
        painter.setBrush(QBrush(QColor(255, 255, 255, 0)))
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

        # --- Контекстное меню на карточке ---
        container.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        container.customContextMenuRequested.connect(
            lambda pos, w=container, t=task: self._show_task_context_menu(pos, w, t)
        )

        return container
    
    def _move_task_to_column(self, task_id, new_column):
        if self.task_manager.move_task(task_id, new_column):
            self.load_tasks()

    def _edit_active_task(self, task):
        new_text, ok = StyledEditDialog.get_text_dialog(
            self,
            title="Редактировать задачу",
            label="Новый текст:",
            initial_text=task["text"]
        )
        if ok and new_text:
            self.task_manager.edit_task(task["id"], new_text)
            self.load_tasks()

    def _delete_active_task(self, task_id):
        self.task_manager.delete_task(task_id)
        self.load_tasks()

    def _change_active_task_date(self, task):
        current_date_str = task.get("date", QDate.currentDate().toString("dd.MM.yyyy"))
        current_date = QDate.fromString(current_date_str, "dd.MM.yyyy")
        new_date, ok = StyledDateEditDialog.get_date_dialog(
            self,
            title="Изменить дату задачи",
            initial_date=current_date
        )
        if ok and new_date is not None:
            task["date"] = new_date.toString("dd.MM.yyyy")
            self.task_manager.save()
            self.load_tasks()

    def _show_task_context_menu(self, pos, widget, task):
        menu = QMenu()
        menu.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
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
            QPushButton:disabled {
                opacity: 0.3;
            }
            QPushButton:focus {
                outline: none;
                border: none;
            }
        """)

        current_col = task.get("column", 0)

        # ---------- Ряд 1: выбор приоритета ----------
        container1 = QWidget()
        layout1 = QHBoxLayout(container1)
        layout1.setSpacing(10)
        layout1.setContentsMargins(10, 10, 10, 5)

        def _make_icon(color, size=24):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            p = QPainter(pixmap)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QBrush(QColor(color)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(0, 0, size, size)
            p.end()
            return QIcon(pixmap)

        colors = [(0, "#fdd5cf"), (1, "#fee5b7"), (2, "#cce5d8")]
        for col_idx, color in colors:
            b = QPushButton()
            b.setIcon(_make_icon(color))
            b.setIconSize(QSize(24, 24))
            b.setFixedSize(40, 40)
            b.setEnabled(current_col != col_idx)
            b.clicked.connect(lambda _, c=col_idx: self._move_task_to_column(task["id"], c))
            b.clicked.connect(menu.close)
            layout1.addWidget(b)

        wa1 = QWidgetAction(menu)
        wa1.setDefaultWidget(container1)
        menu.addAction(wa1)

        # ---------- Ряд 2: дата / редактировать / удалить ----------
        container2 = QWidget()
        layout2 = QHBoxLayout(container2)
        layout2.setSpacing(10)
        layout2.setContentsMargins(10, 5, 10, 10)

        btn_date = QPushButton()
        btn_date.setIcon(QIcon(resource_path("edit_date.png")))
        btn_date.setIconSize(QSize(24, 24))
        btn_date.setFixedSize(40, 40)
        btn_date.setToolTip("Изменить дату")
        btn_date.clicked.connect(lambda: self._change_active_task_date(task))
        btn_date.clicked.connect(menu.close)

        btn_edit = QPushButton()
        btn_edit.setIcon(QIcon(resource_path("edit.png")))
        btn_edit.setIconSize(QSize(24, 24))
        btn_edit.setFixedSize(40, 40)
        btn_edit.setToolTip("Редактировать")
        btn_edit.clicked.connect(lambda: self._edit_active_task(task))
        btn_edit.clicked.connect(menu.close)

        btn_del = QPushButton()
        btn_del.setIcon(QIcon(resource_path("delete.png")))
        btn_del.setIconSize(QSize(24, 24))
        btn_del.setFixedSize(40, 40)
        btn_del.setToolTip("Удалить")
        btn_del.clicked.connect(lambda: self._delete_active_task(task["id"]))
        btn_del.clicked.connect(menu.close)

        layout2.addWidget(btn_date)
        layout2.addWidget(btn_edit)
        layout2.addWidget(btn_del)

        wa2 = QWidgetAction(menu)
        wa2.setDefaultWidget(container2)
        menu.addAction(wa2)

        menu.exec(widget.mapToGlobal(pos))

    
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
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid rgba(255, 255, 255, 220);
                border-radius: 20px;
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
                background-color: rgba(255,255,255,0.5);
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
        self.setMinimumSize(350, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        painter.setBrush(QColor(255, 255, 255, 130))
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
        painter.drawRoundedRect(rect, 20, 20)

        margin = 12
        top_offset = 30
        day_width = (rect.width() - 2 * margin) // 7
        day_height = (rect.height() - top_offset - margin) // 6

        # Дни недели (русские)
        font = painter.font()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Black)   # максимум жирности (900)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
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
                dot_size = 8
                spacing = 3
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
            background: rgba(255, 255, 255, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.40);
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
                color: white;
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
        self.month_label.setStyleSheet("color: white; font-weight: bold; border-radius: 15px; font-size: 18px;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("▶")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
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
        # Разумные пределы высоты: не даём календарю растянуться до небес
        self.calendar.setMinimumHeight(300)
        self.calendar.setMaximumHeight(560)
        # stretch=3 — календарь растёт в 3 раза быстрее блока задач снизу
        layout.addWidget(self.calendar, stretch=3)

        # ---- Блок задач для выбранной даты ----
        self.tasks_frame = QFrame()
        self.tasks_frame.setStyleSheet("""
            background: rgba(255, 255, 255, 0.0);
            border: 1px solid rgba(255, 255, 255, 0.0);
            border-radius: 20px;
            padding: 10px;
        """)
        self.tasks_frame.setMinimumHeight(180)
        tasks_layout = QVBoxLayout(self.tasks_frame)
        tasks_layout.setSpacing(8)

        date_header = QHBoxLayout()
        self.date_label = QLabel("Выберите дату")
        self.date_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px; font-weight: bold;")
        date_header.addWidget(self.date_label)

        add_btn = QPushButton("+ Добавить")
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.40);
                border: 1px solid rgba(255, 255, 255, 0.55);
                border: none;
                border-radius: 12px;
                padding: 4px 10px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.6);
            }
        """)
        add_btn.clicked.connect(self.add_task_for_selected_date)
        date_header.addWidget(add_btn)
        tasks_layout.addLayout(date_header)

        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("""
        QListWidget {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 15px;
            color: white;
            font-weight: bold;
            font-size: 13px;
            padding: 8px;
        }
        QListWidget::item {
            background: rgba(255, 255, 255, 0.55);
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

class GlassComboBox(QComboBox):
    """QComboBox со стеклянным combo-полем и светлым popup-списком со скруглениями."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_popup_style()

    def _apply_popup_style(self):
        view = self.view()
        if view is None:
            return

        container = view.parentWidget()

        # ---------- 1. Контейнер popup (QComboBoxPrivateContainer) ----------
        if container is not None and container is not self:
            # Полупрозрачное окно без рамки — тогда border-radius реально виден
            container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            container.setWindowFlags(
                Qt.WindowType.Popup
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.NoDropShadowWindowHint
            )
            container.setStyleSheet("""
                QFrame {
                    background-color: #ecebe6;
                    border: 1px solid rgba(255, 255, 255, 0.90);
                    border-radius: 7px;
                }
            """)

        # ---------- 2. Внутренний QListView — прозрачный ----------
        # Отдаём весь фон контейнеру — тогда его скруглённые углы видны
        view.setStyleSheet("""
            QListView {
                background: transparent;
                color: white;
                border: none;
                padding: 4px;
                outline: none;
                selection-background-color: #b6b8d0;
                selection-color: #2a2a3a;
            }
            QListView::item {
                padding: 6px 10px;
                border-radius: 5px;
                min-height: 22px;
                color: white;
                background-color: transparent;
            }
            QListView::item:hover {
                background-color: #d6d4e0;
            }
            QListView::item:selected {
                background-color: #b6b8d0;
                color: #2a2a3a;
            }
        """)
        view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        view.viewport().setAutoFillBackground(False)
        view.viewport().setStyleSheet("background: transparent;")

        pal = view.palette()
        # Base/Window делаем полностью прозрачными, чтобы контейнер был виден
        pal.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0, 0))
        pal.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
        pal.setColor(QPalette.ColorRole.Text, QColor("#3a3a4a"))
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#3a3a4a"))
        pal.setColor(QPalette.ColorRole.Highlight, QColor("#b6b8d0"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#2a2a3a"))
        view.setPalette(pal)

    def showPopup(self):
        # Переприменяем перед показом — popup-контейнер может пересоздаться
        self._apply_popup_style()
        super().showPopup()

class SettingsPage(QWidget):
    def __init__(self, task_manager, main_window, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.main_window = main_window
        self.setStyleSheet("background-color: transparent;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical {
                width: 8px; background: rgba(255,255,255,0.10); border-radius: 4px;
                margin: 4px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.45); border-radius: 4px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)

        # ==================== ДВЕ КОЛОНКИ ====================
        columns = QHBoxLayout()
        columns.setSpacing(15)

        # ---------- ЛЕВАЯ: Внешний вид ----------
        left_card, left_layout = self._make_section("Внешний вид")

        # Тема
        self.theme_combo = GlassComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.setStyleSheet(self._combo_style())
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        left_layout.addLayout(self._setting_row("Тема", self.theme_combo))

        left_layout.addWidget(self._divider())

        # Фон светлой темы
        left_layout.addWidget(self._subtitle("Фон светлой темы"))
        self.bg_light_path_label = QLabel("Стандартный")
        self.bg_light_path_label.setStyleSheet(self._path_label_style())
        self.bg_light_path_label.setWordWrap(True)
        left_layout.addWidget(self.bg_light_path_label)

        light_btn_row = QHBoxLayout()
        light_btn_row.setSpacing(8)
        self.select_bg_light_btn = QPushButton("Выбрать")
        self.select_bg_light_btn.setStyleSheet(self._btn_style())
        self.select_bg_light_btn.clicked.connect(lambda: self.select_background("light"))
        light_btn_row.addWidget(self.select_bg_light_btn)

        self.reset_bg_light_btn = QPushButton("Сбросить")
        self.reset_bg_light_btn.setStyleSheet(self._btn_style())
        self.reset_bg_light_btn.clicked.connect(lambda: self.reset_background("light"))
        light_btn_row.addWidget(self.reset_bg_light_btn)
        left_layout.addLayout(light_btn_row)

        left_layout.addWidget(self._divider())

        # Фон тёмной темы
        left_layout.addWidget(self._subtitle("Фон тёмной темы"))
        self.bg_dark_path_label = QLabel("Стандартный")
        self.bg_dark_path_label.setStyleSheet(self._path_label_style())
        self.bg_dark_path_label.setWordWrap(True)
        left_layout.addWidget(self.bg_dark_path_label)

        dark_btn_row = QHBoxLayout()
        dark_btn_row.setSpacing(8)
        self.select_bg_dark_btn = QPushButton("Выбрать")
        self.select_bg_dark_btn.setStyleSheet(self._btn_style())
        self.select_bg_dark_btn.clicked.connect(lambda: self.select_background("dark"))
        dark_btn_row.addWidget(self.select_bg_dark_btn)

        self.reset_bg_dark_btn = QPushButton("Сбросить")
        self.reset_bg_dark_btn.setStyleSheet(self._btn_style())
        self.reset_bg_dark_btn.clicked.connect(lambda: self.reset_background("dark"))
        dark_btn_row.addWidget(self.reset_bg_dark_btn)
        left_layout.addLayout(dark_btn_row)

        left_layout.addWidget(self._divider())

        # Курсор
        self.cursor_combo = QComboBox()
        self.cursor_combo.addItems([
            "arrow", "hand", "wait", "ibeam", "cross",
            "size_all", "size_h", "size_v", "forbidden",
            "open_hand", "closed_hand"
        ])
        self.cursor_combo.setStyleSheet(self._combo_style())
        self.cursor_combo.currentTextChanged.connect(self.apply_cursor)
        left_layout.addLayout(self._setting_row("Курсор", self.cursor_combo))

        self.load_cursor_btn = QPushButton("Загрузить свой курсор…")
        self.load_cursor_btn.setStyleSheet(self._btn_style())
        self.load_cursor_btn.clicked.connect(self.load_custom_cursor)
        left_layout.addWidget(self.load_cursor_btn)

        left_layout.addStretch()

        # ---------- ПРАВАЯ: Погода ----------
        right_card, right_layout = self._make_section("Погода")

        right_layout.addWidget(self._subtitle("Город"))
        city_hint = QLabel("Погода показывается на главной странице справа.")
        city_hint.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 12px; background: transparent;border-radius: 7px;")
        city_hint.setWordWrap(True)
        right_layout.addWidget(city_hint)

        right_layout.addSpacing(4)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Например: Москва")
        self.city_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.20);
                border: 1px solid rgba(255, 255, 255, 0.45);
                border-radius: 12px;
                padding: 10px 14px;
                color: white;
                font-weight: bold;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.85);
                background: rgba(255, 255, 255, 0.28);
            }
        """)
        right_layout.addWidget(self.city_input)

        self.save_city_btn = QPushButton("Сохранить город")
        self.save_city_btn.setStyleSheet(self._btn_style())
        self.save_city_btn.clicked.connect(self.save_city)
        right_layout.addWidget(self.save_city_btn)

        right_layout.addStretch()

        columns.addWidget(left_card, stretch=1)
        columns.addWidget(right_card, stretch=1)
        root.addLayout(columns)

        # ==================== ОПАСНАЯ ЗОНА ====================
        danger_card = QFrame()
        danger_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        danger_card.setMinimumHeight(130)
        danger_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 90, 90, 0.15);
                border: 1px solid rgba(255, 120, 120, 0.55);
                border-radius: 7px;
            }
        """)
        danger_layout = QVBoxLayout(danger_card)
        danger_layout.setContentsMargins(20, 15, 20, 15)
        danger_layout.setSpacing(8)

        danger_title = QLabel("Опасная зона")
        danger_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent;")
        danger_layout.addWidget(danger_title)

        danger_hint = QLabel("Сбросит все настройки (тема, фон, курсор, город) к значениям по умолчанию.")
        danger_hint.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;")
        danger_hint.setWordWrap(True)
        danger_layout.addWidget(danger_hint)

        reset_all_btn = QPushButton("Сбросить все настройки")
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 80, 80, 0.85);
                border: 1px solid rgba(255, 150, 150, 0.9);
                border-radius: 12px;
                padding: 10px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(255, 60, 60, 1.0); }
            QPushButton:pressed { background: rgba(220, 40, 40, 1.0); }
        """)
        reset_all_btn.clicked.connect(self.reset_all_settings)
        danger_layout.addWidget(reset_all_btn)

        root.addWidget(danger_card)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        # ==================== ЗАГРУЗКА ====================
        self.load_settings()
    
    def _make_section(self, title_text):
        """Карточка-секция с заголовком. Возвращает (frame, content_layout)."""
        frame = QFrame()
        frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        frame.setMinimumHeight(300)
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.38);
                border-radius: 7px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(title)

        # Тонкая линия под заголовком
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(255, 255, 255, 0.25); border: none;")
        layout.addWidget(line)

        return frame, layout

    def _setting_row(self, label_text, widget, stretch=1):
        """Строка 'метка — виджет'."""
        row = QHBoxLayout()
        row.setSpacing(12)
        label = QLabel(label_text)
        label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
            background: transparent;
        """)
        label.setFixedWidth(80)
        row.addWidget(label)
        row.addWidget(widget, stretch=stretch)
        return row

    def _subtitle(self, text):
        """Подзаголовок внутри секции (серый, маленький)."""
        lbl = QLabel(text)
        lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.85);
            font-size: 13px;
            font-weight: bold;
            background: transparent;
        """)
        return lbl

    def _divider(self):
        """Тонкая линия-разделитель между блоками."""
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(255, 255, 255, 0.18); border: none; margin: 4px 0;")
        return line

    def _combo_style(self):
        return """
        QComboBox {
            background: rgba(255, 255, 255, 0.20);
            border: 1px solid rgba(255, 255, 255, 0.45);
            border-radius: 7px;
            padding: 8px 12px;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }
        QComboBox:hover {
            background: rgba(255, 255, 255, 0.30);
        }
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid white;
            width: 0px;
            height: 0px;
            margin-right: 8px;
        }

        QComboBox QAbstractItemView,
        QComboBox QListView {
            background-color: #ecebe6;
            color: #3a3a4a;
            selection-background-color: #b6b8d0;
            selection-color: #2a2a3a;
            border: 1px solid rgba(255, 255, 255, 0.9);
            border-radius: 7px;
            padding: 4px;
            outline: none;
        }
        QComboBox QAbstractItemView::item,
        QComboBox QListView::item {
            background-color: transparent;
            color: #3a3a4a;
            padding: 6px 10px;
            border-radius: 5px;
            min-height: 22px;
        }
        QComboBox QAbstractItemView::item:hover,
        QComboBox QListView::item:hover {
            background-color: #d6d4e0;
        }
        QComboBox QAbstractItemView::item:selected,
        QComboBox QListView::item:selected {
            background-color: #b6b8d0;
            color: #2a2a3a;
        }
        """

    def _path_label_style(self):
        return """
            color: white;
            font-size: 12px;
            font-weight: bold;
            padding: 8px 10px;
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.30);
            border-radius: 8px;
        """
    
    def _btn_style(self):
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.20);
                border: 1px solid rgba(255, 255, 255, 0.45);
                border-radius: 12px;
                padding: 9px 14px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.65);
            }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.45); }
        """

    def load_settings(self):
        """Загружает все настройки в поля."""
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)

                # Город
                city = data.get("city", "")
                if city:
                    self.city_input.setText(city)

                # Курсор
                cursor = data.get("cursor", "arrow")
                index = self.cursor_combo.findText(cursor)
                if index >= 0:
                    self.cursor_combo.setCurrentIndex(index)

                # Тема
                theme = data.get("theme", "light")
                theme_index = self.theme_combo.findText("Светлая" if theme == "light" else "Тёмная")
                if theme_index >= 0:
                    self.theme_combo.setCurrentIndex(theme_index)

                # Фоны
                bg_light = data.get("background_path_light", "")
                if bg_light:
                    self.bg_light_path_label.setText(bg_light)
                bg_dark = data.get("background_path_dark", "")
                if bg_dark:
                    self.bg_dark_path_label.setText(bg_dark)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def select_background(self, theme):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Выберите фон для {'светлой' if theme == 'light' else 'тёмной'} темы",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            if theme == "light":
                self.bg_light_path_label.setText(file_path)
            else:
                self.bg_dark_path_label.setText(file_path)
            # Сразу применяем, если это текущая тема
            self.main_window.theme_manager.set_background_image(file_path, theme)

    def reset_background(self, theme):
        self.main_window.theme_manager.reset_background(theme)
        if theme == "light":
            self.bg_light_path_label.setText("Стандартный")
        else:
            self.bg_dark_path_label.setText("Стандартный")

    def save_city(self):
        city = self.city_input.text().strip()
        if not city:
            QMessageBox.warning(self, "Ошибка", "Введите название города")
            return

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

        if self.main_window and hasattr(self.main_window, 'task_card'):
            weather = self.main_window.task_card.weather_widget
            if weather:
                weather.city = city
                weather.city_input.setText(city)
                weather.update_weather()

        QMessageBox.information(self, "Успех", f"Город '{city}' сохранён")

    def apply_cursor(self, cursor_name):
        if self.main_window:
            self.main_window.theme_manager.apply_cursor(cursor_name)

    def load_custom_cursor(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл курсора",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.cur)"
        )
        if file_path:
            self.main_window.theme_manager.apply_cursor(file_path)

    def apply_theme(self, theme_name):
        if self.main_window:
            theme = "dark" if theme_name == "Тёмная" else "light"
            self.main_window.theme_manager.apply_theme(theme)

    def reset_all_settings(self):
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите сбросить все настройки?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.main_window.theme_manager.reset_all_settings()
            self.load_settings()
            self.bg_light_path_label.setText("Стандартный (кот)")
            self.bg_dark_path_label.setText("Стандартный (кот)")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # ---- Фоновый гиф ----
        self.bg_movie = QMovie(resource_path("Sleepy_cat.gif"))
        self.bg_label = QLabel(self)
        self.bg_label.setMovie(self.bg_movie)
        self.bg_movie.start()
        self.bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.bg_label.lower()
        self.bg_label.setScaledContents(True)

        self.bg_pixmap = QPixmap()
        self.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding

        # ---- Менеджер визуальных настроек ----
        self.theme_manager = ThemeManager(self)

        # Загружаем сохранённый фон
        saved_bg = self.theme_manager.load_background_path()
        if saved_bg:
            self.theme_manager.set_background_image(saved_bg)

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
        self.title_bar.setStyleSheet("""
            background: rgba(255, 255, 255, 0.25);
            border-bottom: 1px solid rgba(255, 255, 255, 0.35);
        """)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.addStretch()

        self.btn_minimize = QPushButton("—")
        self.btn_maximize = QPushButton("□")
        self.btn_close = QPushButton("✕")
        btn_style = """
            QPushButton {
                background-color: transparent;
                color: white;
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
        sidebar.setStyleSheet("""
            background: rgba(255, 255, 255, 0.25);
            border-right: 1px solid rgba(255, 255, 255, 0.35);
        """)
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
                    background-color: rgba(255,255,255,0.10);
                    border: 1px solid rgba(255,255,255,0.25);
                    border-radius: 14px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.35);
                    border: 1px solid rgba(255,255,255,0.55);
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

        # ---- Загружаем курсор и тему ----
        cursor_setting = self.theme_manager.load_cursor_setting()
        self.theme_manager.apply_cursor(cursor_setting)

        theme_setting = self.theme_manager.load_theme_setting()
        self.theme_manager.apply_theme(theme_setting)

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
            min_w, min_h = 800, 600
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
            background: rgba(255, 255, 255, 0.0);
            border: 1px solid rgba(255, 255, 255, 0.0);
            border-radius: 30px;
        """)
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        self.weather_widget = WeatherWidget()
        self.weather_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_layout.addWidget(self.weather_widget, stretch=1)

        # Заголовок панели
        title = QLabel("Выполненные")
        title.setStyleSheet("""
            background: rgba(255, 255, 255, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.45);
            border-radius: 15px;
            color: white;
            font-size: 22px;
            padding: 8px 12px;
            font-weight: bold;
        """)
        self.right_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Список выполненных задач
        self.done_list = QListWidget()
        self.done_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.30);
                border-radius: 25px;
                color: white;
                font-size: 14px;
                padding: 6px;
                font-weight: bold;
            }
            QListWidget::item {
                background: rgba(255, 255, 255, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.65);
                border-radius: 14px;
                padding: 8px;
                margin: 3px;
            }
            QScrollBar:vertical { width: 0px; background: transparent; }
        """)
        self.right_layout.addWidget(self.done_list, stretch=3)
        
        
        
        
        self.h_layout.addWidget(self.left_widget, stretch=1)
        self.h_layout.addWidget(self.right_panel, stretch=1)
        main_layout.addLayout(self.h_layout, stretch=1)

        # --- Поле ввода + дата + три цветные кнопки ---
        self.input_container = QWidget()
        self.input_container.setStyleSheet("""
            background: rgba(255, 255, 255, 0.0);
            border: 1px solid rgba(255, 255, 255, 0.0);
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
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.30);
                border-radius: 12px;
                padding: 4px 10px;
                color: white;
                font-size: 14px;
                font-weight: bold;
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

        # Если окно свёрнуто — вообще ничего не пересчитываем
        win = self.window()
        if win is not None and win.isMinimized():
            return

        # Если размеры слишком маленькие (идёт сворачивание / анимация) — пропускаем
        if self.width() < 200 or self.height() < 150:
            return

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
            background-color: rgba(255, 255, 255, 0.00);
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
        if self.width() < 200 or self.height() < 150:
            return

        for w in self.task_widgets:
            try:
                parent = w.parentWidget()
                if parent is None:
                    continue
                layout = parent.layout()
                if layout is None:
                    continue
                container = layout.parentWidget()
                if container is None:
                    continue

                avail = container.width() - 30

                if avail > 80:
                    w.setMaximumWidth(avail)
                else:
                    w.setMaximumWidth(16777215)  

            except RuntimeError:
                continue

    def update_radius(self):
        if self.width() < 200 or self.height() < 150:
            return

        # 1. Общий контейнер
        w = self.columns_container.width()
        h = self.columns_container.height()
        if w > 0 and h > 0:
            r = max(10, int(min(w, h) * 0.10))
            self.columns_container.setStyleSheet(f"""
                background: rgba(255, 255, 255, 0.0);
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
            r_in = 20
            font_size = 18

        self.task_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(255, 255, 255, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.50);
                border-radius: {r_in}px;
                font-size: {font_size}px;
                color: white;
                font-weight: bold;
            }}
            QTextEdit::viewport {{
                background-color: transparent;
                border-radius: {r_in}px;
            }}
        """)

        self.input_container.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.0);
            border: 1px solid rgba(255, 255, 255, 0.0);
            border-radius: {r_in}px;
        """)

        # 3. Цветные колонки
        for col, col_color in [(self.col_red, "rgba(253,213,208,0.7)"),
                           (self.col_yellow, "rgba(253,228,183,0.7)"),
                           (self.col_green, "rgba(204,229,216,0.7)")]:
            w_col = col.width()
            h_col = col.height()
            if w_col > 0 and h_col > 0:
                r_col = max(10, int(min(w_col, h_col) * 0.20))
                col.setStyleSheet(f"""
                    background-color: rgba(255, 255, 255, 0.0);
                    border: 1px solid rgba(255, 255, 255, 0.0);
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