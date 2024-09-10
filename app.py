from flask import Flask, request, send_file, redirect, url_for, render_template_string, render_template, Response, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from geopy.geocoders import Nominatim
from googlesearch import search
from gtts import gTTS
import os
import uuid
import smtplib
import schedule
import time
from threading import Thread
from twilio.rest import Client
import geocoder
import cv2
import subprocess
import pandas as pd
import boto3

app = Flask(__name__)

@app.route('/sendemails', methods=['GET', 'POST'])
def send_emails():
    success_message = None
    error_message = None
    if request.method == 'POST':
        emails = request.form.get('emails').split(',')
        subject = request.form.get('subject')
        message = request.form.get('message')
        sender_email = "pranav.avlok@gmail.com"
        sender_password = "qtzi vtbd wgyu ynei"
        for email in emails:
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = email.strip()  # Strip any extra whitespace
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                text = msg.as_string()
                server.sendmail(sender_email, email.strip(), text)
                server.quit()
            except Exception as e:
                error_message = f"Error sending to {email}: {str(e)}"
                break
        else:
            success_message = "Emails sent successfully!"
    return render_template('bulk_email.html', success_message=success_message, error_message=error_message)

@app.route("/email", methods=["POST"])
def send_email():
    sender_email = request.form.get('sender_email')
    sender_password = request.form.get('sender_password')
    recipient_email = request.form.get('recipient_email')
    subject = request.form.get('subject')
    body = request.form.get('body')
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.set_content(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()
    return "Email sent successfully"
        
@app.route('/geo', methods=['GET', 'POST'])
def geo():
    latitude = None
    longitude = None
    error = None
    if request.method == 'POST':
        location_name = request.form.get('location')
        if location_name:
            geolocator = Nominatim(user_agent="my_geocoder")
            location = geolocator.geocode(location_name)
            if location:
                latitude = location.latitude
                longitude = location.longitude
            else:
                error = "Location not found"
    return render_template('geo.html', latitude=latitude, longitude=longitude, error=error)
        
@app.route("/gsearch", methods=["POST"])
def gsearch():
    query = request.form.get("query")
    r = []
    if query:
        count = 0
        for j in search(query, num_results=5):
            r.append(j)
            count += 1
            if count == 5:
                break
    return render_template("gsearch.html", results=r)

@app.route('/convert', methods=['POST'])
def convert_text_to_speech():
    text = request.form.get('text', '')
    if not text:
        return {'error': 'No text provided'}, 400
    language = 'en'
    filename = f"audio_{uuid.uuid4().hex}.mp3"
    # Generate audio file from text
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save(os.path.join('static', filename))  # Save in 'static' folder
    # Redirect to the audio playback page
    return redirect(url_for('play_audio', filename=filename))
@app.route('/play/<filename>')
def play_audio(filename):
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Playing Audio</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #2C3E50;
                    color: #ECF0F1;
                    margin: 0;
                    padding: 20px;
                    text-align: center;
                }
                audio {
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <h1>Playing Audio</h1>
            <audio controls autoplay>
                <source src="{{ url_for('static', filename=filename) }}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        </body>
        </html>
    """)

def send_email(sender_email, sender_password, recipient_email, message):
    try:
        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(sender_email, sender_password)
        s.sendmail(sender_email, recipient_email, message)
        s.quit()
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"
def schedule_email(timeinput, sender_email, sender_password, recipient_email, message):
    schedule.every().day.at(timeinput).do(lambda: send_email(sender_email, sender_password, recipient_email, message))
    while True:
        schedule.run_pending()
        time.sleep(1)
@app.route("/schedule_email", methods=["GET"])
def schedule_email_endpoint():
    sender_email = request.args.get("sender_email")
    sender_password = request.args.get("sender_password")
    recipient_email = request.args.get("recipient_email")
    message = request.args.get("message")
    timeinput = request.args.get("timeinput")
    if not all([sender_email, sender_password, recipient_email, message, timeinput]):
        return "Missing one or more required fields."
    thread = Thread(target=schedule_email, args=(timeinput, sender_email, sender_password, recipient_email, message))
    thread.start()
    return f"Email scheduled to be sent to {recipient_email} at {timeinput}."

@app.route("/sms", methods=["GET", "POST"])
def sms_():
    if request.method == "POST":
        # Get the Twilio credentials and form data from the request
        accountsid = request.form['accountsid']
        authtoken = request.form['authtoken']
        msgbody = request.form['msgbody']
        from_phno = request.form['from_phno']
        to_phno = request.form['to_phno']
        try:
            # Initialize the Twilio client
            client = Client(accountsid, authtoken)
            # Send the SMS
            message = client.messages.create(body=msgbody, from_=from_phno, to=to_phno)
            return render_template('sms.html', success="Message sent successfully!")
        except Exception as e:
            return render_template('sms.html', error=f"Failed to send message: {str(e)}")
    # Render the form when the method is GET
    return render_template('sms.html')

@app.route('/geolocation')
def geolocation():
    # Get geolocation information
    g = geocoder.ip('me')
    latitude = g.latlng[0] if g.latlng else 'Not Available'
    longitude = g.latlng[1] if g.latlng else 'Not Available'
    address = g.address if g.address else 'Not Available'
    return render_template('geonew.html', latitude=latitude, longitude=longitude, address=address)

@app.route('/camglasses')
def camglasses():
    return render_template('camglasses.html')
def gen_frames():
    cap = cv2.VideoCapture(0)
    # Load the sunglasses image with transparency channel
    glasses_img = cv2.imread("deal-with-it-glasses-png-41918.png", cv2.IMREAD_UNCHANGED)
    # Original dimensions of the sunglasses image
    original_width, original_height = 370, 267
    # Desired width for the sunglasses image
    desired_width = 200  # Adjust as needed
    # Calculate the new height to maintain aspect ratio
    aspect_ratio = original_width / original_height
    desired_height = int(desired_width / aspect_ratio)
    # Resize the sunglasses image
    glasses_img = cv2.resize(glasses_img, (desired_width, desired_height))
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Get the frame dimensions
            frame_height, frame_width = frame.shape[:2]
            # Calculate the placement coordinates to center the sunglasses
            x = (frame_width - desired_width) // 2
            # Position the sunglasses half screen above the center
            y = (frame_height // 2) - (desired_height // 2) - (frame_height // 4)  # Move up half screen
            # Define region of interest (ROI) where the glasses will be placed
            if x + desired_width <= frame_width and y + desired_height <= frame_height:
                # Create an overlay mask for transparency handling
                for c in range(0, 3):  # For RGB channels
                    frame[y:y+desired_height, x:x+desired_width, c] = glasses_img[:, :, c] * (glasses_img[:, :, 3] / 255.0) + frame[y:y+desired_height, x:x+desired_width, c] * (1.0 - glasses_img[:, :, 3] / 255.0)
            # Convert frame to JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/docker_image_pull", methods=["POST"])
def docker_img_pull():
    image = request.form.get('image')
    cmd = f"docker pull {image}"
    output = subprocess.getstatusoutput(cmd)
    if output[0] == 0:
        return jsonify({"message": "Image downloaded successfully.", "status": "success"})
    else:
        return jsonify({"message": "Image download failed.", "status": "fail"})


@app.route("/launch_docker", methods=["POST"])
def docker_launch():
    container_name = request.form.get('container_name')
    image = request.form.get('image')
    cmd = f"docker run -dit --name {container_name} {image}"
    output = subprocess.getstatusoutput(cmd)
    if output[0] == 0:
        return jsonify({"message": "Docker container launched successfully.", "status": "success", "container_id": output[1]})
    else:
        return jsonify({"message": "Failed to launch Docker container.", "status": "fail"})


@app.route("/docker_stop", methods=["POST"])
def docker_stop():
     container_name = request.form.get('container_name')
     cmd = f"docker stop {container_name}"
     output = subprocess.getstatusoutput(cmd)
     if output[0] == 0:
        return jsonify({"message": "Docker container stopped successfully.", "status": "success"})
     else:
        return jsonify({"message": "Failed to stop Docker container.", "status": "fail"})

@app.route("/docker_start", methods=["POST"])
def docker_start():
    container_name = request.form.get('container_name')
    cmd = f"docker start {container_name}"
    output = subprocess.getstatusoutput(cmd)
    if output[0] == 0:
        return jsonify({"message": "Docker container started successfully.", "status": "success"})
    else:
        return jsonify({"message": "Failed to start Docker container.", "status": "fail"})

@app.route("/docker_status", methods=["POST"])
def docker_status():
    container_name = request.form.get('container_name')
    cmd = f"docker ps -a --filter name={container_name} --format '{{{{.ID}}}} {{{{.Names}}}} {{{{.Status}}}}'"
    output = subprocess.getstatusoutput(cmd)
    if output[0] == 0:
        return jsonify({"message": output[1], "status": "success"})
    else:
        return jsonify({"message": "Failed to get Docker container status.", "status": "fail"})

@app.route("/docker_remove", methods=["POST"])
def docker_remove():
    container_name = request.form.get('container_name')
    cmd = f"docker rm {container_name}"
    output = subprocess.getstatusoutput(cmd)
    if output[0] == 0:
        return jsonify({"message": "Docker container removed successfully.", "status": "success"})
    else:
        return jsonify({"message": "Failed to remove Docker container.", "status": "fail"})

@app.route("/docker_logs", methods=["POST"])
def docker_logs():
    container_name = request.form.get('container_name')
    cmd = f"docker logs {container_name}"
    output = subprocess.getstatusoutput(cmd)
    if output[0] == 0:
        return jsonify({"message": output[1], "status": "success"})
    else:
        return jsonify({"message": "Failed to get Docker container logs.", "status": "fail"})

@app.route("/docker_image_remove", methods=["POST"])
def docker_img_remove():
    image = request.form.get('image')
    cmd = f"docker rmi -f {image}"
    output = subprocess.getstatusoutput(cmd)
    if output[0] == 0:
        return jsonify({"message": "Docker image removed successfully.", "status": "success"})
    else:
            return jsonify({"message": "Failed to remove Docker image.", "status": "fail"})

@app.route('/create_instance', methods=['POST'])
def runec2():
    
    image_id = request.form.get('image_id')
    instance_type = request.form.get('instance_type')
    num_instances = int(request.form.get('num_instances'))
    region = request.form.get('region')
    
    session = boto3.Session(region_name=region)
    ec2 = session.resource('ec2')
    def ciec2():
        instances = ec2.create_instances(
        ImageId=image_id,  
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1
        )
    for i in range(num_instances):
        ciec2()
    return 'Done'

@app.route('/terminal')
def terminal():
    return render_template('terminal.html')
@app.route('/command', methods=['POST'])
def command():
    command = request.form.get('command')
    output = subprocess.getoutput("sudo " + command)
    return output
    
#     if command.lower() == "sl":
#         return ""
#     response = process_command(command)
#     return response
# def process_command(command):
#     # Basic command processing logic
#     if command.lower() == "hello":
#         return "Hello! How can I assist you today?"
#     elif command.lower() == "date":
#         from datetime import datetime
#         return f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
#     elif command.lower() == "exit":
#         return "Exiting terminal... Goodbye!"
#     else:
#         return f"Command not recognized: {command}"

# @app.route('/s3')
# def upload_form():
#     return render_template('s3.html')
# @app.route('/upload', methods=['POST'])
# def upload_file():
#     s3 = boto3.client('s3')
#     if 'file' not in request.files:
#         return "No file part"
#     file = request.files['file']
#     if file.filename == '':
#         return "No selected file"
#     bucket_name = 'mymenuprojectbucket'
#     s3.upload_fileobj(file, bucket_name, file.filename)
#     return f"File '{file.filename}' uploaded to bucket '{bucket_name}'."

@app.route('/bmi', methods=['GET', 'POST'])
def calculate_bmi():
    bmi = None
    category = None
    if request.method == 'POST':
        try:
            height = float(request.form.get('height'))
            weight = float(request.form.get('weight'))
            # Calculate BMI
            bmi = weight / (height ** 2)
            # Classify the BMI
            if bmi < 18.5:
                category = "Underweight"
            elif 18.5 <= bmi < 24.9:
                category = "Normal weight"
            elif 25 <= bmi < 29.9:
                category = "Overweight"
            else:
                category = "Obesity"
        except (TypeError, ValueError):
            category = "Invalid input. Please enter valid numbers for height and weight."
    return render_template('bmi.html', bmi=bmi, category=category)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005)
    
    