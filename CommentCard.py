import os
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QTabWidget, \
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
import subprocess


class CommentCard(QFrame):
    def __init__(self, type, title, paper_count, description, file_list, file_list_dic, parent=None):
        super(CommentCard, self).__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

        self.type_label = QLabel(type)
        self.title_label = QLabel(title)
        self.paper_count_label = QLabel(paper_count)

        self.title_label.setMaximumWidth(270)
        self.title_label.setToolTip(title)  # 设置工具提示为标题文本

        # 添加展开/收起按钮
        self.toggle_button = QPushButton("+")
        self.toggle_button.setFixedSize(30, 30)  # 设置按钮大小
        self.toggle_button.clicked.connect(self.toggle_content)  # 连接按钮的点击事件

        self.title_layout = QHBoxLayout()
        self.title_layout.addWidget(self.type_label)
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()  # 添加弹簧以使按钮位于右侧
        self.title_layout.addWidget(self.paper_count_label)
        self.title_layout.addWidget(self.toggle_button)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)

        self.tab_widget = QTabWidget()
        self.tab_widget.setFixedHeight(220)

        # 第一个标签页：描述
        description_widget = QWidget()
        description_layout = QVBoxLayout()
        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        description_layout.addWidget(self.description_label)
        description_widget.setLayout(description_layout)
        self.tab_widget.addTab(description_widget, "描述")

        # 第二个标签页：文件列表
        file_list_widget = QWidget()
        file_list_layout = QVBoxLayout()
        # self.file_list = QListWidget()   # 不采用表格形式

        self.file_list = QTableWidget()
        self.file_list.setColumnCount(3)  # 设置列数
        self.file_list.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 设置表格不允许编辑内容
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置选择整行
        self.file_list.itemDoubleClicked.connect(self.on_row_double_clicked)  # 连接双击事件处理函数

        # 获取水平表头
        header = self.file_list.horizontalHeader()
        # 设置列的宽度为固定值
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 0)  # 设置最后一列的宽度为0像素
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 100)  # 设置第二列的宽度为100像素
        # 设置第一列的宽度为自动填充剩余宽度
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        # 设置列的标题
        self.file_list.setHorizontalHeaderLabels(["文件名", "出现次数", ""])

        # print(file_list_dic)
        for i, file_name in enumerate(file_list_dic.items()):
            # item = QListWidgetItem(file_name)
            # self.file_list.addItem(item)
            self.file_list.insertRow(i)  # 插入新行
            self.file_list.setItem(i, 0, QTableWidgetItem(os.path.basename(file_name[0])))
            self.file_list.setItem(i, 1, QTableWidgetItem(str(file_name[1]['count'])))
            self.file_list.setItem(i, 2, QTableWidgetItem(file_name[0]))

        file_list_layout.addWidget(self.file_list)
        file_list_widget.setLayout(file_list_layout)
        self.tab_widget.addTab(file_list_widget, "文件列表")

        self.is_content_visible = True  # 初始时标签页内容隐藏
        self.toggle_content()  # 初始时隐藏标签页内容

        self.setup_ui()

    def toggle_content(self):
        # 切换标签页内容的可见性
        self.is_content_visible = not self.is_content_visible
        self.tab_widget.setVisible(self.is_content_visible)
        if self.is_content_visible:
            self.toggle_button.setText("-")
        else:
            self.toggle_button.setText("+")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addLayout(self.title_layout)
        layout.addWidget(self.separator)
        layout.addWidget(self.tab_widget)

        self.setLayout(layout)
        self.description_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def on_row_double_clicked(self, item):
        if item is not None:
            row = item.row()  # 获取双击的行号

            # 获取第一列的文本信息
            pdf_path_full = self.file_list.item(row, 2).text()
            # print(f"Double-clicked on row {pdf_path_full}")

            # 使用系统默认的 PDF 阅读器打开 PDF 文件（适用于 Windows）
            try:
                subprocess.Popen(['start', '', pdf_path_full], shell=True)
            except Exception as e:
                print(f"Error opening PDF file: {e}")
