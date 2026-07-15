# Gesture Based Device Control

A computer vision and IoT-based smart device control system that allows users to control home appliances using hand gestures. The system uses real-time hand gesture recognition through a webcam and communicates with an ESP8266-based hardware controller using Blynk IoT.

---

# Project Overview

The **Gesture Based Device Control** system provides a touch-free method to operate electrical appliances such as lights, fans, bed bulbs, and AC units.

The system combines:

* Computer vision for real-time hand detection
* MediaPipe-based hand tracking
* Gesture-based device selection and control
* Flask web dashboard
* IoT communication
* ESP8266 hardware control
* Blynk IoT cloud integration

The user first selects a device zone by showing an open palm inside the required zone. Once a zone is activated, only that selected device can be controlled for a limited duration, preventing accidental activation of other devices.

---

# Features

## Gesture-Based Control

* Real-time hand detection using MediaPipe
* Finger-count-based gesture recognition
* Touch-free appliance operation
* Stable gesture detection using gesture buffering
* Zone activation system to avoid false triggering
* Automatic zone timeout for safer operation

---

# Device Control

The system controls multiple appliances:

| Device   | Function       |
| -------- | -------------- |
| Light    | ON/OFF control |
| Fan      | ON/OFF control |
| Bed Bulb | ON/OFF control |
| AC       | ON/OFF control |

---

# Zone Activation System

The camera frame is divided into four device zones:

```
+----------------+----------------+
|                |                |
|     LIGHT      |      FAN       |
|                |                |
+----------------+----------------+
|                |                |
|   BED BULB     |       AC       |
|                |                |
+----------------+----------------+
```

## Zone Selection Process

1. The user places their palm inside a device zone.
2. An open palm gesture activates that zone.
3. The selected zone is highlighted and becomes active.
4. The active zone remains available for **5 seconds**.
5. During this period, only the selected device can receive ON/OFF commands.
6. After 5 seconds, the zone automatically deactivates to prevent accidental commands.

This prevents:

* Incorrect device selection
* False positives caused by random hand movement
* Accidental appliance switching

---

# Gesture Commands

| Gesture                | Action                      |
| ---------------------- | --------------------------- |
| Open Palm (4+ fingers) | Activate/select device zone |
| Index Finger           | Turn ON selected device     |
| Closed Fist            | Turn OFF selected device    |

## Control Flow

```
Open Palm
    |
    v
Select Device Zone
    |
    v
Zone Active for 5 seconds
    |
    +----------------+
    |                |
    v                v
Index Finger      Closed Fist
    |                |
    v                v
Device ON        Device OFF
```

---

# System Architecture

```
             Webcam
                |
                |
                v
        OpenCV + MediaPipe
                |
                |
                v
       Hand Gesture Recognition
                |
                |
                v
       Zone Selection Logic
                |
                |
                v
          Flask Application
                |
                |
                v
          Blynk IoT Cloud
                |
                |
                v
            ESP8266
                |
                |
                v
       Relay Module + Appliances
```

---

# Technologies Used

## Software

* Python
* OpenCV
* MediaPipe
* Flask
* NumPy
* Requests
* Blynk IoT

## Hardware

* ESP8266 NodeMCU
* 4-channel Relay Module
* LEDs
* Electrical appliances
* Webcam
* WiFi connection

---

# Project Structure

```
gesture-based-device-control/

│
├── app.py
│   └── Main Flask application with gesture recognition
│
├── test.py
│   └── Standalone gesture testing application
│
├── requirements.txt
│   └── Python dependencies
│
├── README.md
│
├── hardware/
│   └── esp8266_blynk_control.ino
│       └── ESP8266 firmware for relay and LED control
│
├── templates/
│   ├── index.html
│   └── landing.html
│
└── static/
    └── css/
        └── style.css
```

---

# Software Installation

## 1. Clone Repository

```bash
git clone https://github.com/SravaniGorinta/gesture-based-device-control.git
```

Navigate into the project folder:

```bash
cd gesture-based-device-control
```

---

## 2. Create Virtual Environment

Create a Python virtual environment:

```bash
python -m venv venv310
```

Activate it:

### Windows

```bash
venv310\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

Start the Flask application:

```bash
python app.py
```

Open:

```
http://localhost:5000
```

The dashboard provides:

* Live camera stream
* Current selected zone
* Device status
* Gesture-based control feedback

---

# Hardware Setup

## ESP8266 LED Connections

| Device       | ESP8266 Pin | Blynk Virtual Pin |
| ------------ | ----------- | ----------------- |
| Light LED    | D0          | V0                |
| Fan LED      | D2          | V1                |
| Bed Bulb LED | D3          | V2                |
| AC LED       | D4          | V3                |

---

## Relay Connections

| Device         | ESP8266 Pin | Blynk Virtual Pin |
| -------------- | ----------- | ----------------- |
| Light Relay    | D1          | V4                |
| Fan Relay      | D5          | V5                |
| Bed Bulb Relay | D6          | V6                |
| AC Relay       | D7          | V7                |

---

# ESP8266 Setup

1. Install Arduino IDE.
2. Install ESP8266 board support.
3. Install libraries:

```
Blynk
ESP8266WiFi
```

4. Open:

```
hardware/esp8266_blynk_control.ino
```

5. Configure:

```cpp
#define BLYNK_AUTH_TOKEN "YOUR_TOKEN"

char ssid[] = "YOUR_WIFI_NAME";
char pass[] = "YOUR_WIFI_PASSWORD";
```

6. Upload firmware to ESP8266.

---

# Blynk Integration

The Python application communicates with Blynk Cloud using virtual pins.

```
V0 - Light LED
V1 - Fan LED
V2 - Bed Bulb LED
V3 - AC LED

V4 - Light Relay
V5 - Fan Relay
V6 - Bed Bulb Relay
V7 - AC Relay
```

Communication flow:

```
Python Application
        |
        v
Blynk Cloud
        |
        v
ESP8266 Controller
        |
        v
Relay Switching
        |
        v
Electrical Appliance
```

---

# Requirements

## Python Packages

```
opencv-python
mediapipe
numpy
flask
requests
```

## Hardware Requirements

* ESP8266 NodeMCU
* 4-channel relay module
* LEDs
* Webcam
* WiFi connection

---

# Future Improvements

* Voice-based device control
* Mobile application support
* Deep learning-based gesture recognition
* Multiple user profiles
* Smart scheduling
* Energy consumption monitoring
* Real-time usage analytics

---

# Author

**Sravani Gorinta**

Project: Gesture Based Device Control

---

# License

This project is developed for educational and academic purposes.
