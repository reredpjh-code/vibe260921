import base64
import mimetypes
import os
import sys

from openai import OpenAI
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

AVAILABLE_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "gpt-5-mini", "gpt-5"]
DEFAULT_MODEL = AVAILABLE_MODELS[0]
DEFAULT_PROMPT = "이 사진에 무엇이 보이는지 한국어로 자세히 설명해줘."


def encode_image_to_data_url(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/png"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


class AnalysisWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key: str, image_path: str, prompt: str, model: str = DEFAULT_MODEL):
        super().__init__()
        self._api_key = api_key
        self._image_path = image_path
        self._prompt = prompt
        self._model = model

    def run(self):
        try:
            client = OpenAI(api_key=self._api_key)
            data_url = encode_image_to_data_url(self._image_path)

            kwargs = {}
            if self._model.startswith(("gpt-5", "o1", "o3", "o4")):
                # 추론 모델은 max_completion_tokens 예산을 내부 추론 토큰과
                # 함께 소비하므로, 추론 강도를 낮춰 답변에 쓸 토큰을 확보한다.
                kwargs["reasoning_effort"] = "low"

            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self._prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                max_completion_tokens=2000,
                **kwargs,
            )
            choice = response.choices[0]
            content = choice.message.content
            if not content:
                content = f"(응답 내용이 비어 있습니다. finish_reason: {choice.finish_reason})"
            self.finished.emit(content)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이미지 분석기 (OpenAI Vision)")
        self.resize(720, 640)

        self._image_path: str | None = None
        self._worker: AnalysisWorker | None = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        api_key_row = QHBoxLayout()
        api_key_row.addWidget(QLabel("OpenAI API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        self.api_key_input.setText(os.environ.get("OPENAI_API_KEY", ""))
        api_key_row.addWidget(self.api_key_input)
        layout.addLayout(api_key_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("모델:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setCurrentText(DEFAULT_MODEL)
        model_row.addWidget(self.model_combo)
        layout.addLayout(model_row)

        prompt_row = QHBoxLayout()
        prompt_row.addWidget(QLabel("질문:"))
        self.prompt_input = QLineEdit(DEFAULT_PROMPT)
        prompt_row.addWidget(self.prompt_input)
        layout.addLayout(prompt_row)

        self.image_label = QLabel("업로드된 이미지가 여기에 표시됩니다.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(320)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #fafafa;")
        layout.addWidget(self.image_label)

        button_row = QHBoxLayout()
        self.upload_button = QPushButton("이미지 업로드")
        self.upload_button.clicked.connect(self._select_image)
        button_row.addWidget(self.upload_button)

        self.analyze_button = QPushButton("분석하기")
        self.analyze_button.clicked.connect(self._analyze)
        self.analyze_button.setEnabled(False)
        button_row.addWidget(self.analyze_button)
        layout.addLayout(button_row)

        layout.addWidget(QLabel("분석 결과:"))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "이미지 선택",
            "",
            "이미지 파일 (*.png *.jpg *.jpeg *.gif *.webp *.bmp)",
        )
        if not path:
            return

        self._image_path = path
        pixmap = QPixmap(path)
        scaled = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.analyze_button.setEnabled(True)
        self.result_text.clear()

    def _analyze(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "API Key 필요", "OpenAI API Key를 입력해주세요.")
            return
        if not self._image_path:
            QMessageBox.warning(self, "이미지 필요", "먼저 이미지를 업로드해주세요.")
            return

        prompt = self.prompt_input.text().strip() or DEFAULT_PROMPT
        model = self.model_combo.currentText().strip() or DEFAULT_MODEL

        self.analyze_button.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.result_text.setPlainText("분석 중입니다...")

        self._worker = AnalysisWorker(api_key, self._image_path, prompt, model)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_finished(self, content: str):
        self.result_text.setPlainText(content)
        self.analyze_button.setEnabled(True)
        self.upload_button.setEnabled(True)

    def _on_analysis_error(self, message: str):
        self.result_text.clear()
        QMessageBox.critical(self, "분석 실패", f"이미지 분석 중 오류가 발생했습니다:\n{message}")
        self.analyze_button.setEnabled(True)
        self.upload_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
