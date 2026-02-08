# file safeshieldcv/notebooks/data/videos/test_model_with_video.py
# video src: https://www.freepik.com/videos/construction-ppe
# test code src: https://docs.ultralytics.com/modes/predict/#streaming-source-for-loop
import cv2
import os
from pathlib import Path
from ultralytics import YOLO

# folders
NOTEBOOKS_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = NOTEBOOKS_DIR / "outputs"
VIDEOS_DIR = NOTEBOOKS_DIR / "data" / "videos"
EXPORT_DIR = NOTEBOOKS_DIR / "exports"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)
TARGET_RESOLUTION = (1280, 720)

def main():
    model_path = MODEL_DIR / "sscv_yolo26s.pt"
    model = YOLO(str(model_path)) # Path to string

    video_path = VIDEOS_DIR / "test_ppe_vid_01.mp4"
    
    # FIX 1: Always convert pathlib objects to str for VideoCapture
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print(f"❌ ERROR: Could not open video file at {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25
    
    output_path = EXPORT_DIR / "ppe_detection_output_01.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, TARGET_RESOLUTION)

    print(f"🎬 Starting processing at {fps} FPS...")

    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            print("🏁 Reached end of video or failed to read frame.")
            break

        # FIX 2: Resize the frame BEFORE inference for consistency
        frame_resized = cv2.resize(frame, TARGET_RESOLUTION)
        
        # Inference
        results = model(frame_resized, conf=0.25, iou=0.7, verbose=False)

        # Visualize
        annotated_frame = results[0].plot()

        # Save to file
        out.write(annotated_frame)

        # Display
        cv2.imshow("SSCV PPE Detection", annotated_frame)

        # WaitKey(1) allows the UI to refresh. 'q' to quit.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Cleanup
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"✅ Saved output video to: {output_path}")

if __name__ == "__main__":
    main()