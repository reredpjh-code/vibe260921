"""
PyQt6 GUI 기반 네이버 뉴스 크롤러

검색어를 입력하면 네이버 통합검색(nexearch) 결과에서 뉴스 항목을 수집하고,
네이버뉴스 링크가 있는 기사는 본문까지 가져와 표와 미리보기로 보여준다.
결과는 CSV 또는 엑셀(.xlsx)로 저장할 수 있다.

네이버 검색 결과 페이지는 클래스명이 빌드마다 바뀌는 해시값(예: sds-comps-...)을 쓰기 때문에
클래스 대신 비교적 안정적인 data-heatmap-target 속성(".tit", ".nav", ".body", ".prof")을
기준으로 파싱한다.
"""
import csv
import html
import re
import sys

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

SEARCH_URL = "https://search.naver.com/search.naver"


def clean_text(text):
    """네이버 접근성 텍스트('새 창 열림')와 중복 공백을 제거한다."""
    text = text.replace("새 창 열림", "")
    return re.sub(r"\s+", " ", text).strip()


def get_news_items(query):
    """뉴스 검색 탭(where=news) 결과에서 뉴스 항목별 제목/언론사/요약/링크 정보를 추출한다.

    통합검색(where=nexearch) 첫 화면은 네이버가 화제성 높은 검색어에만 뉴스 블록을
    끼워 넣고, "서울신용보증재단" 같은 기관명 검색어는 뉴스 탭 링크만 보여준 채
    실제 뉴스 블록을 아예 넣지 않는 경우가 있다. 뉴스 전용 탭은 해당 검색어의
    뉴스 결과가 존재하는 한 항상 목록을 보여주므로 이쪽을 기준으로 크롤링한다.
    """
    params = {
        "where": "news",
        "query": query,
    }
    res = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
    res.raise_for_status()
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    items = []
    seen_titles = set()

    for title_a in soup.select("a[data-heatmap-target='.tit']"):
        title = clean_text(title_a.get_text(" ", strip=True))
        article_url = title_a.get("href")
        if not title or not article_url or title in seen_titles:
            continue
        seen_titles.add(title)

        # 제목 링크 주변 컨테이너를 위로 탐색하며 네이버뉴스 링크를 찾는다.
        container = title_a
        nav_a = None
        for _ in range(6):
            if container.parent is None:
                break
            container = container.parent
            nav_a = container.select_one("a[data-heatmap-target='.nav']")
            if nav_a:
                break

        naver_news_url = None
        if nav_a and "네이버뉴스" in nav_a.get_text():
            naver_news_url = nav_a.get("href")

        body_a = container.select_one("a[data-heatmap-target='.body']")
        snippet = clean_text(body_a.get_text(" ", strip=True)) if body_a else ""

        press_tag = container.select_one(".sds-comps-profile-info-title-text")
        press = clean_text(press_tag.get_text(strip=True)) if press_tag else ""

        items.append({
            "title": title,
            "press": press,
            "snippet": snippet,
            "article_url": article_url,
            "naver_news_url": naver_news_url,
        })

    return items


def get_article_content(url):
    """네이버뉴스(n.news.naver.com) 기사 페이지에서 본문 텍스트를 추출한다."""
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    body_tag = soup.select_one("#dic_area")
    if not body_tag:
        return "(본문을 찾을 수 없습니다)"

    for tag in body_tag.select("script, style, span.end_photo_org"):
        tag.decompose()
    return body_tag.get_text("\n", strip=True)


class CrawlWorker(QThread):
    """네트워크 요청을 백그라운드 스레드에서 수행해 UI 멈춤을 막는다."""

    progress = pyqtSignal(str)
    item_crawled = pyqtSignal(dict)
    finished_all = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, query, max_articles):
        super().__init__()
        self.query = query
        self.max_articles = max_articles
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            items = get_news_items(self.query)[: self.max_articles]
        except requests.RequestException as e:
            self.error.emit(f"검색 결과를 가져오지 못했습니다: {e}")
            return

        self.progress.emit(f"'{self.query}' 검색 결과 {len(items)}건을 찾았습니다.")

        results = []
        for i, item in enumerate(items, start=1):
            if self._stop:
                break

            self.progress.emit(f"[{i}/{len(items)}] {item['title']}")
            content = item["snippet"]
            if item["naver_news_url"]:
                try:
                    content = get_article_content(item["naver_news_url"])
                except requests.RequestException as e:
                    self.progress.emit(f"  -> 본문 요청 실패, 요약으로 대체: {e}")
                self.msleep(800)

            result = {
                "title": item["title"],
                "press": item["press"],
                "article_url": item["article_url"],
                "naver_news_url": item["naver_news_url"] or "",
                "content": content,
            }
            results.append(result)
            self.item_crawled.emit(result)

        self.finished_all.emit(results)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 뉴스 크롤러")
        self.resize(1000, 640)

        self.results = []
        self.worker = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("검색어"))
        self.query_edit = QLineEdit("반도체")
        self.query_edit.returnPressed.connect(self.start_crawl)
        search_row.addWidget(self.query_edit, stretch=1)

        search_row.addWidget(QLabel("최대 기사 수"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 50)
        self.max_spin.setValue(10)
        search_row.addWidget(self.max_spin)

        self.start_btn = QPushButton("크롤링 시작")
        self.start_btn.clicked.connect(self.start_crawl)
        search_row.addWidget(self.start_btn)

        self.save_csv_btn = QPushButton("CSV로 저장")
        self.save_csv_btn.setEnabled(False)
        self.save_csv_btn.clicked.connect(self.save_csv)
        search_row.addWidget(self.save_csv_btn)

        self.save_excel_btn = QPushButton("엑셀로 저장")
        self.save_excel_btn.setEnabled(False)
        self.save_excel_btn.clicked.connect(self.save_excel)
        search_row.addWidget(self.save_excel_btn)

        layout.addLayout(search_row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["언론사", "제목", "링크"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.show_selected_content)
        layout.addWidget(self.table, stretch=1)

        layout.addWidget(QLabel("본문 미리보기"))
        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)
        self.content_view.document().setDocumentMargin(20)
        layout.addWidget(self.content_view, stretch=2)

        self.status_label = QLabel("대기 중")
        layout.addWidget(self.status_label)

    def start_crawl(self):
        if self.worker is not None and self.worker.isRunning():
            return

        query = self.query_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "입력 오류", "검색어를 입력하세요.")
            return

        self.table.setRowCount(0)
        self.content_view.clear()
        self.results = []
        self.save_csv_btn.setEnabled(False)
        self.save_excel_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.start_btn.setText("크롤링 중...")

        self.worker = CrawlWorker(query, self.max_spin.value())
        self.worker.progress.connect(self.on_progress)
        self.worker.item_crawled.connect(self.on_item_crawled)
        self.worker.finished_all.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_progress(self, text):
        self.status_label.setText(text)

    def on_item_crawled(self, result):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(result["press"]))
        self.table.setItem(row, 1, QTableWidgetItem(result["title"]))
        self.table.setItem(row, 2, QTableWidgetItem(result["naver_news_url"] or result["article_url"]))

    def on_finished(self, results):
        self.results = results
        self.status_label.setText(f"완료: {len(results)}건 크롤링됨")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("크롤링 시작")
        self.save_csv_btn.setEnabled(bool(results))
        self.save_excel_btn.setEnabled(bool(results))

    def on_error(self, message):
        QMessageBox.critical(self, "오류", message)
        self.status_label.setText("오류로 중단됨")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("크롤링 시작")

    def show_selected_content(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        index = rows[0].row()
        if index < len(self.results):
            self.content_view.setHtml(self._render_article_html(self.results[index]))

    @staticmethod
    def _render_article_html(result):
        """기사 본문을 실제 뉴스처럼 제목/언론사/문단 구분이 있는 리치 텍스트로 렌더링한다."""
        paragraphs = [p.strip() for p in result["content"].split("\n") if p.strip()]
        body_html = "".join(f"<p>{html.escape(p)}</p>" for p in paragraphs)

        return f"""
        <div style="font-family: -apple-system, 'Apple SD Gothic Neo', '맑은 고딕', sans-serif;">
            <h2 style="margin:0 0 4px 0; font-size:20px; line-height:1.4;">
                {html.escape(result['title'])}
            </h2>
            <div style="color:#888888; font-size:13px; margin-bottom:20px;">
                {html.escape(result['press'])}
            </div>
            <div style="font-size:16px; line-height:1.9; color:#222222;">
                {body_html}
            </div>
        </div>
        """

    def save_csv(self):
        if not self.results:
            return
        path, _ = QFileDialog.getSaveFileName(self, "CSV로 저장", "naver_news.csv", "CSV Files (*.csv)")
        if not path:
            return

        fieldnames = ["title", "press", "article_url", "naver_news_url", "content"]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

        QMessageBox.information(self, "저장 완료", f"{path}\n에 저장되었습니다.")

    def save_excel(self):
        if not self.results:
            return
        path, _ = QFileDialog.getSaveFileName(self, "엑셀로 저장", "naver_news.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"

        headers = ["제목", "언론사", "원문 링크", "네이버뉴스 링크", "본문"]
        keys = ["title", "press", "article_url", "naver_news_url", "content"]

        wb = Workbook()
        ws = wb.active
        ws.title = "네이버뉴스"
        ws.append(headers)

        for result in self.results:
            ws.append([result[key] for key in keys])

        widths = [45, 14, 40, 40, 60]
        for i, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = width

        wb.save(path)
        QMessageBox.information(self, "저장 완료", f"{path}\n에 저장되었습니다.")

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
