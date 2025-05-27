from mediapipe import solutions
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import mediapipe as mp
import cv2

left_shoulder_elbow_up = False
left_elbow_wrist_up = False

right_shoulder_elbow_up = False
right_elbow_wrist_up = False

arms_up = False
low_light = False


def detect_low_light(frame):
    global low_light
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Calculate mean brightness
    mean_brightness = np.mean(gray)

    low_light = True if mean_brightness < 60 else False


def draw_landmarks_on_image(rgb_image, detection_result):
    global left_shoulder_elbow_up, left_elbow_wrist_up, right_shoulder_elbow_up, right_elbow_wrist_up

    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)

    # Loop through the detected poses to visualize.
    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]


        # Esquerda
        left_shoulder = pose_landmarks_list[0][12]
        left_elbow = pose_landmarks_list[0][14]
        left_wrist = pose_landmarks_list[0][16]

        # print(left_shoulder.y)
        # print(left_elbow.y)
        # print(left_wrist.y)

        # print((left_elbow.y - left_shoulder.y) / ((left_shoulder.z + left_elbow.z) / 2)) # 0.20
        # print((left_wrist.y - left_elbow.y) / ((left_wrist.z + left_elbow.z) / 2)) # 0.30

        left_shoulder_elbow_up = True if (left_elbow.y - left_shoulder.y) / ((left_shoulder.z + left_elbow.z) / 2) > 0.30 else False
        left_elbow_wrist_up = True if (left_wrist.y - left_elbow.y) / ((left_wrist.z + left_elbow.z) / 2) > 0.20 else False



        # Direita
        right_shoulder = pose_landmarks_list[0][11]
        right_elbow = pose_landmarks_list[0][13]
        right_wrist = pose_landmarks_list[0][15]

        # print(right_shoulder.y)
        # print(right_elbow.y)
        # print(right_wrist.y)

        # print((right_elbow.y - right_shoulder.y) / ((right_shoulder.z + right_elbow.z) / 2)) # 0.30
        # print((right_wrist.y - right_elbow.y) / ((right_wrist.z + right_elbow.z) / 2)) # 0.20

        right_shoulder_elbow_up = True if (right_elbow.y - right_shoulder.y) / ((right_shoulder.z + right_elbow.z) / 2) > 0.30 else False
        right_elbow_wrist_up = True if (right_wrist.y - right_elbow.y) / ((right_wrist.z + right_elbow.z) / 2) > 0.20 else False


        # Draw the pose landmarks.
        pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        pose_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
        ])
        solutions.drawing_utils.draw_landmarks(
            annotated_image,
            pose_landmarks_proto,
            solutions.pose.POSE_CONNECTIONS,
            solutions.drawing_styles.get_default_pose_landmarks_style())
    return annotated_image


BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO)

with PoseLandmarker.create_from_options(options) as landmarker:
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FPS, 60)

    while True:
        if left_shoulder_elbow_up and left_elbow_wrist_up and right_shoulder_elbow_up and left_elbow_wrist_up:
            arms_up = True
        else:
            arms_up = False

        ret, frame = cam.read()
        frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        detect_low_light(rgb_frame)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        pose_landmarker_result = landmarker.detect_for_video(mp_image, int(cv2.getTickCount() / cv2.getTickFrequency() * 1000))

        annotated_image = draw_landmarks_on_image(mp_image.numpy_view(), pose_landmarker_result)

        alert = True if arms_up and low_light else False

        cv2.putText(annotated_image, f"Maos alto: {arms_up}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        cv2.putText(annotated_image, f"Escuro: {low_light}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.putText(annotated_image, f"Alerta: {alert}", (430, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("View", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        if cv2.waitKey(1) == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
