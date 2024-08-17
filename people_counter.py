# people_counter.py
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import cv2
import numpy as np

class PeopleCounter:
    def __init__(self):
        self.model = YOLO('yolov8s.pt')
        self.tracker = DeepSort(max_age=30)
        self.in_count = 0
        self.out_count = 0
        self.counting_line = None
        self.tracked_paths = {}

    def set_counting_line(self, frame_height):
        self.counting_line = frame_height // 2

    def detect_and_track(self, frame):
        if self.counting_line is None:
            self.set_counting_line(frame.shape[0])

        results = self.model(frame, classes=0)  # 0 is the class for person
        detections = []

        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            confidences = r.boxes.conf.cpu().numpy()
            
            for box, conf in zip(boxes, confidences):
                x1, y1, x2, y2 = box
                detections.append(([x1, y1, x2 - x1, y2 - y1], conf, 'person'))

        tracks = self.tracker.update_tracks(detections, frame=frame)

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()
            
            center_y = (ltrb[1] + ltrb[3]) / 2

            if track_id not in self.tracked_paths:
                self.tracked_paths[track_id] = []
            self.tracked_paths[track_id].append(center_y)

            if len(self.tracked_paths[track_id]) >= 2:
                prev_y = self.tracked_paths[track_id][-2]
                curr_y = self.tracked_paths[track_id][-1]

                if prev_y < self.counting_line and curr_y >= self.counting_line:
                    self.in_count += 1
                elif prev_y > self.counting_line and curr_y <= self.counting_line:
                    self.out_count += 1

            cv2.rectangle(frame, (int(ltrb[0]), int(ltrb[1])), (int(ltrb[2]), int(ltrb[3])), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {track_id}", (int(ltrb[0]), int(ltrb[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.line(frame, (0, self.counting_line), (frame.shape[1], self.counting_line), (0, 0, 255), 2)
        cv2.putText(frame, f"In: {self.in_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Out: {self.out_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Current: {self.in_count - self.out_count}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return frame, self.in_count, self.out_count