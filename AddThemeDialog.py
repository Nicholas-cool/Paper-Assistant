from PySide2.QtWidgets import QVBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QDialog, QMessageBox
from PySide2.QtGui import QFont
from PySide2.QtCore import Qt
import sqlite3


class AddThemeDialog(QDialog):
    def __init__(self, db_file, default_theme_category):
        super(AddThemeDialog, self).__init__()
        self.setWindowTitle("新增主题")
        self.setGeometry(800, 400, 400, 200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # 设置保持在最前

        self.db_file = db_file   # 数据库文件
        self.default_theme_category = default_theme_category

        # 设置字体和行距
        font = QFont()
        font.setPointSize(12)  # 设置字体大小

        self.type_label = QLabel("类型:")
        self.type_label.setFont(font)
        self.type_combobox = QComboBox()

        # 获取类型
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        cur.execute(""" select * from category """)
        category_list = [line[0] for line in cur.fetchall()]
        cur.close()
        conn.close()
        for cate_name in category_list:
            self.type_combobox.addItem(cate_name)

        self.type_combobox.setFont(font)

        self.title_label = QLabel("标题（必须以##开头和结尾）:")
        self.title_label.setFont(font)
        self.title_input = QLineEdit()
        self.title_input.setFont(font)

        self.description_label = QLabel("描述:")
        self.description_label.setFont(font)
        self.description_input = QTextEdit()
        self.description_input.setFont(font)

        self.add_button = QPushButton("新增")
        self.add_button.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combobox)
        layout.addWidget(self.title_label)
        layout.addWidget(self.title_input)
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_input)
        layout.addWidget(self.add_button)

        self.add_button.clicked.connect(self.do_add_theme)
        self.setLayout(layout)

        # 设置默认的选项
        self.show_default_category()

    def do_add_theme(self):
        t_type = self.type_combobox.currentText()
        t_title = self.title_input.text()
        t_desc = self.description_input.toPlainText()
        # print(t_type, t_title, t_desc)

        if t_title[:2] != '##' or t_title[-2:] != '##':
            QMessageBox.information(self, "添加失败", "主题标题不符合格式要求！")
            return

        # 插入数据库中
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        cur.execute(""" insert into theme (category, name, desc) values (?, ?, ?) """, (t_type, t_title, t_desc))
        conn.commit()
        cur.close()
        conn.close()

        QMessageBox.information(self, "成功添加", "主题已成功添加!")
        self.accept()

    def show_default_category(self):
        self.type_combobox.setCurrentText(self.default_theme_category)
