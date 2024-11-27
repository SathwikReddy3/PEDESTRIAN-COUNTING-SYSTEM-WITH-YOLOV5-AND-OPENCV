import tkinter as tk
from tkinter import filedialog, Label, Button
import cv2
import threading
import torch
from collections import deque

# Load the YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

# Global variables
video_path = None
stop_flag = False
pedestrian_class_id = 0  # COCO dataset "person" class ID
object_tracker = {}  # Track objects by unique IDs
next_object_id = 0  # Incremental object ID counter

# Function to process video or webcam feed
def process_video(source, is_webcam=False):
    global stop_flag, object_tracker, next_object_id
    stop_flag = False
    total_pedestrians = 0
    object_tracker = {}
    next_object_id = 0

    # Open video source
    video_stream = cv2.VideoCapture(source)
    if not video_stream.isOpened():
        result_label.config(text="Error: Could not open video source.")
        return

    while not stop_flag:
        ret, frame = video_stream.read()
        if not ret:
            break

        # Resize the frame for consistent performance
        frame_resized = cv2.resize(frame, (640, 360))

        # Run YOLO detection
        results = model(frame_resized)
        pedestrians = [box for box in results.xyxy[0] if int(box[5]) == pedestrian_class_id]

        # Update tracked objects
        for *xyxy, conf, cls in pedestrians:
            x1, y1, x2, y2 = map(int, xyxy)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

            # Check if this pedestrian is new
            match_found = False
            for obj_id, track in object_tracker.items():
                prev_x, prev_y = track[-1]
                if abs(center_x - prev_x) < 50 and abs(center_y - prev_y) < 50:
                    object_tracker[obj_id].append((center_x, center_y))
                    match_found = True
                    break

            if not match_found:
                object_tracker[next_object_id] = deque(maxlen=30)
                object_tracker[next_object_id].append((center_x, center_y))
                total_pedestrians += 1
                next_object_id += 1

            # Draw bounding boxes around detected pedestrians
            label = f"Person {conf:.2f}"
            cv2.rectangle(frame_resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_resized, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Show the frame with bounding boxes
        window_name = "Pedestrian Detection (Webcam)" if is_webcam else "Pedestrian Detection (Video)"
        cv2.imshow(window_name, frame_resized)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_stream.release()
    cv2.destroyAllWindows()

    # Update the result label
    mode = "Webcam" if is_webcam else "Video"
    result_label.config(text=f"Total Pedestrians Detected: {total_pedestrians} ({mode})")

# Function to stop the detection
def stop_detection():
    global stop_flag
    stop_flag = True

# Function to start webcam detection
def start_webcam():
    threading.Thread(target=process_video, args=(0, True)).start()

# Function to upload and process video
def upload_video():
    global video_path
    video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if video_path:
        threading.Thread(target=process_video, args=(video_path, False)).start()
    else:
        result_label.config(text="No video selected.")

# Function to reset the counter and trackers
def reset_counter():
    global object_tracker, next_object_id
    object_tracker = {}
    next_object_id = 0
    result_label.config(text="Counter reset successfully!")

# Create the main window
root = tk.Tk()
root.title("Pedestrian Counter")
root.geometry("600x600")

# UI Elements
Label(root, text="Pedestrian Counter", font=("Arial", 24, "bold"), fg="black").pack(pady=20)

start_button = Button(root, text="Start Webcam", bg="green", fg="white", command=start_webcam)
start_button.pack(pady=5)

upload_button = Button(root, text="Upload Video", bg="blue", fg="white", command=upload_video)
upload_button.pack(pady=5)

count_button = Button(root, text="Count", bg="orange", fg="white", command=lambda: result_label.config(text="Counting pedestrians..."))
count_button.pack(pady=5)

stop_webcam_button = Button(root, text="Stop Webcam", bg="red", fg="white", command=stop_detection)
stop_webcam_button.pack(pady=5)

reset_button = Button(root, text="Reset Counter", bg="purple", fg="white", command=reset_counter)
reset_button.pack(pady=5)

stop_video_button = Button(root, text="Stop Video", bg="gray", fg="white", command=stop_detection)
stop_video_button.pack(pady=5)

close_button = Button(root, text="Close", bg="black", fg="white", command=root.quit)
close_button.pack(pady=5)

result_label = Label(root, text="Welcome to Pedestrian Counter", font=("Arial", 14), fg="black")
result_label.pack(pady=10)

# Run the Tkinter main loop
root.mainloop()