import sys
from PySide2.QtWidgets import QApplication
import yaml

from MainWindow import MainWindow


if __name__ == "__main__":
    # 读取配置项
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    app = QApplication(sys.argv)
    window = MainWindow(pdf_folder=config['paper_repo_path'], db_file=config['db_file'])

    window.show()
    sys.exit(app.exec_())
