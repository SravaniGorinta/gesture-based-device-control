import cv2
import mediapipe as mp
import time
import numpy as np
import threading
import queue
import requests
from flask import Flask, render_template, Response, jsonify

# ---------------- Flask Setup ----------------
app = Flask(__name__)

system_state = {
    "target": "READY",
    "action": "---",
    "LIGHT": "OFF",
    "FAN": "OFF",
    "BED BULB": "OFF",
    "AC": "OFF"
}

# ---------------- Configuration ----------------
USE_BLYNK = True
BLYNK_AUTH = "wkzeMnZq8c7Q6gUZEx8X9rqMoJIFlZUy"
BASE_URL = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}"

ZONE_LED_PINS = {"LIGHT": "V0", "FAN": "V1", "BED BULB": "V2", "AC": "V3"}
ZONE_RELAY_PINS = {"LIGHT": "V4", "FAN": "V5", "BED BULB": "V6", "AC": "V7"}

# ---------------- Blynk Async ----------------
_blynk_queue = queue.Queue()

def blynk_worker():
    session = requests.Session()
    while True:
        url = _blynk_queue.get()
        if url is None: break
        try:
            session.get(url, timeout=0.7)
        except:
            pass
        _blynk_queue.task_done()

threading.Thread(target=blynk_worker, daemon=True).start()

def send_to_blynk(pin, value):
    if not USE_BLYNK: return
    url = f"{BASE_URL}&{pin}={value}"
    _blynk_queue.put(url)
    print(f"Sent to Blynk: {pin} -> {value}")

# ---------------- MediaPipe Setup ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.75, min_tracking_confidence=0.75)
draw = mp.solutions.drawing_utils

# ---------------- States ----------------
last_output = ""
last_time = 0
cooldown = 0.1
gesture_history = []
BUFFER_SIZE = 3
zone_selected = None
zone_selected_time = None
highlight_time = None
selection_highlight_time = None
last_relay_state = {"LIGHT":"OFF","FAN":"OFF","BED BULB":"OFF","AC":"OFF"}
current_led_zone = None
output_frame = None
lock = threading.Lock()

# ---------------- FINAL FIXED FUNCTION ----------------
def finger_count(hand, hand_type):
    lm = hand.landmark

    wrist = lm[0]
    tip_ids = [4, 8, 12, 16, 20]

    # Distance-based analysis
    distances = []
    for tip in tip_ids:
        dist = ((lm[tip].x - wrist.x)**2 + (lm[tip].y - wrist.y)**2) ** 0.5
        distances.append(dist)

    # Count closed fingers
    closed_fingers = sum(1 for d in distances if d < 0.18)

    # Robust fist detection (prevents single finger misclassification)
    if closed_fingers >= 4 and max(distances) < 0.22:
        return 0

    # Original logic
    count = 0

    # Thumb
    if hand_type == "Right":
        if lm[4].x > lm[3].x: count += 1
    else:
        if lm[4].x < lm[3].x: count += 1

    # Fingers
    tips = [8,12,16,20]
    mids = [6,10,14,18]

    for t,m in zip(tips,mids):
        if lm[t].y < lm[m].y:
            count += 1

    return count

# ---------------- Functions ----------------
def detect_zone(x,y,w,h):
    if y < h//2:
        return "LIGHT" if x < w//2 else "FAN"
    else:
        return "BED BULB" if x < w//2 else "AC"

def highlight(frame, zone, color):
    h,w,_ = frame.shape
    overlay = frame.copy()
    if zone=="LIGHT":
        cv2.rectangle(overlay,(0,0),(w//2,h//2),color,-1)
    elif zone=="FAN":
        cv2.rectangle(overlay,(w//2,0),(w,h//2),color,-1)
    elif zone=="BED BULB":
        cv2.rectangle(overlay,(0,h//2),(w//2,h),color,-1)
    elif zone=="AC":
        cv2.rectangle(overlay,(w//2,h//2),(w,h),color,-1)
    cv2.addWeighted(overlay,0.3,frame,0.7,0,frame)

# ---------------- Flask Routes ----------------
@app.route('/')
def landing(): return render_template('landing.html')

@app.route('/dashboard')
def index(): return render_template('index.html')

@app.route('/get_status')
def get_status(): 
    for key in last_relay_state:
        system_state[key] = last_relay_state[key]
    system_state["target"] = zone_selected if zone_selected else "READY"
    return jsonify(system_state)

def generate_frames():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None: continue
            ret, buffer = cv2.imencode('.jpg', output_frame)
            frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ---------------- MAIN LOGIC THREAD ----------------
def run_logic():
    global last_output, last_time, gesture_history, zone_selected, zone_selected_time
    global highlight_time, selection_highlight_time, last_relay_state, current_led_zone, output_frame

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.resize(frame, (640, 480))
        frame = cv2.flip(frame,1)
        h,w,_ = frame.shape

        cv2.line(frame,(w//2,0),(w//2,h),(0,255,0),1)
        cv2.line(frame,(0,h//2),(w,h//2),(0,255,0),1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            hand_type = result.multi_handedness[0].classification[0].label
            draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            xs = [p.x for p in hand.landmark]
            ys = [p.y for p in hand.landmark]
            cx, cy = int(np.mean(xs)*w), int(np.mean(ys)*h)

            zone = detect_zone(cx,cy,w,h)
            fingers = finger_count(hand, hand_type)

            gesture_history.append(fingers)
            if len(gesture_history)>BUFFER_SIZE: gesture_history.pop(0)
            stable = max(set(gesture_history), key=gesture_history.count)

            now = time.time()
            if now - last_time > cooldown:
                output = ""

                if stable >= 4:
                    output = zone
                    zone_selected = zone
                    zone_selected_time = time.time()
                    selection_highlight_time = time.time()

                    if current_led_zone != zone:
                        current_led_zone = zone
                        for z,pin in ZONE_LED_PINS.items(): send_to_blynk(pin, 0)
                        send_to_blynk(ZONE_LED_PINS[zone], 1)

                elif zone_selected == zone and zone_selected_time and (time.time() - zone_selected_time < 5):
                    
                    if 1 <= stable <= 3:
                        output = f"{zone} ON"
                        zone_selected_time = time.time()
                    
                    elif stable == 0:
                        output = f"{zone} OFF"
                        zone_selected_time = time.time()

                if output and output != last_output:
                    last_output = output
                    last_time = now
                    parts = output.split()
                    zone_name = " ".join(parts[:-1]) if len(parts)>1 else output
                    state = parts[-1] if len(parts)>1 else None

                    if state == "ON" and last_relay_state[zone_name] != "ON":
                        last_relay_state[zone_name] = "ON"
                        send_to_blynk(ZONE_RELAY_PINS[zone_name], 1)
                    elif state == "OFF" and last_relay_state[zone_name] != "OFF":
                        last_relay_state[zone_name] = "OFF"
                        send_to_blynk(ZONE_RELAY_PINS[zone_name], 0)

                    highlight_time = time.time()

        if zone_selected and zone_selected_time:
            if time.time() - zone_selected_time > 5:
                if current_led_zone:
                    send_to_blynk(ZONE_LED_PINS[current_led_zone], 0)
                    current_led_zone = None
                zone_selected = None
                zone_selected_time = None

        if last_output:
            cv2.putText(frame, last_output, (30, h-30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        if selection_highlight_time and time.time() - selection_highlight_time < 1:
            highlight(frame, zone_selected, (255, 200, 100))

        if highlight_time and time.time() - highlight_time < 1:
            parts = last_output.split()
            if len(parts) > 1:
                zn = " ".join(parts[:-1]); st = parts[-1]
                clr = (0, 255, 0) if st == "ON" else (0, 0, 255)
                highlight(frame, zn, clr)

        with lock:
            output_frame = frame.copy()

        # NO POPUP WINDOW
        # cv2.imshow("Gesture Control", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_logic, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)