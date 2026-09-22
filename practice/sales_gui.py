import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QTabWidget,
    QTableView,
    QPushButton,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QStyledItemDelegate,
    QComboBox,
    QCompleter,
    QDateEdit,
    QHeaderView,
    QStatusBar,
)

DB_PATH = Path(__file__).parent / "sample.db"

STYLESHEET = """
QWidget {
    background-color: #F4F6FB;
    color: #262B3D;
    font-family: "Apple SD Gothic Neo", "Malgun Gothic", "Segoe UI", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #F4F6FB;
}
QTabWidget::pane {
    border: 1px solid #DDE2F0;
    border-radius: 8px;
    background: #FFFFFF;
    top: -1px;
}
QTabBar::tab {
    background: #E7EAF6;
    color: #4A4F6A;
    padding: 9px 22px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #4F5DFF;
    color: #FFFFFF;
}
QTabBar::tab:hover:!selected {
    background: #D6DBF5;
}
QGroupBox {
    border: 1px solid #DDE2F0;
    border-radius: 8px;
    margin-top: 10px;
    padding: 12px 10px 10px 10px;
    background: #FBFCFF;
    font-weight: 600;
    color: #4A4F6A;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #4F5DFF;
}
QTableView {
    background-color: #FFFFFF;
    alternate-background-color: #F1F3FC;
    gridline-color: #E7EAF6;
    selection-background-color: #4F5DFF;
    selection-color: #FFFFFF;
    border: 1px solid #DDE2F0;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #2E3352;
    color: #FFFFFF;
    padding: 6px;
    border: none;
    font-weight: 600;
}
QTableView::item {
    padding: 4px;
}
QPushButton {
    background-color: #E7EAF6;
    color: #333A5C;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #D6DBF5;
}
QPushButton:pressed {
    background-color: #C3CAF0;
}
QPushButton#addBtn {
    background-color: #3B82F6;
    color: white;
}
QPushButton#addBtn:hover { background-color: #2E6FDB; }
QPushButton#deleteBtn {
    background-color: #EF4444;
    color: white;
}
QPushButton#deleteBtn:hover { background-color: #D93A3A; }
QPushButton#saveBtn {
    background-color: #22C55E;
    color: white;
}
QPushButton#saveBtn:hover { background-color: #1CAA4E; }
QPushButton#searchBtn {
    background-color: #4F5DFF;
    color: white;
}
QPushButton#searchBtn:hover { background-color: #3E4CE0; }
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
    background: #FFFFFF;
    border: 1px solid #D3D8ED;
    border-radius: 5px;
    padding: 4px 6px;
    min-height: 22px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border: 1px solid #4F5DFF;
}
QLabel#countLabel {
    color: #4F5DFF;
    font-weight: 700;
}
QStatusBar {
    background: #2E3352;
    color: #FFFFFF;
}
"""


def sql_escape(text):
    return text.replace("'", "''")


def fetch_id_label_pairs(table, id_col, label_expr):
    query = QSqlQuery(f"SELECT {id_col}, {label_expr} FROM {table} ORDER BY {id_col}")
    pairs = []
    while query.next():
        pairs.append((query.value(0), query.value(1)))
    return pairs


def table_row_count(table, where_clause=""):
    sql = f"SELECT COUNT(*) FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    query = QSqlQuery(sql)
    query.next()
    return query.value(0)


def populate_lookup_combo(combo, pairs, all_label="전체"):
    current_data = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    combo.addItem(all_label, None)
    for item_id, label in pairs:
        combo.addItem(f"{item_id} - {label}", item_id)
    pos = combo.findData(current_data)
    combo.setCurrentIndex(pos if pos >= 0 else 0)
    combo.blockSignals(False)


class ComboBoxDelegate(QStyledItemDelegate):
    """Foreign-key 컬럼을 'ID - 표시이름' 콤보박스로 편집할 수 있게 해주는 델리게이트.

    id -> label 매핑을 캐시해두고 refresh_cache()로만 다시 조회한다.
    (매 셀 렌더링마다 DB를 조회하면 대량 데이터에서 매우 느려지기 때문)
    """

    def __init__(self, id_label_pairs_provider, parent=None):
        super().__init__(parent)
        self._provider = id_label_pairs_provider
        self._cache = {}
        self.refresh_cache()

    def refresh_cache(self):
        self._cache = dict(self._provider())

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        for item_id, label in self._cache.items():
            combo.addItem(f"{item_id} - {label}", item_id)
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = combo.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        return combo

    def setEditorData(self, editor, index):
        current_id = index.model().data(index, Qt.ItemDataRole.EditRole)
        pos = editor.findData(current_id)
        editor.setCurrentIndex(pos if pos >= 0 else 0)

    def setModelData(self, editor, model, index):
        data = editor.currentData()
        if data is None:
            pos = editor.findText(editor.currentText())
            data = editor.itemData(pos) if pos >= 0 else None
        if data is not None:
            model.setData(index, data, Qt.ItemDataRole.EditRole)

    def displayText(self, value, locale):
        label = self._cache.get(value)
        return f"{value} - {label}" if label is not None else str(value)


class DateEditDelegate(QStyledItemDelegate):
    """OrderDate 컬럼을 달력 팝업이 있는 QDateEdit으로 편집하기 위한 델리게이트."""

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("yyyy-MM-dd")
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.ItemDataRole.EditRole)
        date = QDate.fromString(text, "yyyy-MM-dd") if text else QDate.currentDate()
        editor.setDate(date if date.isValid() else QDate.currentDate())

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date().toString("yyyy-MM-dd"), Qt.ItemDataRole.EditRole)


# ---------------------------------------------------------------------------
# 검색 조건(필터) 패널: 테이블별로 다양한 조건을 조합해서 검색할 수 있게 한다.
# 각 패널은 get_where() -> SQL WHERE 절 문자열, reset() -> 조건 초기화를 제공한다.
# ---------------------------------------------------------------------------


class CustomerFilterPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("검색 조건", parent)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("예: 김민준")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("예: example.com")

        form = QHBoxLayout(self)
        form.addWidget(QLabel("성명"))
        form.addWidget(self.name_edit)
        form.addWidget(QLabel("이메일"))
        form.addWidget(self.email_edit)
        form.addStretch()

    def get_where(self):
        conditions = []
        if self.name_edit.text().strip():
            conditions.append(f"(LastName || FirstName) LIKE '%{sql_escape(self.name_edit.text().strip())}%'")
        if self.email_edit.text().strip():
            conditions.append(f"Email LIKE '%{sql_escape(self.email_edit.text().strip())}%'")
        return " AND ".join(conditions)

    def reset(self):
        self.name_edit.clear()
        self.email_edit.clear()

    def refresh_lookups(self):
        pass


class ProductFilterPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("검색 조건", parent)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("예: 이어폰")

        self.price_min = QDoubleSpinBox()
        self.price_max = QDoubleSpinBox()
        for box in (self.price_min, self.price_max):
            box.setRange(0, 1_000_000)
            box.setDecimals(0)
            box.setSingleStep(1000)
            box.setSuffix(" 원")
        self.price_max.setValue(1_000_000)

        self.stock_min = QSpinBox()
        self.stock_max = QSpinBox()
        for box in (self.stock_min, self.stock_max):
            box.setRange(0, 1000)
        self.stock_max.setValue(1000)

        form = QHBoxLayout(self)
        form.addWidget(QLabel("제품명"))
        form.addWidget(self.name_edit)
        form.addWidget(QLabel("가격"))
        form.addWidget(self.price_min)
        form.addWidget(QLabel("~"))
        form.addWidget(self.price_max)
        form.addWidget(QLabel("재고"))
        form.addWidget(self.stock_min)
        form.addWidget(QLabel("~"))
        form.addWidget(self.stock_max)
        form.addStretch()

    def get_where(self):
        conditions = [
            f"UnitPrice BETWEEN {self.price_min.value()} AND {self.price_max.value()}",
            f"UnitsInStock BETWEEN {self.stock_min.value()} AND {self.stock_max.value()}",
        ]
        if self.name_edit.text().strip():
            conditions.append(f"ProductName LIKE '%{sql_escape(self.name_edit.text().strip())}%'")
        return " AND ".join(conditions)

    def reset(self):
        self.name_edit.clear()
        self.price_min.setValue(0)
        self.price_max.setValue(1_000_000)
        self.stock_min.setValue(0)
        self.stock_max.setValue(1000)

    def refresh_lookups(self):
        pass


class OrderFilterPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("검색 조건", parent)
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(160)

        self.date_from = QDateEdit(QDate(2023, 1, 1))
        self.date_to = QDateEdit(QDate(2025, 12, 31))
        for box in (self.date_from, self.date_to):
            box.setCalendarPopup(True)
            box.setDisplayFormat("yyyy-MM-dd")

        self.amount_min = QSpinBox()
        self.amount_max = QSpinBox()
        for box in (self.amount_min, self.amount_max):
            box.setRange(0, 100_000)
            box.setSingleStep(1000)
            box.setSuffix(" 원")
        self.amount_max.setValue(100_000)

        form = QHBoxLayout(self)
        form.addWidget(QLabel("고객"))
        form.addWidget(self.customer_combo)
        form.addWidget(QLabel("주문일"))
        form.addWidget(self.date_from)
        form.addWidget(QLabel("~"))
        form.addWidget(self.date_to)
        form.addWidget(QLabel("금액"))
        form.addWidget(self.amount_min)
        form.addWidget(QLabel("~"))
        form.addWidget(self.amount_max)
        form.addStretch()

        self.refresh_lookups()

    def get_where(self):
        conditions = [
            f"OrderDate BETWEEN '{self.date_from.date().toString('yyyy-MM-dd')}' "
            f"AND '{self.date_to.date().toString('yyyy-MM-dd')}'",
            f"TotalAmount BETWEEN {self.amount_min.value()} AND {self.amount_max.value()}",
        ]
        customer_id = self.customer_combo.currentData()
        if customer_id is not None:
            conditions.append(f"CustomerID = {customer_id}")
        return " AND ".join(conditions)

    def reset(self):
        self.customer_combo.setCurrentIndex(0)
        self.date_from.setDate(QDate(2023, 1, 1))
        self.date_to.setDate(QDate(2025, 12, 31))
        self.amount_min.setValue(0)
        self.amount_max.setValue(100_000)

    def refresh_lookups(self):
        pairs = fetch_id_label_pairs("Customers", "CustomerID", "LastName || FirstName")
        populate_lookup_combo(self.customer_combo, pairs)


class OrderDetailFilterPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("검색 조건", parent)
        self.order_id_spin = QSpinBox()
        self.order_id_spin.setRange(0, 999_999)
        self.order_id_spin.setSpecialValueText("전체")

        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(180)

        self.qty_min = QSpinBox()
        self.qty_max = QSpinBox()
        for box in (self.qty_min, self.qty_max):
            box.setRange(0, 100)
        self.qty_max.setValue(100)

        form = QHBoxLayout(self)
        form.addWidget(QLabel("주문번호"))
        form.addWidget(self.order_id_spin)
        form.addWidget(QLabel("제품"))
        form.addWidget(self.product_combo)
        form.addWidget(QLabel("수량"))
        form.addWidget(self.qty_min)
        form.addWidget(QLabel("~"))
        form.addWidget(self.qty_max)
        form.addStretch()

        self.refresh_lookups()

    def get_where(self):
        conditions = [f"Quantity BETWEEN {self.qty_min.value()} AND {self.qty_max.value()}"]
        if self.order_id_spin.value() > 0:
            conditions.append(f"OrderID = {self.order_id_spin.value()}")
        product_id = self.product_combo.currentData()
        if product_id is not None:
            conditions.append(f"ProductID = {product_id}")
        return " AND ".join(conditions)

    def reset(self):
        self.order_id_spin.setValue(0)
        self.product_combo.setCurrentIndex(0)
        self.qty_min.setValue(0)
        self.qty_max.setValue(100)

    def refresh_lookups(self):
        pairs = fetch_id_label_pairs("Products", "ProductID", "ProductName")
        populate_lookup_combo(self.product_combo, pairs)


class TableTab(QWidget):
    """QSqlTableModel 하나를 조회/추가/삭제/저장/검색할 수 있는 공용 탭 위젯."""

    def __init__(self, table_name, filter_panel=None, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.filter_panel = filter_panel

        self.model = QSqlTableModel(self)
        self.model.setTable(table_name)
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.model.select()

        self.view = QTableView(self)
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.view.verticalHeader().setVisible(False)

        add_btn = QPushButton("추가")
        add_btn.setObjectName("addBtn")
        delete_btn = QPushButton("삭제")
        delete_btn.setObjectName("deleteBtn")
        save_btn = QPushButton("저장")
        save_btn.setObjectName("saveBtn")
        refresh_btn = QPushButton("새로고침")
        add_btn.clicked.connect(self.add_row)
        delete_btn.clicked.connect(self.delete_selected_rows)
        save_btn.clicked.connect(self.save_changes)
        refresh_btn.clicked.connect(self.refresh)

        self.count_label = QLabel()
        self.count_label.setObjectName("countLabel")

        toolbar = QHBoxLayout()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(save_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.count_label)

        layout = QVBoxLayout(self)
        if filter_panel is not None:
            search_btn = QPushButton("검색")
            search_btn.setObjectName("searchBtn")
            reset_btn = QPushButton("초기화")
            search_btn.clicked.connect(self.apply_filter)
            reset_btn.clicked.connect(self.reset_filter)

            filter_row = QHBoxLayout()
            filter_row.addWidget(filter_panel, stretch=1)
            btn_col = QVBoxLayout()
            btn_col.addWidget(search_btn)
            btn_col.addWidget(reset_btn)
            filter_row.addLayout(btn_col)
            layout.addLayout(filter_row)

        layout.addLayout(toolbar)
        layout.addWidget(self.view)

        self.update_count()

    def add_row(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        index = self.model.index(row, 1 if self.model.columnCount() > 1 else 0)
        self.view.setCurrentIndex(index)
        self.view.edit(index)

    def delete_selected_rows(self):
        rows = sorted({idx.row() for idx in self.view.selectionModel().selectedRows()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "안내", "삭제할 행을 선택하세요.")
            return
        for row in rows:
            self.model.removeRow(row)
        if not self.model.submitAll():
            QMessageBox.warning(self, "삭제 실패", self.model.lastError().text())
            self.model.revertAll()
        self.update_count()

    def save_changes(self):
        if not self.model.submitAll():
            QMessageBox.warning(self, "저장 실패", self.model.lastError().text())
            self.model.revertAll()
        else:
            QMessageBox.information(self, "저장 완료", "변경 사항이 저장되었습니다.")
        self.update_count()

    def refresh(self):
        self.model.revertAll()
        self.model.select()
        self.update_count()

    def apply_filter(self):
        where_clause = self.filter_panel.get_where() if self.filter_panel else ""
        self.model.setFilter(where_clause)
        self.model.select()
        self.update_count()

    def reset_filter(self):
        if self.filter_panel:
            self.filter_panel.reset()
        self.apply_filter()

    def update_count(self):
        count = table_row_count(self.table_name, self.model.filter())
        self.count_label.setText(f"검색 결과: {count:,}건")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("판매 데이터 관리 시스템")
        self.resize(1250, 750)

        tabs = QTabWidget(self)
        self.setCentralWidget(tabs)
        self.setStatusBar(QStatusBar(self))

        self.customer_filter = CustomerFilterPanel()
        self.product_filter = ProductFilterPanel()
        self.order_filter = OrderFilterPanel()
        self.order_detail_filter = OrderDetailFilterPanel()

        self.customers_tab = TableTab("Customers", self.customer_filter)
        self.products_tab = TableTab("Products", self.product_filter)
        self.orders_tab = TableTab("Orders", self.order_filter)
        self.order_details_tab = TableTab("OrderDetails", self.order_detail_filter)

        customer_delegate = ComboBoxDelegate(
            lambda: fetch_id_label_pairs("Customers", "CustomerID", "LastName || FirstName"),
            self.orders_tab,
        )
        self.orders_tab.view.setItemDelegateForColumn(
            self.orders_tab.model.fieldIndex("CustomerID"), customer_delegate
        )
        self.orders_tab.view.setItemDelegateForColumn(
            self.orders_tab.model.fieldIndex("OrderDate"), DateEditDelegate(self.orders_tab)
        )

        order_delegate = ComboBoxDelegate(
            lambda: fetch_id_label_pairs("Orders", "OrderID", "OrderDate"),
            self.order_details_tab,
        )
        self.order_details_tab.view.setItemDelegateForColumn(
            self.order_details_tab.model.fieldIndex("OrderID"), order_delegate
        )
        product_delegate = ComboBoxDelegate(
            lambda: fetch_id_label_pairs("Products", "ProductID", "ProductName"),
            self.order_details_tab,
        )
        self.order_details_tab.view.setItemDelegateForColumn(
            self.order_details_tab.model.fieldIndex("ProductID"), product_delegate
        )
        self._fk_delegates = [customer_delegate, order_delegate, product_delegate]
        self._filter_panels = [
            self.customer_filter,
            self.product_filter,
            self.order_filter,
            self.order_detail_filter,
        ]

        tabs.addTab(self.customers_tab, "고객 관리")
        tabs.addTab(self.products_tab, "제품 관리")
        tabs.addTab(self.orders_tab, "주문 관리")
        tabs.addTab(self.order_details_tab, "주문 상세 관리")

        tabs.currentChanged.connect(self.on_tab_changed)
        self.on_tab_changed(0)

    def on_tab_changed(self, index):
        for delegate in self._fk_delegates:
            delegate.refresh_cache()
        for panel in self._filter_panels:
            panel.refresh_lookups()
        counts = [
            ("고객", table_row_count("Customers")),
            ("제품", table_row_count("Products")),
            ("주문", table_row_count("Orders")),
            ("주문상세", table_row_count("OrderDetails")),
        ]
        summary = "  |  ".join(f"{name} 전체 {count:,}건" for name, count in counts)
        self.statusBar().showMessage(summary)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Apple SD Gothic Neo", 10))

    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(str(DB_PATH))
    if not db.open():
        QMessageBox.critical(None, "DB 연결 실패", db.lastError().text())
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
