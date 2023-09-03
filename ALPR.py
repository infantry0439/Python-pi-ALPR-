import cv2
import os
from openalpr import Alpr
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime

# Initialize the OpenALPR object
alpr = Alpr("us", "/etc/openalpr/openalpr.conf", "/usr/share/openalpr/runtime_data")

# Initialize the Raspberry Pi camera
camera = cv2.VideoCapture(0)

# Create a directory to store vehicle images
if not os.path.exists("vehicle_images"):
    os.mkdir("vehicle_images")

# Email configuration
sender_email = "your_email@gmail.com"
sender_password = "your_password"
receiver_email = "recipient@example.com"
subject = "Vehicle Log Report"
body = "Please find attached the vehicle log report."

# Create an email message
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject
msg.attach(MIMEText(body, "plain"))

# Continuously capture frames from the camera
while True:
    # Read a frame from the camera
    ret, frame = camera.read()

    # Check if the frame was successfully captured
    if not ret:
        print("Error: failed to capture frame from camera")
        break

    # Perform license plate recognition on the frame
    results = alpr.recognize_ndarray(frame)

    # Process recognition results
    for result in results["results"]:
        for candidate in result["candidates"]:
            plate = candidate["plate"]
            confidence = candidate["confidence"]

            # Save the vehicle image with timestamp as the filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_filename = f"vehicle_images/{timestamp}.jpg"
            cv2.imwrite(image_filename, frame)

            # Create or append to the log file
            log_filename = "vehicle_log.txt"
            with open(log_filename, "a") as log_file:
                log_entry = f"Plate: {plate}, Confidence: {confidence}, Timestamp: {timestamp}, Image: {image_filename}\n"
                log_file.write(log_entry)

            # Print the results
            print(f"License plate: {plate}, Confidence: {confidence}")

    # Display the frame
    cv2.imshow("License Plate Scanner", frame)

    # Wait for a key press
    key = cv2.waitKey(1) & 0xFF

    # If the 'q' key was pressed, quit the loop
    if key == ord("q"):
        break

# Release the camera and cleanup
camera.release()
cv2.destroyAllWindows()
alpr.unload()

# Attach the log file to the email
with open(log_filename, "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename= {log_filename}")

msg.attach(part)

# Send the email
try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()
    print("Email sent successfully")
except Exception as e:
    print(f"Email could not be sent: {str(e)}")
