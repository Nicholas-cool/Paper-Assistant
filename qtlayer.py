import os
import sys
from PySide2.QtCore import QRect, Qt
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, \
    QLineEdit, QFrame, QScrollArea, QTextEdit, QTabWidget, QListWidget, QListWidgetItem, QSizePolicy, QComboBox, \
    QDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSizeGrip
from PySide2.QtGui import QFont, QColor, QPalette
import sqlite3
import fitz  # PyMuPDF
import subprocess


class CommentCard(QFrame):
    def __init__(self, type, title, paper_count, description, file_list, file_list_dic, parent=None):
        super(CommentCard, self).__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

        self.type_label = QLabel(type)
        self.title_label = QLabel(title)
        self.papercount_label = QLabel(paper_count)

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
        self.title_layout.addWidget(self.papercount_label)
        self.title_layout.addWidget(self.toggle_button)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)

        self.tab_widget = QTabWidget()

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


class AddThemeDialog(QDialog):
    def __init__(self):
        super(AddThemeDialog, self).__init__()
        self.setWindowTitle("新增主题")
        self.setGeometry(800, 400, 400, 200)

        # 设置字体和行距
        font = QFont()
        font.setPointSize(12)  # 设置字体大小

        self.type_label = QLabel("类型:")
        self.type_label.setFont(font)
        self.type_combobox = QComboBox()

        # 获取类型
        conn = sqlite3.connect('c_data.db')
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

    def do_add_theme(self):
        t_type = self.type_combobox.currentText()
        t_title = self.title_input.text()
        t_desc = self.description_input.toPlainText()
        # print(t_type, t_title, t_desc)

        if t_title[:2] != '##' or t_title[-2:] != '##':
            QMessageBox.information(self, "添加失败", "主题标题不符合格式要求！")
            return

        # 插入数据库中
        conn = sqlite3.connect('c_data.db')
        cur = conn.cursor()
        cur.execute(""" insert into theme (category, name, desc) values (?, ?, ?) """, (t_type, t_title, t_desc))
        conn.commit()
        cur.close()
        conn.close()

        QMessageBox.information(self, "成功添加", "主题已成功添加!")
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, PDF_folder):
        super(MainWindow, self).__init__()
        self.pdf_folder = PDF_folder
        self.setWindowTitle("Paper Comment Application")
        # self.setFixedSize(650, 600)  # 固定大小
        self.setGeometry(500, 200, 650, 600)   # 可拖动窗口大小
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # 设置窗口始终保持在最前面
        self.init_ui()

        # 创建 QSizeGrip 小部件并添加到窗口的右下角
        self.size_grip = QSizeGrip(self)
        self.size_grip.setGeometry(QRect(self.rect().bottomRight().x() - self.size_grip.width(),
                                         self.rect().bottomRight().y() - self.size_grip.height(),
                                         self.size_grip.width(),
                                         self.size_grip.height()))

    def resizeEvent(self, event):
        # 这是窗口大小变化时的回调函数，保持 QSizeGrip 部件的位置
        self.size_grip.setGeometry(QRect(self.rect().bottomRight().x() - self.size_grip.width(),
                                         self.rect().bottomRight().y() - self.size_grip.height(),
                                         self.size_grip.width(),
                                         self.size_grip.height()))

    def init_ui(self):
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_widget.setFixedHeight(40)

        topic_label = QLabel("注释主题")
        self.topic_sm_label = QLabel("正常")

        font2 = QFont()
        font2.setPointSize(16)
        topic_label.setFont(font2)

        font5 = QFont()
        font5.setPointSize(12)
        font5.setBold(1)
        self.topic_sm_label.setFont(font5)

        self.palette1 = QPalette()
        text_color1 = QColor(0, 0, 255)  # 设置文本颜色为红色
        self.palette1.setColor(QPalette.WindowText, text_color1)

        self.palette2 = QPalette()
        text_color2 = QColor(255, 0, 0)  # 设置文本颜色为红色
        self.palette2.setColor(QPalette.WindowText, text_color2)

        self.topic_sm_label.setPalette(self.palette1)

        add_button = QPushButton("+")
        refresh_button = QPushButton("↻")

        # 连接"+""按钮的点击事件，显示新增评论对话框
        add_button.clicked.connect(self.show_add_theme_dialog)
        refresh_button.clicked.connect(self.refresh_main_layout)

        top_layout.addWidget(topic_label)
        top_layout.addWidget(self.topic_sm_label)
        top_layout.addWidget(add_button)
        top_layout.addWidget(refresh_button)

        top_widget.setLayout(top_layout)

        search_widget = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_widget.setFixedHeight(40)

        search_box = QLineEdit()

        search_type = QComboBox()
        search_type.addItem("全部")
        # 获取类型
        conn = sqlite3.connect('c_data.db')
        cur = conn.cursor()
        cur.execute(""" select * from category """)
        category_list = [line[0] for line in cur.fetchall()]
        cur.close()
        conn.close()
        for cate_name in category_list:
            search_type.addItem(cate_name)

        search_options = QComboBox()
        search_options.addItem("标题")
        search_options.addItem("描述")
        search_options.addItem("论文名")

        font = QFont()
        font.setPointSize(12)
        search_options.setFont(font)
        search_type.setFont(font)
        search_box.setFont(font)

        search_options.setFixedHeight(30)
        search_type.setFixedHeight(30)
        search_button = QPushButton("搜索")
        search_button.setFixedHeight(32)
        search_button.setFont(font)

        search_layout.addWidget(search_box)
        search_layout.addWidget(search_type)
        search_layout.addWidget(search_options)
        search_layout.addWidget(search_button)

        search_widget.setLayout(search_layout)

        main_widget = QScrollArea()
        main_widget.setWidgetResizable(True)

        main_content = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(10)

        self.refresh_main_layout()   # 更新主体部分内容

        main_content.setLayout(self.main_layout)
        main_widget.setWidget(main_content)

        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setSpacing(0)

        central_layout.addWidget(top_widget)
        central_layout.addWidget(search_widget)
        central_layout.addWidget(main_widget)

        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

    def refresh_main_layout(self):
        self.topic_sm_label.setText('更新中')
        self.topic_sm_label.setPalette(self.palette2)
        QApplication.processEvents()  # 立刻更新字体状态

        # 清空布局
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 重新获取PDF中的注释
        anno_dic = {}
        for filepath, dirnames, filenames in os.walk(self.pdf_folder):
            for filename in filenames:
                if filename.split('.')[-1] != 'pdf':
                    continue
                file_path_abs = os.path.join(filepath, filename)
                pdf_document = fitz.open(file_path_abs)

                # 遍历每一页并提取注释
                anno_dic[file_path_abs] = []
                for page_number in range(pdf_document.page_count):
                    page = pdf_document[page_number]
                    annotations = page.annots()

                    for annotation in annotations:
                        annotation_text = annotation.info.get("content", "")
                        if annotation_text:
                            anno_dic[file_path_abs].append((page_number + 1, annotation_text))
                # 关闭PDF文件
                pdf_document.close()
        # print(anno_dic)

        # 获取数据库数据
        conn = sqlite3.connect('c_data.db')
        cur = conn.cursor()

        comments_data = []
        cur.execute(""" select category, name, desc from theme; """)
        theme_all = cur.fetchall()
        for one_theme in theme_all:
            # 当前theme对应的pdf文件
            theme_pdf_dic = {}

            for pdf_path_a in anno_dic.keys():   # 对于每个 pdf
                for single_anno in anno_dic[pdf_path_a]:  # 对于每条注释
                    if one_theme[1] in single_anno[1]:  # 如果符合条件
                        if theme_pdf_dic.get(pdf_path_a) is not None:
                            theme_pdf_dic[pdf_path_a]['count'] += 1
                            theme_pdf_dic[pdf_path_a]['page_list'].append(single_anno[0])
                        else:
                            theme_pdf_dic[pdf_path_a] = {}
                            theme_pdf_dic[pdf_path_a]['count'] = 1
                            theme_pdf_dic[pdf_path_a]['page_list'] = [single_anno[0]]

            # 更新数据库内容
            cur.execute(""" delete from pdf; """)
            for pdf_path_a in theme_pdf_dic.keys():
                cur.execute(""" 
                    insert into pdf (theme, pdf_path, pages, count) values 
                    (?, ?, ?, ?); 
                """, (one_theme[1], pdf_path_a, str(theme_pdf_dic[pdf_path_a]['page_list']).replace('\'', '\"'),
                      theme_pdf_dic[pdf_path_a]['count']))
            conn.commit()

            # 返回前端的数据
            comments_data.append({
                "type": one_theme[0],
                "title": one_theme[1],
                "description": one_theme[2],
                'file_list': [os.path.basename(_) for _ in theme_pdf_dic.keys()],
                'file_list_dic': theme_pdf_dic,
            })

        cur.close()
        conn.close()

        for data in comments_data:
            comment = CommentCard(f"【{data['type']}】", data["title"], f"（论文数 {str(len(data['file_list']))} ）",
                                  data["description"], data["file_list"], data["file_list_dic"])
            self.main_layout.addWidget(comment)

        self.topic_sm_label.setText('正常')
        self.topic_sm_label.setPalette(self.palette1)
        QApplication.processEvents()  # 立刻更新字体状态

    def show_add_theme_dialog(self):
        dialog = AddThemeDialog()
        result = dialog.exec_()

        if result == QDialog.Accepted:  # 添加成功
            # print('accept')
            self.refresh_main_layout()  # 更新主体部分内容


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(PDF_folder=r'C:\Users\wang\Zotero\storage')

    window.show()
    sys.exit(app.exec_())
