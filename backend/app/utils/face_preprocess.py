import cv2
import mediapipe as mp
import numpy as np

# Lazy initialization for thread safety
_mp_face = None

def _get_face_mesh():
    global _mp_face
    if _mp_face is None:
        _mp_face = mp.solutions.face_mesh.FaceMesh(static_image_mode=True)
    return _mp_face

def align_face(face_img):
    if face_img is None or face_img.size == 0:
        return face_img
    
    # Ensure BGR format
    if len(face_img.shape) == 2:  # Grayscale
        face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)
    
    img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    results = _get_face_mesh().process(img_rgb)

    if not results.multi_face_landmarks:
        return face_img

    landmarks = results.multi_face_landmarks[0].landmark

    # lấy 2 điểm mắt
    left_eye = landmarks[33]
    right_eye = landmarks[263]

    h, w = face_img.shape[:2]
    left = np.array([left_eye.x * w, left_eye.y * h])
    right = np.array([right_eye.x * w, right_eye.y * h])

    dy, dx = right[1] - left[1], right[0] - left[0]
    angle = np.degrees(np.arctan2(dy, dx))

    M = cv2.getRotationMatrix2D(tuple(left), angle, 1.0)
    aligned = cv2.warpAffine(face_img, M, (w, h))

    return aligned

    
def normalize_face(face_img):
    if face_img is None or face_img.size == 0:
        return face_img
    
    # Ensure BGR format
    if len(face_img.shape) == 2:  # Grayscale
        face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)
    
    lab = cv2.cvtColor(face_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    lab = cv2.merge((l,a,b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
