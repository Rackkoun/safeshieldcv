# file safeshield/notebooks/tests/test_model_with_webcam.py
import os
from pathlib import Path
import onnxruntime as onnxrt
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtGui import QColor, QPalette, QImage, QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from datetime import datetime

# yolo detector with ONNX
# src 1: https://github.com/ultralytics/ultralytics/blob/main/examples/RTDETR-ONNXRuntime-Python/main.py
# src 2: https://onnxruntime.ai/docs/api/python/api_summary.html
# src 3: https://docs.ultralytics.com/modes/predict/#inference-sources

# 1. Detector
class YOLO_ONNXDetector:
    def __init__(self, model_path, conf_threshold=0.45):
        self.conf_threshold = conf_threshold
        try:
            # Initialize Session
            # OPTIMIZATION: Set session options for CPU speed
            options = onnxrt.SessionOptions()
            options.intra_op_num_threads = 4 # Adjust based on CPU cores
            options.graph_optimization_level = onnxrt.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.session = onnxrt.InferenceSession(model_path, sess_options=options, providers=['CPUExecutionProvider'])
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            # Get model input dimensions (usually 640x640)
            self.input_width = self.session.get_inputs()[0].shape[3]
            self.input_height = self.session.get_inputs()[0].shape[2]
        except Exception as e:
            print(f"Error loading ONNX model: {e}")

    def detect(self, frame):
        # A. Pre-process
        img = cv2.resize(frame, (self.input_width, self.input_height))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1)) # HWC to CHW
        img = np.expand_dims(img, axis=0)  # Add batch dimension

        # B. Run Inference
        outputs = self.session.run([self.output_name], {self.input_name: img})
        predictions = outputs[0] # Shape: [1, 300, 6]
        # print(f"[DEBUG](Predictions): {predictions}")

        # C. Post-process with nms for filtering overlaps
        boxes, confs, class_ids = [], [], []
        
        h, w = frame.shape[:2]
        for i in range(predictions.shape[1]):
            pred = predictions[0, i]
            conf = pred[4]
            if conf > self.conf_threshold:
                # Scale boxes back to original frame size
                x1 = int(pred[0] * w / self.input_width)
                y1 = int(pred[1] * h / self.input_height)
                x2 = int(pred[2] * w / self.input_width)
                y2 = int(pred[3] * h / self.input_height)
                # convert [x1, y1, x2, y2] to [x, y, w, h] for nms boxes

                boxes.append([x1, y1, x2 - x1, y2 -y1])
                confs.append(conf)
                class_ids.append(int(pred[5]))
        # apply nms with 0.45 or 0.5
        detections = []
        if len(boxes) > 0:
            indices = cv2.dnn.NMSBoxes(boxes, confs, self.conf_threshold, 0.45)
            if len(indices) > 0:
                for i in indices.flatten():
                    x, y, bw, bh = boxes[i]
                    detections.append({
                        "bbox": [x, y, x+bw, y+bh],
                        "confidence": confs[i],
                        "class_id": class_ids[i]
                    })
        return detections

# 2. Webcam widget
class WebCamProcessing(QWidget):
    def __init__(self, model_path=None):
        super().__init__()
        self.cap = None
        self.prev_time = datetime.now()
        self.timer = QTimer()
        self.classes = ["helmet", "gloves", "vest", "boots", "goggles"]
        self.colors = [(255, 0, 0), (0, 255, 0), (0, 165, 255), (128, 128, 0), (235, 156, 48)]
        
        self.detector = YOLO_ONNXDetector(model_path, conf_threshold=0.5) if model_path else None
        
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.video_label)
        self.timer.timeout.connect(self.update_frame)

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        # Capture at lower resolution to speed up pre-processing if needed
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.timer.start(1) # Run as fast as processing allows
        # self.timer.start(30)
        return self.cap.isOpened()

    def stop_camera(self):
        self.timer.stop()
        if self.cap: self.cap.release()
        self.video_label.clear()

    def update_frame(self):
            
        ret, frame = self.cap.read()
        if ret:
            # mesure time
            start_t = datetime.now()
            if self.detector:
                results = self.detector.detect(frame)
                for det in results:
                    x1, y1, x2, y2 = det["bbox"]
                    color = self.colors[det["class_id"] % len(self.colors)]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    # Draw label
                    label = f"{self.classes[det['class_id']]}: {det['confidence']:.2f}"
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                    )
                    # Label background
                    cv2.rectangle(
                        frame, (x1, y1 - text_height - baseline - 10),
                        (x1 + text_width, y1), color, -1
                    )
                    cv2.putText(frame, label, 
                                (x1, y1-baseline-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                    

            # estimate actual fps
            end_t = datetime.now()
            fps = 1 / (end_t - self.prev_time).total_seconds()
            self.prev_time = end_t
            # fps
            cv2.putText( frame, f"FPS: {fps:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            # convert qimage and display
            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            qt_img = QImage(rgb_img.data, w, h, ch * w, QImage.Format.Format_RGB888)
            # Scaling is expensive; only scale if the label size is different from frame size
            pixmap = QPixmap.fromImage(qt_img)
            self.video_label.setPixmap(pixmap.scaled(
                self.video_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation # Fast is better for FPS than Smooth
            ))

# 3. Main app
class SafeShieldCV(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SafeShieldCV - PPE Monitor")
        self.resize(1280, 720)
        
        main_layout = QHBoxLayout(self)
        
        # Left Panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Controls
        ctrl_layout = QHBoxLayout()
        self.cam_btn = QPushButton("Start Camera")
        self.stop_btn = QPushButton("Stop Camera")
        self.stop_btn.setEnabled(False)
        ctrl_layout.addWidget(self.cam_btn)
        ctrl_layout.addWidget(self.stop_btn)
        
        # Video Container
        model_path = Path(__file__).resolve().parents[1] / "outputs" / "sscv_yolo26n.onnx"
        self.webcam_container = WebCamProcessing(str(model_path))
        
        left_layout.addLayout(ctrl_layout)
        left_layout.addWidget(self.webcam_container, stretch=4)
        left_layout.addWidget(QLabel("Logs Area"), stretch=1)
        
        # Right Panel (Placeholders)
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Top Stats"), stretch=1)
        right_panel.addWidget(QLabel("Violation List"), stretch=2)
        
        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addLayout(right_panel, stretch=1)

        # Signals
        self.cam_btn.clicked.connect(self.start_camera)
        self.stop_btn.clicked.connect(self.stop_camera)

    def start_camera(self):
        if self.webcam_container.start_camera():
            self.cam_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

    def stop_camera(self):
        self.webcam_container.stop_camera()
        self.cam_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

if __name__ == "__main__":
    app = QApplication([])
    window = SafeShieldCV()
    window.show()
    app.exec()