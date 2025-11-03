# 🖐️ Air Cursor Using Hand Gestures

**Air Cursor Using Hand Gestures** is a Python-based project that enables hands-free cursor navigation through real-time hand gesture recognition.  
Using computer vision and machine learning, it lets you control your computer’s mouse cursor using only your hand movements captured by a webcam.

This project aims to make computer interaction more intuitive and accessible, especially for users who prefer or require touchless control.

---

## 🚀 Features

- **Hands-free cursor control:** Move your system cursor using your hand instead of a traditional mouse.  
- **Real-time gesture recognition:** Detects and responds instantly to your hand movements via webcam.  
- **Air drawing mode:** Draw on the screen using simple gestures (see `enhanced_air_drawing.py`).  
- **Gesture-controlled games:** Play example games controlled entirely by hand gestures.  
- **Customizable gestures:** Easy to expand for more gesture-based controls.

---

## 🧩 Project Structure

| File | Description |
|------|--------------|
| `Air_Cursor.py` | Main script to control the system cursor using hand gestures. |
| `enhanced_air_drawing.py` | Script that allows drawing in the air using gestures. |
| `game.py` / `game1.py` | Sample gesture-controlled games for demonstration. |
| `requirements.txt` | List of dependencies required to run the project. |

---

## 🛠 Requirements

Make sure you have **Python 3.x** installed.  
You’ll also need the following libraries:

- `opencv-python`
- `mediapipe`
- `numpy`
- `pyautogui`
- `time` (built-in)
- `math` (built-in)

You can install all dependencies with:

```bash
pip install opencv-python mediapipe numpy pyautogui
````

Alternatively, if you have the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/cherry-12345/Air-Cursor-Using-Hand-Gestures.git
   cd Air-Cursor-Using-Hand-Gestures
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Connect your webcam**

   Make sure your webcam is working and accessible.

---

## ▶️ Usage

### 1. Run Air Cursor

Start the main program to control the cursor using your hand:

```bash
python Air_Cursor.py
```

Move your hand in front of the camera to move the cursor.
Different gestures perform different actions such as clicking or dragging.

### 2. Try Air Drawing Mode

To enable air drawing (using gestures to draw on screen):

```bash
python enhanced_air_drawing.py
```

Follow the on-screen instructions to toggle between cursor and drawing modes.

### 3. Play Gesture-Controlled Games

You can try fun demo games that use gesture controls:

```bash
python game.py
# or
python game1.py
```

---

## 🧠 How It Works

1. The program captures real-time video from your webcam using **OpenCV**.
2. **MediaPipe** detects hand landmarks (like finger tips and joints).
3. Based on the position of landmarks, gestures are identified.
4. **PyAutoGUI** translates those gestures into cursor movements and clicks.
5. The system runs smoothly in real time for an interactive experience.

---

## 🎥 Demo

You can include screenshots or a demo GIF here:

```
![Air Cursor Demo](demo/demo.gif)
```

*(Add your own demo files inside a `/demo` folder for GitHub display.)*

---

## 🧾 Example Gestures

| Gesture                  | Action                 |
| ------------------------ | ---------------------- |
| Index finger up          | Move cursor            |
| Index + middle finger up | Click or drag          |
| All fingers closed       | Stop cursor movement   |
| Special combination      | Switch to drawing mode |

*(These can be customized in the code.)*

---

## 🧑‍💻 Author

**Cherry-12345**
GitHub: [https://github.com/cherry-12345](https://github.com/cherry-12345)

---

## 🤝 Contributing

Contributions are always welcome!
If you’d like to improve gesture recognition, add new features, or fix bugs:

1. Fork the repository
2. Create a new branch (`feature/your-feature-name`)
3. Commit your changes
4. Push to your branch
5. Open a pull request

---

## 📜 License

This project is open-source and distributed under the **MIT License**.
You are free to use, modify, and distribute it with proper attribution.

---

## 💬 Acknowledgements

* [OpenCV](https://opencv.org/) for real-time computer vision
* [MediaPipe](https://developers.google.com/mediapipe) for hand landmark detection
* [PyAutoGUI](https://pyautogui.readthedocs.io/en/latest/) for system-level cursor control

---

# ⭐ If you find this project useful, don’t forget to give it a star on GitHub!

