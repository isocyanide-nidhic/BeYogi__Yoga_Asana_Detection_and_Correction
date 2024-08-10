import threading
from flask import Flask, render_template, url_for, request, session
import sqlite3
import os
import secrets
from flask import Flask, render_template, Response
import cv2
import mediapipe as mp
import math
import matplotlib.pyplot as plt
from gtts import gTTS
import os
from mutagen.mp3 import MP3
import pygame 
import time

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()



command = """CREATE TABLE IF NOT EXISTS user(name TEXT, password TEXT, mobile TEXT, email TEXT)"""
cursor.execute(command)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('userlog.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/userlog', methods=['GET', 'POST'])
def userlog():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM user WHERE email = '"+email+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchone()

        if result:
            session['user'] = result[0]
            return render_template('userlog.html')
        else:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('index.html')


@app.route('/userreg', methods=['GET', 'POST'])
def userreg():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']
        mobile = request.form['phone']
        email = request.form['email']
        
        print(name, mobile, email, password)

        cursor.execute("INSERT INTO user VALUES ('"+name+"', '"+password+"', '"+mobile+"', '"+email+"')")
        connection.commit()

        return render_template('index.html', msg='Successfully Registered')
    
    return render_template('index.html')

@app.route('/logout')
def logout():
    return render_template('index.html')

# Initialize mediapipe pose class
mp_pose = mp.solutions.pose

# Setting up the Pose function
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)

# Initializing mediapipe drawing class, useful for annotation.
mp_drawing = mp.solutions.drawing_utils 

def detectPose(image, pose, display=True):
    '''
    This function performs pose detection on an image.
    Args:
        image: The input image with a prominent person whose pose landmarks needs to be detected.
        pose: The pose setup function required to perform the pose detection.
        is_correct_pose: A boolean indicating whether the detected pose is correct or not.
        display: A boolean value that is if set to true the function displays the original input image, the resultant image, 
                and the pose landmarks in 3D plot and returns nothing.
    Returns:
        output_image: The input image with the detected pose landmarks drawn.
        landmarks: A list of detected landmarks converted into their original scale.
    '''

    # Create a copy of the input image.
    output_image = image.copy()

    # Convert the image from BGR into RGB format.
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Perform the Pose Detection.
    results = pose.process(imageRGB)

    # Retrieve the height and width of the input image.
    height, width, _ = image.shape

    # Initialize a list to store the detected landmarks.
    landmarks = []

    # Check if any landmarks are detected.
    if results.pose_landmarks:

        # Draw Pose landmarks on the output image.
        mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks,
                                  connections=mp_pose.POSE_CONNECTIONS)

        # Iterate over the detected landmarks.
        for landmark in results.pose_landmarks.landmark:
            
            # Append the landmark into the list.
            landmarks.append((int(landmark.x * width), int(landmark.y * height),
                              (landmark.z * width)))
            # Draw the landmark on the output image

    return output_image, landmarks


def calculateAngle(landmark1, landmark2, landmark3):
    '''
    This function calculates angle between three different landmarks.
    Args:
        landmark1: The first landmark containing the x,y and z coordinates.
        landmark2: The second landmark containing the x,y and z coordinates.
        landmark3: The third landmark containing the x,y and z coordinates.
    Returns:
        angle: The calculated angle between the three landmarks.

    '''

    # Get the required landmarks coordinates.
    x1, y1, _ = landmark1
    x2, y2, _ = landmark2
    x3, y3, _ = landmark3

    # Calculate the angle between the three points
    angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
    
    # Check if the angle is less than zero.
    if angle < 0:

        # Add 360 to the found angle.
        angle += 360
    
    # Return the calculated angle.
    return angle


def get_audio_length(file_path):
    # Load the audio file
    sound = pygame.mixer.Sound(file_path)
    # Get the duration of the audio in seconds
    return sound.get_length()

def play_audio(path):
    # Initialize pygame mixer

    pygame.mixer.init()

    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

    # Wait for the audio to finish playing
    time.sleep(get_audio_length(path))
    # Cleanup
    pygame.mixer.quit()


  


def classifyPose(landmarks, output_image, display=False):
    '''
    This function classifies yoga poses depending upon the angles of various body joints.
    Args:
        landmarks: A list of detected landmarks of the person whose pose needs to be classified.
        output_image: A image of the person with the detected pose landmarks drawn.
        display: A boolean value that is if set to true the function displays the resultant image with the pose label
        written on it and returns nothing.
    Returns:
        output_image: The image with the detected pose landmarks drawn and pose label written.
        label: The classified pose label of the person in the output_image.

    '''

    # Initialize the label of the pose. It is not known at this stage.
    label = 'Unknown Pose'

    # Specify the color (Red) with which the label will be written on the image.
    color = (0, 0, 255)

    # Calculate the required angles.
    #----------------------------------------------------------------------------------------------------------------

    # Get the angle between the left shoulder, elbow and wrist points.
    left_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                      landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                      landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value])

    # Get the angle between the right shoulder, elbow and wrist points.
    right_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                       landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value],
                                       landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value])

    # Get the angle between the left elbow, shoulder and hip points.
    left_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                         landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                         landmarks[mp_pose.PoseLandmark.LEFT_HIP.value])

    # Get the angle between the right hip, shoulder and elbow points.
    right_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                          landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value])

    # Get the angle between the left hip, knee and ankle points.
    left_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value],
                                     landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value],
                                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value])

    # Get the angle between the right hip, knee and ankle points
    right_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                      landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value],
                                      landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value])

    #----------------------------------------------------------------------------------------------------------------

    # Check if it is the warrior II pose or the T pose.
    # As for both of them, both arms should be straight and shoulders should be at the specific angle.
    #----------------------------------------------------------------------------------------------------------------

    # if (165 < left_knee_angle < 195) and (165 < right_knee_angle < 195) \
    #     and (130 < left_elbow_angle < 180) and (175 < right_elbow_angle < 220) \
    #     and (100 < left_shoulder_angle < 200) and (50 < right_shoulder_angle < 130):

    #     # Specify the label of the pose as Trikonasana Pose
    #     label = 'T Pose'

    # #----------------------------------------------------------------------------------------------------------------

    # # Check if the both arms are straight.
    # if left_elbow_angle > 165 and left_elbow_angle < 195 and right_elbow_angle > 165 and right_elbow_angle < 195:

    #     # Check if shoulders are at the required angle.
    #     if left_shoulder_angle > 80 and left_shoulder_angle < 110 and right_shoulder_angle > 80 and right_shoulder_angle < 110:

    #         # Check if it is the warrior II pose.
    #         #----------------------------------------------------------------------------------------------------------------

    #         # Check if one leg is straight.
    #         if left_knee_angle > 165 and left_knee_angle < 195 or right_knee_angle > 165 and right_knee_angle < 195:

    #             # Check if the other leg is bended at the required angle.
    #             if left_knee_angle > 90 and left_knee_angle < 120 or right_knee_angle > 90 and right_knee_angle < 120:

    #                 # Specify the label of the pose that is Warrior II pose.
    #                 label = 'Warrior II Pose'

    #         #----------------------------------------------------------------------------------------------------------------

    #         #----------------------------------------------------------------------------------------------------------------

    #         # Check if both legs are straight
    #         if left_knee_angle > 160 and left_knee_angle < 195 and right_knee_angle > 160 and right_knee_angle < 195:

    #         #     # Specify the label of the pose that is tree pose.
    #             label = 'Virabadrasana'
    #----------------------------------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------------------------------

    # Check if it is the tree pose.
    #----------------------------------------------------------------------------------------------------------------

    # Check if one leg is straight
    if left_knee_angle > 165 and left_knee_angle < 195 or right_knee_angle > 165 and right_knee_angle < 195:

        # Check if the other leg is bended at the required angle.
        if left_knee_angle > 315 and left_knee_angle < 335 or right_knee_angle > 25 and right_knee_angle < 45:

            # Specify the label of the pose that is tree pose.
            label = 'Tree Pose'

    #----------------------------------------------------------------------------------------------------------------
    # Check if one leg is straight
    if left_knee_angle > 185 and left_knee_angle < 165 or right_knee_angle > 185 and right_knee_angle < 165:

            # Specify the label of the pose that is tree pose.
        label = 'Vrikshasana'

    #----------------------------------------------------------------------------------------------------------------
    #----our code neww------------------------------------------------------------------------------------------------------------    
    
    #Utkata Konasana ---- Kekada pose
    if (60 < left_elbow_angle < 95) and (210 < right_elbow_angle < 280) \
        and (200 < left_knee_angle < 260) and (90 < right_knee_angle < 135) \
        and (50 <left_shoulder_angle < 100) and (50 < right_shoulder_angle < 100):
        
    #     # Specify the label of the pose as Tadasana Pose
        label = 'Utkata Konasana'
    #----------------------------------------------------------------------------------------
    
    if (150 < left_elbow_angle < 175) and (180 < right_elbow_angle < 210) \
        and (165 < left_knee_angle < 180) and (170 < right_knee_angle < 190) \
        and (170<left_shoulder_angle < 195) and (175<right_shoulder_angle < 190):
        
        # Specify the label of the pose as Tadasana Pose
        label = 'Tadasana'
    #--------------------------------------------------
#utkatasana right facing
    if (160 < left_elbow_angle < 190) and (150 < right_elbow_angle < 190) \
        and (230 < left_knee_angle < 270) and (240 < right_knee_angle < 280) \
        and (140<left_shoulder_angle < 170) and (185<right_shoulder_angle < 225):
        
        # Specify the label of the pose as Tadasana Pose
        label = 'Utkatasana'
#------------------------------------------------------------------------------------------
#trikonasana  
    if (150 < left_elbow_angle < 190) and (180 < right_elbow_angle < 200) \
        and (180 < left_knee_angle < 185) and (165 < right_knee_angle < 180) \
        and (70<left_shoulder_angle < 135) and (100<right_shoulder_angle < 130):
        
        # Specify the label of the pose as Tadasana Pose
        label = 'Trikonasana'

#--------------------------------------------------------------------------------------

    DetectedText  = "yoga pose is correct, well done"
    #--------------our code ends-------------------------
    # Check if the pose is classified successfully
    if label == 'Unknown Pose':
        # Update the color (to green) with which the label will be written on the image.
        color = (0, 0, 255)
        DetectedText = "yoga pose is not correct, follow the instructions"
    else:
        color = (0,255,0)

    # Write the label on the output image.
    cv2.putText(output_image, label, (10, 30),cv2.FONT_HERSHEY_PLAIN, 2, color, 2)
    height, width, _ = output_image.shape

    for landmark in landmarks:
        cv2.circle(output_image, (landmark[0], landmark[1]), 5, color,-1)

    cv2.putText(output_image, DetectedText, (10, 600),cv2.FONT_HERSHEY_PLAIN, 2, color, 2)

    # Check if the resultant image is specified to be displayed.
    if display:
        # Display the resultant image.
        plt.figure(figsize=[10,10])
        plt.imshow(output_image)
    return output_image, label


def webcam_feed():
    count=0
    # Initialize the VideoCapture object to read from the webcam
    camera_video = cv2.VideoCapture(0)
    camera_video.set(3, 1380)
    camera_video.set(4, 960)
    camera_video.set(cv2.CAP_PROP_FPS, 5)  # Set frame rate (fps)


    while camera_video.isOpened():
        count=count+30
        # Read a frame
        ok, frame = camera_video.read()

        if not ok:
            break  # Exit the loop if no frame is captured

        # Flip the frame horizontally for natural (selfie-view) visualization
        frame = cv2.flip(frame, 1)

        # Get the width and height of the frame
        frame_height, frame_width, _ = frame.shape

        # Resize the frame while keeping the aspect ratio
        frame = cv2.resize(frame, (int(frame_width * (640 / frame_height)), 640))

        # Perform Pose landmark detection
        frame, landmarks = detectPose(frame, pose, display=False)

        if landmarks:
            # Perform the Pose Classification
            frame, _ = classifyPose(landmarks, frame, display=False)
            if count %1000 == 0:
                if _ != "Unknown Pose" :
                    play_audio("./right.mp3")
                else:
                    play_audio("./wrong.mp3")

        
        # Convert the frame to JPEG format
        ret, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # Release the video capture object and close any OpenCV windows
    camera_video.release()
    cv2.destroyAllWindows()

@app.route('/yoga_try')
def yoga_try():
    return render_template('yoga_try.html')

@app.route('/video_feed1')
def video_feed1():
    return Response(webcam_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)


