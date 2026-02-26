# file safeshield/frontend/sscv-desktop-app/widgets/webcam_widget.py

import onnxruntime as onnxrt
print(f"[WEBCAM DEBUG]: {onnxrt.get_device()}")  # should print "CPU"
import sys
from pathlib import Path
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from datetime import datetime

# yolo detector with ONNX
# src 1: https://github.com/ultralytics/ultralytics/blob/main/examples/RTDETR-ONNXRuntime-Python/main.py
# src 2: https://onnxruntime.ai/docs/api/python/api_summary.html
# src 3: https://docs.ultralytics.com/modes/predict/#inference-sources

# 1. Detector
class SSCV_YOLOONNXDetector:
    """
    Class to preprocess DL object detection 
    """
    def __init__(self, model_path, conf_threshold=0.45):
        # to avoid: ImportError: DLL load failed while importing onnxruntime_pybind11_state: A dynamic link library (DLL) initialization routine failed.
        self.conf_threshold = conf_threshold

        try:
            # optimization for CPU inference
            options = onnxrt.SessionOptions()
            options.intra_op_num_threads = 4 # Adjust based on CPU cores
            options.graph_optimization_level = onnxrt.GraphOptimizationLevel.ORT_ENABLE_ALL
            # load model
            self.session = onnxrt.InferenceSession(
                model_path, sess_options=options,
                providers=['CPUExecutionProvider']
            )
            # get input, output and shape
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            input_shape = self.session.get_inputs()[0].shape
            self.input_width = input_shape[3]
            self.input_height = input_shape[2]
        except Exception as e:
            print(f"Error loading the model: {e}")
            sys.exit(1)
    

    def preprocess(self, image):
        import cv2
        """Preprocess image for YOLO inference"""
        img = cv2.resize(image, (self.input_width, self.input_height))
        # convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # normalize img
        img = img.astype(np.float32) / 255.0
        # change from hwc to chw format
        img = np.transpose(img, (2, 0, 1))
        # add batch dim
        img = np.expand_dims(img, axis=0)

        return img

    def postprocess(self, outputs, original_shape):
        import cv2
        height, width = original_shape[:2]
        boxes, confs, class_ids = [], [], []
        detections = []
        predictions = outputs[0]
        # iterate over 300 possibles detection
        for i in range(predictions.shape[1]):
            pred = predictions[0, i]
            conf = pred[4]
            if conf > self.conf_threshold:
                x1 = int(pred[0] * width / self.input_width)
                y1 = int(pred[1] * height / self.input_height)
                x2 = int(pred[2] * width / self.input_width)
                y2 = int(pred[3] * height / self.input_height)
                # convert (x1, y1, x2, y2) to (x, y, w, h) for nms boxes
                boxes.append([x1, y1, x2 - x1, y2 -y1])
                confs.append(conf)
                class_ids.append(int(pred[5]))
        if len(boxes) > 0:
            # apply nms with 0.45
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
    
    def detect(self, image):
        """Run inference on image"""
        original_shape = image.shape[:2]
        # preprocess
        input_image = self.preprocess(image)
        # run inference
        outputs = self.session.run([self.output_name], {self.input_name: input_image})
        preds = outputs[0]
        # postprocess
        detections = self.postprocess(outputs, original_shape)
        return detections
    

class WebcamProcessing(QWidget):
    """Widget class for displaying webcam feed with YOLO detection"""
    violation_detected_sgn = pyqtSignal(list, str)

    def __init__(self, model_path=None, conf_threshold=0.45):
        super().__init__()
        self.cap = None
        self.prev_time = datetime.now()
        self.timer = QTimer()
        self.is_running = False

        self.classes = ["helmet", "gloves", "vest", "boots", "goggles"]
        self.colors = [(255, 0, 0), (0, 255, 0), (0, 165, 255), (128, 128, 0), (235, 156, 48)]
        # violation logic
        self.required_ppe = {"helmet", "gloves", "vest"}
        # take the first screenshot after 15 sec when app starts
        self.app_start_time = datetime.now()
        self.warmup_duration = 15
        self.violation_start_time = None
        self.violation_saved_time = None
        # wait 10 sec before saving evidence
        self.missing_duration_required = 10
        # if ppe detected after 5 sec, cancel saving
        self.grace_period_after_save = 5
        self.violation_active = False
        # project root dir
        project_root = Path(__file__).resolve().parents[3]
        self.evidence_dir = project_root / "daily_violations" / datetime.now().strftime("%Y-%m-%d")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        # init detector only if model_path is provided
        self.detector = None
        if model_path and Path(model_path).exists():
            try:
                self.detector = SSCV_YOLOONNXDetector(model_path, conf_threshold)
            except Exception as e:
                print(f"Error initializing detector: {e}")
        else:
            # Add this else block to debug!
            print(f"CRITICAL: Model file NOT FOUND at: {model_path}")
        # setup UI and timer for updating frames
        self.setup_ui()
        self.timer.timeout.connect(self.update_frame)
    

    def setup_ui(self):
        """Set components ui"""
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background-color: black;")

        self.main_layout.addWidget(self.video_label)
        self.setLayout(self.main_layout)
    
    def start_camera(self, camera_index=0):
        import cv2

        if self.is_running:
            return
        # release previous capture if exists
        if self.cap is not None:
            self.cap.release()
        # init webcam
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            print("Error: Could not open Webcam")
            return False
        # capture frame at lower resolution to speed-up the pre-preprocessing
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.is_running = True
        # run as fast as processing allows
        self.timer.start(1)
        print("Webcam successfully started!")
        return True
    
    def update_frame(self):
        import cv2

        if self.cap is None or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if ret:
            processed_frame = self.process_frame(frame)
            # convert opencv image to QImage
            rgb_img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            # height, width, channel
            h, w, ch = rgb_img.shape
            qt_img = QImage(rgb_img.data, w, h, w * ch, QImage.Format.Format_RGB888)
            # scale image to fit label while maintining aspect ratio
            scaled_pixmap = QPixmap.fromImage(qt_img).scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
    

    def process_frame(self, frame):
        import cv2
        """Process frame with YOLO"""
        if self.detector is None:
            return frame
        
        # measure time
        now = datetime.now()
        # warm up period
        if (now - self.app_start_time).seconds < self.warmup_duration:
            cv2.putText(
                frame, "Warming up system...", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2
            )
            return frame
        #  run detection
        detections = self.detector.detect(frame)
        current_time = datetime.now()
        detected_items = set()
        # draw detections
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            class_id = detection["class_id"]
            
            if class_id >= len(self.classes):
                continue
            class_name = self.classes[class_id]
            if class_name in self.required_ppe:
                detected_items.add(class_name)
            
            color = self.colors[class_id % len(self.colors)]
            label = f"{class_name}: {detection['confidence']:.2f}"
            # draw bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            # draw label
            (text_width, text_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            # label background
            cv2.rectangle(
                frame, (x1, y1 - text_height - baseline - 10),
                (x1 + text_width, y1), color, -1
            )
            # label text
            cv2.putText(
                frame, label, (x1, y1 - baseline - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 2, cv2.LINE_AA
            )
        # check missing ppe
        missing_items = self.required_ppe - detected_items
        # send missing ppe to ui for real-time display
        if missing_items:
            # emit signal immediately for real time ui update
            self.violation_detected_sgn.emit(list(missing_items), None)
            # start violation timer
            if self.violation_start_time is None:
                self.violation_start_time = now
            
            elapsed_missing = (now - self.violation_start_time).seconds
            cv2.putText(
                frame, f"Missing: {', '.join(missing_items)}", # ({elapsed_missing})",
                (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255), 2
            )
            # save evidence if persistent
            if (elapsed_missing >= self.missing_duration_required and not self.violation_active):
                self.save_violation_evidence(frame, missing_items)
                self.violation_active = True
                self.violation_saved_time = now
        else:
            # ppe detected again
            # check grace period if violation was active
            if self.violation_active:
                # reset everything
                self.violation_active = False
                self.violation_saved_time = None
            # reset timers
            self.violation_start_time = None
        
        # estimate actual fps
        end_t = datetime.now()
        fps = 1 / (end_t - self.prev_time).total_seconds()
        self.prev_time = end_t
        # draw fps
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        return frame
    
    def closeEvent(self, event):
        """cleanup when widget is closed"""
        self.stop_camera()
        super().closeEvent()
    
    def stop_camera(self):
        """stop webcam capture"""
        if self.cap is not None:
            print("Stopping webcam stream...")
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.is_running = False
            self.video_label.clear()
            print("Webcam stopped")

    def save_violation_evidence(self, frame, missing_items):
        timestamp = datetime.now().strftime("%H%M%S")
        filename = self.evidence_dir / f"missing_{'_'.join(missing_items)}_{timestamp}.jpg"
        
        import cv2
        # use abs path
        abs_path = str(filename.absolute())
        success = cv2.imwrite(abs_path, frame)
        if success:
            # emit signal
            self.violation_detected_sgn.emit(list(missing_items), str(abs_path))
        else:
            print(f"[ERROR] Failed to save image to: {abs_path}")