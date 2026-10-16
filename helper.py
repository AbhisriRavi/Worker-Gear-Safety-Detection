import cv2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def create_video_writer(video_cap, output_filename):
    # Get the frame width, height, and FPS for the output video file
    frame_width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video_cap.get(cv2.CAP_PROP_FPS))
    
    # Specify the codec for video writing
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')  # Use MP4V codec for MP4 format
    
    # Create a VideoWriter object to save the video
    writer = cv2.VideoWriter(output_filename, fourcc, fps, (frame_width, frame_height))
    
    return writer

def send_summary_email(summary, recipient_email):
    try:
        sender_email = "abhisriravib1@gmail.com"
        sender_password = "projectbatch1"


        subject = "Worker Safety Detection Summary"
        body = "Here is the detection summary:\n\n" + "\n".join([f"{k}: {v}" for k, v in summary.items()])

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
