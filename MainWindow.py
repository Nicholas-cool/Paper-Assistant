import os
from PySide2.QtCore import QRect, Qt
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, \
    QLineEdit, QScrollArea, QComboBox, QDialog, QSizeGrip
from PySide2.QtGui import QFont, QColor, QPalette
import sqlite3
import fitz  # PyMuPDF

from CommentCard import CommentCard
from AddThemeDialog import AddThemeDialog


class MainWindow(QMainWindow):
    def __init__(self, pdf_folder, db_file, default_theme_category):
        super(MainWindow, self).__init__()

        self.pdf_folder = pdf_folder
        self.db_file = db_file
        self.default_theme_category = default_theme_category

        self.setWindowTitle("Paper Comment Application")
        # self.setFixedSize(650, 600)  # 固定大小
        self.setGeometry(500, 300, 650, 700)   # 可拖动窗口大小
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # 设置窗口始终保持在最前面

        # 部分组件的预定义（防止 warning）
        self.topic_sm_label = None
        self.palette1 = None
        self.palette2 = None
        self.search_box = None
        self.search_type = None
        self.main_layout = None

        # 初始化界面
        self.init_ui()

        # 创建 QSizeGrip 小部件并添加到窗口的右下角
        self.size_grip = QSizeGrip(self)
        self.size_grip.setGeometry(QRect(self.rect().bottomRight().x() - self.size_grip.width(),
                                         self.rect().bottomRight().y() - self.size_grip.height(),
                                         self.size_grip.width(),
                                         self.size_grip.height()))

        # 展示默认分类
        self.show_default_category()

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

        self.search_box = QLineEdit()

        self.search_type = QComboBox()
        self.search_type.addItem("全部")
        # 获取类型
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        cur.execute(""" select * from category """)
        category_list = [line[0] for line in cur.fetchall()]
        cur.close()
        conn.close()
        for cate_name in category_list:
            self.search_type.addItem(cate_name)

        self.search_options = QComboBox()
        self.search_options.addItem("标题")
        # self.search_options.addItem("描述")
        # self.search_options.addItem("论文名")

        self.search_box.textChanged.connect(self.search_main_layout)
        self.search_type.currentIndexChanged.connect(self.search_main_layout)

        font = QFont()
        font.setPointSize(12)
        self.search_options.setFont(font)
        self.search_type.setFont(font)
        self.search_box.setFont(font)

        self.search_options.setFixedHeight(30)
        self.search_type.setFixedHeight(30)
        search_button = QPushButton("搜索")
        search_button.setFixedHeight(32)
        search_button.setFont(font)
        search_button.clicked.connect(self.search_main_layout)

        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.search_type)
        search_layout.addWidget(self.search_options)
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

        # 重新获取 PDF 中的注释
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
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        comments_data = []
        cur.execute(""" select category, name, desc from theme; """)
        theme_all = cur.fetchall()

        # 清空 pdf 表
        cur.execute(""" delete from pdf; """)

        for one_theme in theme_all:
            # 当前 theme 对应的 pdf 文件
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
            for pdf_path_a in theme_pdf_dic.keys():
                cur.execute(""" 
                    insert into pdf (theme, pdf_path, pages, count) values (?, ?, ?, ?); 
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

        # 展示默认分类
        self.show_default_category()

    def search_main_layout(self):
        # 清空布局
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 获取搜索条件
        search_text = self.search_box.text()
        search_type = self.search_type.currentText()
        # search_option = self.search_options.currentText()

        # 获取数据库数据
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        comments_data = []

        if search_type == '全部':
            cur.execute(""" select category, name, desc from theme where name like ?; """, (f'%{search_text}%',))
        else:
            cur.execute(""" select category, name, desc from theme where category = ? and name like ?; 
            """, (search_type, f'%{search_text}%'))
        theme_all = cur.fetchall()

        for one_theme in theme_all:
            # 当前 theme 对应的 pdf 文件
            theme_pdf_dic = {}
            cur.execute(""" select theme, pdf_path, pages, count from pdf where theme = ?; """, (one_theme[1],))

            for _ in cur.fetchall():
                theme_pdf_dic[_[1]] = {
                    'count': _[3],
                    'page_list': eval(_[2]) if _[2] else []
                }

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

    def show_add_theme_dialog(self):
        dialog = AddThemeDialog(self.db_file, self.default_theme_category)
        result = dialog.exec_()

        if result == QDialog.Accepted:  # 添加成功
            # print('accept')
            self.refresh_main_layout()  # 更新主体部分内容

    def show_default_category(self):
        self.search_type.setCurrentText(self.default_theme_category)
        self.search_main_layout()
