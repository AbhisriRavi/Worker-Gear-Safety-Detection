import os
import streamlit as st
from ultralytics import YOLO
import cv2
import math
from helper import create_video_writer, send_summary_email

# Make sure working folders exist
os.makedirs("temp", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Initialize YOLO model
model = YOLO("best.pt")

# Class Names
classNames = ['Excavator', 'Gloves', 'Hardhat', 'Ladder', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest',
              'Person', 'SUV', 'Safety Cone', 'Safety Vest', 'bus', 'dump truck', 'fire hydrant', 'machinery',
              'mini-van', 'sedan', 'semi', 'trailer', 'truck and trailer', 'truck', 'van', 'vehicle', 'wheel loader']

# Helper functions
def detect_and_annotate_image(input_path, output_path):
    img = cv2.imread(input_path)
    results = model(img)
    summary = generate_summary(results)
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cls = int(box.cls[0])
            currentClass = classNames[cls]
            conf = math.ceil((box.conf[0] * 100)) / 100
            if conf > 0.5:
                color = (0, 0, 255) if "NO-" in currentClass else (0, 255, 0)
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                cv2.putText(img, currentClass, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imwrite(output_path, img)
    return summary

def detect_and_annotate_video(input_path, output_folder):
    cap = cv2.VideoCapture(input_path)
    model = YOLO("best.pt")
    
    classNames = ['Excavator', 'Gloves', 'Hardhat', 'Ladder', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest',
                  'Person', 'SUV', 'Safety Cone', 'Safety Vest', 'bus', 'dump truck', 'fire hydrant', 'machinery',
                  'mini-van', 'sedan', 'semi', 'trailer', 'truck and trailer', 'truck', 'van', 'vehicle', 'wheel loader']
    
    myColor = (0, 0, 255)
    frame_count = 0  # To track the first 30 frames
    
    os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists

    summary = {}  # Initialize the summary dictionary
    
    while frame_count < 30:
        success, img = cap.read()
        if not success:
            break
        frame_count += 1
        
        results = model(img, stream=True)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])
                currentClass = classNames[cls]
                if conf > 0.5:
                    if currentClass == 'NO-Hardhat' or currentClass == 'NO-Safety Vest' or currentClass == "NO-Mask":
                        myColor = (0, 0, 255)
                    elif currentClass == 'Hardhat' or currentClass == 'Safety Vest' or currentClass == "Mask":
                        myColor = (0, 255, 0)
                    else:
                        myColor = (255, 0, 0)
                    img = cv2.putText(img, f'{classNames[cls]}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX,
                                      1, (255, 0, 0), 2, cv2.LINE_AA)
                    cv2.rectangle(img, (x1, y1), (x2, y2), myColor, 3)
                    
                    # Update the summary
                    summary[currentClass] = summary.get(currentClass, 0) + 1

        # Save the annotated frame
        output_path = os.path.join(output_folder, f"frame_{frame_count}.jpg")
        cv2.imwrite(output_path, img)

    cap.release()
    return summary  # Return the summary


def generate_summary(results):
    summary = {}
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            currentClass = classNames[cls]
            summary[currentClass] = summary.get(currentClass, 0) + 1
    return summary

# Streamlit App
st.title("Worker Safety Detection System")

interface = st.sidebar.selectbox("Choose Interface", ["Normal Interface", "Admin Dashboard"])

if interface == "Normal Interface":
    upload_type = st.selectbox("Upload Type", ["Image", "Video"])
    uploaded_file = st.file_uploader(f"Upload a {upload_type}")
    
    if uploaded_file is not None:
        input_path = f"temp/{uploaded_file.name}"
        output_path = f"output/{uploaded_file.name}"
        
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if upload_type == "Image":
            summary = detect_and_annotate_image(input_path, output_path)
        else:
            summary = detect_and_annotate_video(input_path, output_path)
        
        st.session_state["output_file"] = output_path
        st.session_state["summary"] = summary
        st.success("Detection completed! Switch to the Admin Dashboard.")

elif interface == "Admin Dashboard":
    if "output_file" in st.session_state:
        output_file = st.session_state["output_file"]
        summary = st.session_state["summary"]
        
        # Check if the uploaded file is an image
        if not output_file.endswith(".mp4"):
            # Display the image output
            st.image(output_file)
        else:
            # Video was uploaded, show all frames stored in the output folder
            video_name = os.path.splitext(os.path.basename(output_file))[0]  # Extract the video name without extension
            video_name += ".mp4"
            video_folder = os.path.join("output", video_name)  # Folder for frames named after the video
            
            if os.path.exists(video_folder):
                # Get the list of all images (frames) stored in the video folder
                frame_files = sorted([f for f in os.listdir(video_folder) if f.endswith(('.jpg', '.png', '.jpeg'))])
                
                # Button to display all frames
                display_video_button = st.button("Show Output Video Frames")
                if display_video_button:
                    # Display each frame image in the video folder
                    for frame_file in frame_files:
                        frame_path = os.path.join(video_folder, frame_file)
                        st.image(frame_path, caption=f"Frame: {frame_file}", use_column_width=True)

            else:
                st.error("Output folder not found or no frames generated for the video.")
        
        st.subheader("Detection Summary")
        for item, count in summary.items():
            if output_file.endswith(".mp4"):
                count //= 30
            st.write(f"{item}: {count}")
        
        # Send summary email
        # email_sent = send_summary_email(summary, "akshayayencharla@gmail.com")
        # if email_sent:
        #     st.success("Summary sent to admin email.")
        # else:
        #     st.error("Failed to send email.")
    else:
        st.write("No output file found. Please upload a file in the Normal Interface.")