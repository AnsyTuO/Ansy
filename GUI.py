import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QTextEdit, QSizePolicy,QListWidget,QScrollArea
)
from PyQt6.QtGui import QIcon, QPainter, QColor, QLinearGradient, QBrush, QFont, QPixmap, QPalette, QMovie,QTextOption
from PyQt6.QtCore import Qt, QSize, QPoint, QDate

class CenteredTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Храним свой плейсхолдер, чтобы не конфликтовать с нативным
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
        # Рисуем свой плейсхолдер только если поле пустое
        if self.toPlainText() == "" and self._placeholder_text:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QColor("#9297b0"))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self._placeholder_text)
        
        # Вызываем super(), но так как нативный placeholder пуст, он ничего лишнего не нарисует
        super().paintEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(800, 600)


        self.bg_movie = QMovie("cat2.gif")
        self.bg_label = QLabel(self)
        self.bg_label.setMovie(self.bg_movie)
        self.bg_movie.start()
        self.bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.bg_label.lower()
        self.bg_label.setScaledContents(True)
        

        self.bg_pixmap = QPixmap()
        #self.bg_scaling_mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding

        # Главный контейнер (прозрачный)
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)


        # --- Заголовок (как был) ---
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 1),stop:1 rgba(255, 255, 255, 0))")
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

        # --- Тело (сайдбар + контент) ---
        body = QWidget()
        body.setStyleSheet("background-color: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Сайдбар
        sidebar = QWidget()
        sidebar.setFixedWidth(80)
        sidebar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 1),stop:1 rgba(255, 255, 255, 0))")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setSpacing(15)

        items = [
            ("домик.png", "Home"),
            ("список.png", "List"),
            ("календарь.png", "Calendar"),
            ("настройки.png", "Settings")
        ]
        for icon_path, tooltip in items:
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
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
        sidebar_layout.addStretch()

        # Контент (здесь будет TaskCard)
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)   # отступы от краёв

        # Создаём TaskContainer и добавляем в контент
        self.task_card = TaskContainer()
        content_layout.addWidget(self.task_card)

        body_layout.addWidget(sidebar)
        body_layout.addWidget(content)

        main_layout.addWidget(body)

        # --- Логика изменения размера (без изменений) ---
        self.setMouseTracking(True)
        self._resize_margin = 10
        self._resizing = False
        self._resize_direction = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self.drag_pos = None

    # 7. Обновляем размер фона при изменении окна
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

    def paintEvent(self, event):
        # Рисуем фон всего окна
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

    # Остальные методы для изменения размера и перетаскивания (оставлены без изменений)
    def _get_resize_direction(self, pos):
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        margin = self._resize_margin
        left = x < margin
        right = x > w - margin
        top = y < margin
        bottom = y > h - margin
        if left and top: return 'top-left'
        if right and top: return 'top-right'
        if left and bottom: return 'bottom-left'
        if right and bottom: return 'bottom-right'
        if left: return 'left'
        if right: return 'right'
        if top: return 'top'
        if bottom: return 'bottom'
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



class TaskContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        self.scroll_areas = []  # Список для хранения зон прокрутки
        self.task_widgets = [] 

        # --- Дата ---
        today = QDate.currentDate()
        self.date_label = QLabel(today.toString("dd.MM.yyyy"))
        self.date_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 14px;
            background: rgba(0,0,0,80);
            padding: 4px 10px;
            border-radius: 10px;
        """)
        main_layout.addWidget(self.date_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # --- Поле ввода + три цветные кнопки ---
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
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(10)

        self.task_input = CenteredTextEdit()
        self.task_input.set_my_placeholder("Введите текст задачи...")
        self.task_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_input.viewport().setAutoFillBackground(False)
        self.task_input.viewport().setStyleSheet("background-color: transparent;")
        self.task_input.setMinimumHeight(100)
        input_layout.addWidget(self.task_input, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Кнопки (красная, жёлтая, зелёная) – без изменений
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
            QPushButton#btn_red:hover { background-color: rgba(253,213,208,0.7); }
            QPushButton#btn_red:pressed { background-color: rgba(253,213,208,0.7); }

            QPushButton#btn_yellow {
                background-color: transparent;
                border: 2px solid rgba(253,228,183,1);
                border-radius: %dpx;
            }
            QPushButton#btn_yellow:hover { background-color: rgba(253,228,183,0.7); }
            QPushButton#btn_yellow:pressed { background-color: rgba(253,228,183,0.7); }

            QPushButton#btn_green {
                background-color: transparent;
                border: 2px solid rgba(204,229,216,1);
                border-radius: %dpx;
            }
            QPushButton#btn_green:hover { background-color: rgba(204,229,216,0.7); }
            QPushButton#btn_green:pressed { background-color: rgba(204,229,216,0.7); }
        """ % (btn_size//2, btn_size//2, btn_size//2)

        button_column = QVBoxLayout()
        button_column.setSpacing(8)
        for btn in (self.btn_red, self.btn_yellow, self.btn_green):
            btn.setStyleSheet(btn_style)
            button_column.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        input_layout.addLayout(button_column)
        main_layout.addWidget(self.input_container)

        # --- Три колонки (виджеты-задачи) с заданными цветами ---
        self.columns_container = QWidget()
        self.columns_container.setMinimumWidth(300)
        self.columns_container.setMaximumWidth(1200)
        self.columns_container.setMinimumHeight(180)
        self.columns_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        columns_layout = QHBoxLayout(self.columns_container)
        columns_layout.setContentsMargins(15, 15, 15, 15)
        columns_layout.setSpacing(20)

        # Создаём колонки с hex-цветами (слева направо)
        self.col_red, self.layout_red = self._create_column("rgba(253,213,208,0.7)")
        self.col_yellow, self.layout_yellow = self._create_column("rgba(253,228,183,0.7)")
        self.col_green, self.layout_green = self._create_column("rgba(204,229,216,0.7)")

        columns_layout.addWidget(self.col_red, stretch=1)
        columns_layout.addWidget(self.col_yellow, stretch=1)
        columns_layout.addWidget(self.col_green, stretch=1)

        main_layout.addWidget(self.columns_container)

        # --- Сигналы кнопок ---
        self.btn_red.clicked.connect(lambda: self.add_task(self.layout_red))
        self.btn_yellow.clicked.connect(lambda: self.add_task(self.layout_yellow))
        self.btn_green.clicked.connect(lambda: self.add_task(self.layout_green))

        # ИНИЦИАЛИЗАЦИЯ РАДИУСА
        self.update_radius()

        self.task_input.installEventFilter(self)

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
        # Вычисляем высоту прокрутки (80% от высоты колонки)
        col_height = self.columns_container.height()
        if col_height > 0:
            target_height = int(col_height * 0.7) 
        
            # Обновляем высоту для всех трех зон прокрутки
            for scroll in self.scroll_areas:
                scroll.setFixedHeight(target_height)
            
            # ВАЖНО: Чтобы полоска прокрутки была короче, нужно 
            # сделать область просмотра (viewport) тоже ограниченной.
                scroll.setViewportMargins(0, 0, 0, 0)  # Отсутствие отступов
        self.update_task_widths()
    
        

    def _create_column(self, color):
        wrapper = QWidget()
        wrapper.setStyleSheet("""
            background-color: transparent;
            border-radius: 10px;
            padding: 5px;
        """)
        wrapper.setMaximumWidth(500)
        wrapper.setMinimumWidth(0)
        wrapper.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.MinimumExpanding
        )

        color_bar = QFrame()
        color_bar.setFixedHeight(30)   # высота полоски
        color_bar.setStyleSheet(f"""
            background-color: {color};
            border-radius: 10px;
            margin: 5px 10px 5px 10px;
        """)

        # Создаем зону прокрутки
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
        tasks_container.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.01);
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

    def add_task(self, target_layout, text=None):
        """Добавляет виджет задачи в указанный лейаут."""
        if text is None:
            text = self.task_input.toPlainText().strip()
        if not text:
            return

        task_widget = QFrame()
        task_layout = QHBoxLayout(task_widget)
        task_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        task_widget.setMinimumWidth(0)
        task_widget.setStyleSheet("""
                        background-color: white;
                        border-radius: 20px;
                        padding: 5px;
                    """)
        task_layout.setContentsMargins(10, 8, 10, 8)
        task_layout.setSpacing(10)

        task_label = QTextEdit()
        task_label.setReadOnly(True)
        task_label.setText(text)
        task_label.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        task_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        task_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        task_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        task_label.setMinimumWidth(0)
        task_label.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 0px;
                color: #9297b0;
                font-size: 14px;
            }
        """)
        # Сохраняем ссылку на QTextEdit в виджете задачи
        task_widget._label = task_label
        task_layout.addWidget(task_label, stretch=1)

        done_btn = QPushButton("")
        done_btn.setFixedSize(24, 24)
        done_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid gray;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: gray;
            }
        """)
        done_btn.clicked.connect(lambda checked, w=task_widget: self.toggle_task_done(w))
        task_layout.addWidget(done_btn)

        target_layout.addWidget(task_widget)
        self.task_widgets.append(task_widget)   # сохраняем для обновления ширины
        self.task_input.clear()
        self.update_task_widths()  # сразу подгоняем ширину

    def toggle_task_done(self, widget):
        if not hasattr(widget, '_done'):
            widget._done = False
        widget._done = not widget._done

    # Получаем QTextEdit
        text_edit = getattr(widget, '_label', None)
        done_btn = None
        for child in widget.findChildren(QPushButton):
            if child.text() == "✓":
                done_btn = child
                break

        if widget._done:
            widget.setStyleSheet("""
                QFrame {
                    background-color: rgba(187, 191, 206, 0.5);
                    border-radius: 20px;
                    padding: 5px;
                }
            """)
            if text_edit:
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background: transparent;
                        border: none;
                        padding: 0px;
                        color: white;
                        font-size: 14px;
                        text-decoration: line-through;
                    }
                """)
            if done_btn:
                done_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: 2px solid #4CAF50;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
        else:
            widget.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 20px;
                    padding: 5px;
                }
            """)
            if text_edit:
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background: transparent;
                        border: none;
                        padding: 0px;
                        color: #9297b0;
                        font-size: 14px;
                    }
                """)
            if done_btn:
                done_btn.setStyleSheet("""
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
            else:
                widget.setStyleSheet("""
                    QFrame {
                    background-color: white;
                    border-radius: 20px;
                    padding: 5px;
                }
            """)
            if text_edit:
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background: transparent;
                        border: none;
                        padding: 0px;
                        color: #9297b0;
                        font-size: 14px;
                    }
                """)
            if done_btn:
                done_btn.setStyleSheet("""
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

    def update_task_widths(self):
        for w in self.task_widgets:
            parent = w.parentWidget()
            if parent is not None:
                if hasattr(parent, 'layout'):
                    layout = parent.layout()
                    if layout is not None:
                        container = layout.parentWidget()
                        if container is not None:
                            avail = container.width() - 30  # отступы (15+15)
                            if avail > 0:
                                w.setMaximumWidth(avail)
    

    def update_radius(self):

        # 1. Обновляем радиус для общего контейнера
        w_in = self.input_container.width()
        h_in = self.input_container.height()
        w = self.columns_container.width()
        h = self.columns_container.height()
        r = max(10, int(min(w_in, h_in) * 0.20))
        
        self.columns_container.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.15);
            border-radius: {r}px;
        """)

        # 2. Обновляем радиус для контейнера ввода (input_container)
        w_in = self.input_container.width()
        h_in = self.input_container.height()
        r_in = max(10, int(min(w_in, h_in) * 0.20))
        w_total = self.window().width() 

        font_size = max(18, min(35, int(w_total / 20)))
        # Главное правило: радиус НИКОГДА не больше половины высоты!
        r_cap = h_in // 2 

        # Считаем радиус и ограничиваем его сверху
        r_in = min(r_cap, max(10, int(min(w_in, h_in) * 0.20)))

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


        # 3. Обновляем радиус для цветных колонок
        columns_data = [
            (self.col_red, "rgba(253,213,208,0.7)"),
            (self.col_yellow, "rgba(253,228,183,0.7)"),
            (self.col_green, "rgba(204,229,216,0.7)")
        ]

        for col, col_color in columns_data:
            # Берем меньшую сторону (обычно это ширина)
            w_col = col.width()
            h_col = col.height()
            
            # Для колонок берем 10% от меньшей стороны
            r_col = max(10, int(min(w_in, h_in) * 0.20))
            
            col.setStyleSheet(f"""
                background-color: transparent;
                border-radius: {r_col}px;
                padding: 5px;
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())