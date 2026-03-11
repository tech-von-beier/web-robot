#!~/anaconda3/envs/google_mediapipe/bin/python3.9
# -*- coding: utf-8 -*-

import sys
import time
import json

import cv2
import mediapipe as mp

def recognize_gesture(hand_lms):    
    # hand landmark id
    FINGERS = {
        'index':  {'tip':  8, 'pip':  6, 'mcp':  5},
        'middle': {'tip': 12, 'pip': 10, 'mcp':  9},
        'ring':   {'tip': 16, 'pip': 14, 'mcp': 13},
        'pinky':  {'tip': 20, 'pip': 18, 'mcp': 17}
    }
    wrist = hand_lms.landmark[0]
    
    # calculate distance
    def sq_dist(p1, p2):
        return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

    # determine finger status
    def is_extended(finger):
        tip_idx = FINGERS[finger]['tip']
        pip_idx = FINGERS[finger]['pip']
        
        d_tip = sq_dist(hand_lms.landmark[tip_idx], wrist)
        d_pip = sq_dist(hand_lms.landmark[pip_idx], wrist)
        return d_tip > d_pip
    
    index_ext = is_extended('index')
    middle_ext = is_extended('middle')
    ring_ext = is_extended('ring')
    pinky_ext = is_extended('pinky')
    
    gesture = "Unknown"
    if index_ext and not middle_ext and not ring_ext and not pinky_ext:
        idx_tip = hand_lms.landmark[FINGERS['index']['tip']]
        idx_mcp = hand_lms.landmark[FINGERS['index']['mcp']]
        dx = abs(idx_tip.x - idx_mcp.x)
        dy = abs(idx_tip.y - idx_mcp.y)
        if dx < dy:
            gesture = "down1" if idx_tip.y > idx_mcp.y else "up1"
        else:
            gesture = "right" if idx_tip.x > idx_mcp.x else "left"
    elif index_ext and middle_ext and not ring_ext and not pinky_ext:
        idx_tip = hand_lms.landmark[FINGERS['index']['tip']]        
        gesture = "down2" if idx_tip.y > wrist.y else "up2"
    elif index_ext and middle_ext and ring_ext and not pinky_ext :
        idx_tip = hand_lms.landmark[FINGERS['index']['tip']]
        gesture = "down3" if idx_tip.y > wrist.y else "up3"
    
    return gesture

def process():
    mp_drawing = mp.solutions.drawing_utils
    hand_landmarks_style = mp_drawing.DrawingSpec(color=(0, 0, 255) , thickness=5)
    hand_connections_style = mp_drawing.DrawingSpec(color=(0, 255, 0) , thickness=10)
    mp_hands = mp.solutions.hands
    
    cap = cv2.VideoCapture(0)
    
    with mp_hands.Hands() as hands:
        pTime = 0
        cTime = 0
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                continue

            imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(imageRGB)
            
            # ros request
            line = sys.stdin.readline()
            
            h = image.shape[0]
            w = image.shape[1]
            joints = {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0, "q6": 0}
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        hand_landmarks_style,
                        hand_connections_style) 
                    
                    for i, lm in enumerate(hand_landmarks.landmark):
                        x = int(lm.x * w)
                        y = int(lm.y * h)
                        cv2.putText(image, str(i), (x - 20,y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 2)
                    
                    gesture = recognize_gesture(hand_landmarks)
                    cv2.putText(image, gesture, (200, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 4)
                                        
                    if gesture == "right":
                        joints = {"q1": 1, "q2": 0, "q3": 0, "q4": 0, "q5": 0, "q6": 0}
                    elif gesture == "left":
                        joints = {"q1": -1, "q2": 0, "q3": 0, "q4": 0, "q5": 0, "q6": 0}
                    elif gesture == "down1":
                        joints = {"q1": 0, "q2": 1, "q3": 0, "q4": 0, "q5": 0, "q6": 0}
                    elif gesture == "up1":
                        joints = {"q1": 0, "q2": -1, "q3": 0, "q4": 0, "q5": 0, "q6": 0}
                    elif gesture == "down2":
                        joints = {"q1": 0, "q2": 0, "q3": 1, "q4": 0, "q5": 0, "q6": 0}
                    elif gesture == "up2":
                        joints = {"q1": 0, "q2": 0, "q3": -1, "q4": 0, "q5": 0, "q6": 0}
                    elif gesture == "down3":
                        joints = {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 1, "q6": 0}
                    elif gesture == "up3":
                        joints = {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": -1, "q6": 0}
                    
            payload = {
                "status": "success",
                "joints": joints,
                "py_version": f"{sys.version_info.major}.{sys.version_info.minor}"
            }
            print(json.dumps(payload), flush=True)
                        
            cTime = time.time()
            fps = 1 / (cTime - pTime)
            pTime = cTime
            cv2.putText(image, f"FPS: {int(fps)}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 4) 
            
            cv2.imshow('cam', image)
            if cv2.waitKey(1) & 0xFF == 27:
                break
         
if __name__ == '__main__':
    try:
       process()
    except Exception as e:
       print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
       sys.exit(1)

