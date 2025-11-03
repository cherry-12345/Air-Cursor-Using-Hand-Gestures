import cv2
import mediapipe as mp
import numpy as np
import os
import threading
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import logging

# Suppress TensorFlow warnings for a cleaner output
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Initialize Mediapipe hands module for gesture detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Canvas and drawing settings
canvas_width, canvas_height = 1280, 720  # Increased resolution for larger window
canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
drawing = False
last_point = None
DRAW_COLOR = (255, 255, 255)  # Default white color
DRAW_THICKNESS = 5  # Default thickness
points_history = []  # To store drawing points for undo functionality
current_action = "Idle"  # Track current action (Idle, Drawing, Erasing)

# UI settings for a modern look
UI_COLOR = (0, 255, 0)  # Green for UI text
BUTTON_COLOR = (50, 150, 255)  # Modern blue for buttons
BUTTON_HOVER_COLOR = (100, 200, 255)  # Lighter blue for hover effect
BUTTON_TEXT_COLOR = (255, 255, 255)  # White for button text
STATUS_COLOR = (255, 100, 100)  # Coral for status messages
is_searching = False
mouse_x, mouse_y = 0, 0  # Track mouse position for hover effects
search_failed = False  # Track if the last search failed
show_help = False  # Toggle for help pop-up

# Color options for drawing
COLORS = {
    "White": (255, 255, 255),
    "Red": (0, 0, 255),
    "Green": (0, 255, 0),
    "Blue": (255, 0, 0),
    "Yellow": (0, 255, 255)
}
current_color_name = "White"

# Global WebDriver instance for Google search
driver = None

# Function to initialize or reuse WebDriver (now using Firefox instead of Chrome)
def initialize_driver():
    global driver
    if driver is None:
        try:
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument('--no-sandbox')
            firefox_options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)
            return True
        except Exception as e:
            print(f"Error initializing Firefox WebDriver: {e}")
            try:
                print("Trying to initialize Edge WebDriver as fallback...")
                from selenium.webdriver.edge.service import Service as EdgeService
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                edge_options = webdriver.EdgeOptions()
                driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=edge_options)
                return True
            except Exception as e2:
                print(f"Error initializing Edge WebDriver: {e2}")
                return False
    return True

# Function to enhance the sketch for better Google search recognition
def enhance_sketch(canvas):
    try:
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 10, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        enhanced = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
        return enhanced
    except Exception as e:
        print(f"Error enhancing sketch: {e}")
        return canvas

# Function to perform Google reverse image search
def perform_reverse_image_search(filename):
    global is_searching, search_failed, driver
    is_searching = True
    search_failed = False
    try:
        if not initialize_driver():
            raise Exception("Failed to initialize WebDriver")

        # Open Google Images
        driver.get("https://images.google.com/")

        # Handle cookie consent if it appears
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "L2AGLb"))
            )
            cookie_button.click()
        except:
            print("No cookie consent popup found or different element ID in Firefox.")
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
                )
                cookie_button.click()
            except:
                print("No cookie consent popup found with alternative method.")

        # Click the "Search by image" button (with Firefox-specific handling)
        try:
            # First attempt - common xpath
            camera_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Search by image' or @aria-label='Visual search']"))
            )
            camera_button.click()
        except Exception as e1:
            print(f"Failed to find 'Search by image' button with primary XPath. Trying alternative... Error: {e1}")
            try:
                # Second attempt - alternate xpath
                camera_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Search by image']"))
                )
                camera_button.click()
            except Exception as e2:
                print(f"Failed with second XPath. Trying third option... Error: {e2}")
                try:
                    # Third attempt - find by SVG path
                    camera_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.D9QHau svg"))
                    )
                    camera_button.click()
                except Exception as e3:
                    print(f"Failed with third approach. Final attempt... Error: {e3}")
                    # Fourth attempt - try to find by image alt text
                    camera_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//img[contains(@alt, 'camera')]"))
                    )
                    camera_button.click()

        # Upload the sketch file
        file_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        abs_file_path = os.path.abspath(filename)
        file_input.send_keys(abs_file_path)

        # Wait for the search results to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-ri='0']"))
        )

        print("Search results are displayed in the browser.")
    except Exception as e:
        print(f"Error in Google search process: {e}")
        search_failed = True
    finally:
        is_searching = False

# Function to save the canvas and start search
def save_and_search(canvas):
    try:
        timestamp = int(datetime.now().timestamp())
        filename = f"sketch_{timestamp}.png"
        enhanced_canvas = enhance_sketch(canvas)
        cv2.imwrite(filename, enhanced_canvas)
        search_thread = threading.Thread(target=perform_reverse_image_search, args=(filename,))
        search_thread.daemon = True
        search_thread.start()
        return filename
    except Exception as e:
        print(f"Error saving and searching: {e}")
        return None

# Function to save the sketch as an image file
def save_sketch(canvas):
    try:
        timestamp = int(datetime.now().timestamp())
        filename = f"saved_sketch_{timestamp}.png"
        cv2.imwrite(filename, canvas)
        print(f"Sketch saved as {filename}")
    except Exception as e:
        print(f"Error saving sketch: {e}")

# Function to clear temporary files
def clear_temp_files():
    try:
        for file in os.listdir():
            if file.startswith("sketch_") and file.endswith(".png"):
                os.remove(file)
    except Exception as e:
        print(f"Error clearing temporary files: {e}")

# Function to undo the last drawing action
def undo_last_action():
    global canvas, points_history
    try:
        if points_history:
            canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
            points_history.pop()  # Remove the last action
            # Redraw the remaining points
            for action in points_history:
                if action["type"] == "draw":
                    for i in range(1, len(action["points"])):
                        cv2.line(canvas, action["points"][i-1], action["points"][i], action["color"], DRAW_THICKNESS)
                elif action["type"] == "erase":
                    cv2.circle(canvas, action["point"], action["radius"], (0, 0, 0), -1)
    except Exception as e:
        print(f"Error undoing last action: {e}")

# Function to reset all settings
def reset_all():
    global canvas, points_history, DRAW_COLOR, current_color_name, DRAW_THICKNESS
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
    points_history.clear()
    DRAW_COLOR = (255, 255, 255)
    current_color_name = "White"
    DRAW_THICKNESS = 5
    print("All settings reset.")

# Mouse callback function for button clicks and hover effects
def mouse_callback(event, x, y, flags, param):
    global mouse_x, mouse_y, canvas, is_searching, current_color_name, DRAW_COLOR, DRAW_THICKNESS, show_help
    mouse_x, mouse_y = x, y

    if event == cv2.EVENT_LBUTTONDOWN:
        # Search Sketch button
        if 10 <= x <= 150 and 40 <= y <= 70:
            if not is_searching:
                print("Saving and searching...")
                save_and_search(canvas)
        # Retry Search button (if last search failed)
        elif 160 <= x <= 300 and 40 <= y <= 70 and search_failed:
            if not is_searching:
                print("Retrying search...")
                save_and_search(canvas)
        # Clear Canvas button
        elif 310 <= x <= 450 and 40 <= y <= 70:
            print("Clearing canvas...")
            canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
            points_history.clear()
        # Undo button
        elif 460 <= x <= 600 and 40 <= y <= 70:
            print("Undoing last action...")
            undo_last_action()
        # Reset All button
        elif 610 <= x <= 750 and 40 <= y <= 70:
            print("Resetting all settings...")
            reset_all()
        # Save Sketch button
        elif 10 <= x <= 150 and 80 <= y <= 110:
            print("Saving sketch...")
            save_sketch(canvas)
        # Help button
        elif 160 <= x <= 300 and 80 <= y <= 110:
            show_help = not show_help
        # Thickness adjustment buttons
        elif 310 <= x <= 350 and 80 <= y <= 110:  # Increase thickness
            DRAW_THICKNESS = min(20, DRAW_THICKNESS + 1)
            print(f"Thickness increased to {DRAW_THICKNESS}")
        elif 360 <= x <= 400 and 80 <= y <= 110:  # Decrease thickness
            DRAW_THICKNESS = max(1, DRAW_THICKNESS - 1)
            print(f"Thickness decreased to {DRAW_THICKNESS}")
        # Quit button
        elif 10 <= x <= 150 and canvas_height - 30 <= y <= canvas_height - 10:
            print("Exiting...")
            if driver:
                driver.quit()
            cap.release()
            cv2.destroyAllWindows()
            clear_temp_files()
            exit()
        # Color selection buttons
        for i, (color_name, color_value) in enumerate(COLORS.items()):
            btn_x = 410 + i * 60
            btn_y = 80
            if btn_x <= x <= btn_x + 50 and btn_y <= y <= btn_y + 20:
                current_color_name = color_name
                DRAW_COLOR = color_value
                print(f"Selected color: {color_name}")

# Main program
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, canvas_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, canvas_height)

# Set up the OpenCV window and maximize it
cv2.namedWindow("Air Drawing with Direct Image Search", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Air Drawing with Direct Image Search", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback("Air Drawing with Direct Image Search", mouse_callback)

print("Starting Air Drawing application...")
print("Using Firefox browser for image search (Edge as fallback)")
print("Use your index finger to draw")
print("Click the 'Search Sketch' button to search for similar images")
print("Click the 'Retry Search' button if the last search failed")
print("Click the 'Clear Canvas' button to clear the canvas")
print("Click the 'Undo' button to undo the last action")
print("Click the 'Reset All' button to reset all settings")
print("Click the 'Save Sketch' button to save the sketch")
print("Click the 'Thickness +/-' buttons to adjust brush size")
print("Click the 'Help' button to show/hide instructions")
print("Click the 'Quit' button to exit")

current_points = []  # To store points for the current drawing action

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
            )

            index_tip = hand_landmarks.landmark[8]
            h, w, _ = frame.shape
            x, y = int(index_tip.x * w), int(index_tip.y * h)

            index_up = index_tip.y < hand_landmarks.landmark[6].y
            middle_up = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
            ring_up = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
            pinky_up = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y

            if index_up and not middle_up and not ring_up and not pinky_up:
                current_action = "Drawing"
                if not drawing:
                    drawing = True
                    last_point = (x, y)
                    current_points = [last_point]
                else:
                    if last_point is not None:
                        cv2.line(canvas, last_point, (x, y), DRAW_COLOR, DRAW_THICKNESS)
                        current_points.append((x, y))
                        last_point = (x, y)
            elif index_up and middle_up and not ring_up and not pinky_up:
                current_action = "Erasing"
                erase_radius = 20
                cv2.circle(canvas, (x, y), erase_radius, (0, 0, 0), -1)
                points_history.append({"type": "erase", "point": (x, y), "radius": erase_radius})
                last_point = None
                current_points = []
            elif index_up and middle_up and ring_up and pinky_up:
                current_action = "Idle"
                if drawing:
                    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
                    points_history.clear()
                    last_point = None
                    drawing = False
                    current_points = []
            else:
                current_action = "Idle"
                if drawing:
                    drawing = False
                    if current_points:
                        points_history.append({"type": "draw", "points": current_points, "color": DRAW_COLOR})
                    current_points = []
                    last_point = None

    frame_with_canvas = cv2.addWeighted(frame, 1, canvas, 0.7, 0)

    # Draw status bar at the top with a modern look
    cv2.rectangle(frame_with_canvas, (0, 0), (canvas_width, 30), (30, 30, 30), -1)
    status_text = f"Mode: {current_action} | Color: {current_color_name} | Thickness: {DRAW_THICKNESS}"
    if is_searching:
        status_text += " | Searching Google Images..."
    elif search_failed:
        status_text += " | Search Failed"
    cv2.putText(frame_with_canvas, status_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, STATUS_COLOR, 2)

    # Draw instructions (hidden by default, toggled by Help button)
    if show_help:
        help_box = np.zeros((200, 300, 3), dtype=np.uint8)
        help_box[:] = (50, 50, 50)  # Dark gray background
        cv2.putText(help_box, "Index finger: Draw", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_COLOR, 2)
        cv2.putText(help_box, "Index+Middle: Erase", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_COLOR, 2)
        cv2.putText(help_box, "All fingers up: Clear", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_COLOR, 2)
        cv2.putText(help_box, "Click buttons to use", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, UI_COLOR, 2)
        frame_with_canvas[120:320, 10:310] = help_box

    # Draw buttons with hover effects
    # Search Sketch button
    search_btn_color = BUTTON_HOVER_COLOR if (10 <= mouse_x <= 150 and 40 <= mouse_y <= 70) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (10, 40), (150, 70), search_btn_color, -1)
    cv2.putText(frame_with_canvas, "Search Sketch", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Retry Search button (only visible if search failed)
    if search_failed:
        retry_btn_color = BUTTON_HOVER_COLOR if (160 <= mouse_x <= 300 and 40 <= mouse_y <= 70) else BUTTON_COLOR
        cv2.rectangle(frame_with_canvas, (160, 40), (300, 70), retry_btn_color, -1)
        cv2.putText(frame_with_canvas, "Retry Search", (165, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Clear Canvas button
    clear_btn_color = BUTTON_HOVER_COLOR if (310 <= mouse_x <= 450 and 40 <= mouse_y <= 70) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (310, 40), (450, 70), clear_btn_color, -1)
    cv2.putText(frame_with_canvas, "Clear Canvas", (315, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Undo button
    undo_btn_color = BUTTON_HOVER_COLOR if (460 <= mouse_x <= 600 and 40 <= mouse_y <= 70) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (460, 40), (600, 70), undo_btn_color, -1)
    cv2.putText(frame_with_canvas, "Undo", (465, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Reset All button
    reset_btn_color = BUTTON_HOVER_COLOR if (610 <= mouse_x <= 750 and 40 <= mouse_y <= 70) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (610, 40), (750, 70), reset_btn_color, -1)
    cv2.putText(frame_with_canvas, "Reset All", (615, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Save Sketch button
    save_btn_color = BUTTON_HOVER_COLOR if (10 <= mouse_x <= 150 and 80 <= mouse_y <= 110) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (10, 80), (150, 110), save_btn_color, -1)
    cv2.putText(frame_with_canvas, "Save Sketch", (15, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Help button
    help_btn_color = BUTTON_HOVER_COLOR if (160 <= mouse_x <= 300 and 80 <= mouse_y <= 110) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (160, 80), (300, 110), help_btn_color, -1)
    cv2.putText(frame_with_canvas, "Help", (165, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Thickness adjustment buttons
    inc_thick_btn_color = BUTTON_HOVER_COLOR if (310 <= mouse_x <= 350 and 80 <= mouse_y <= 110) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (310, 80), (350, 110), inc_thick_btn_color, -1)
    cv2.putText(frame_with_canvas, "+", (325, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    dec_thick_btn_color = BUTTON_HOVER_COLOR if (360 <= mouse_x <= 400 and 80 <= mouse_y <= 110) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (360, 80), (400, 110), dec_thick_btn_color, -1)
    cv2.putText(frame_with_canvas, "-", (375, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    # Color selection buttons
    for i, (color_name, color_value) in enumerate(COLORS.items()):
        btn_x = 410 + i * 60
        btn_y = 80
        color_btn_color = color_value if (btn_x <= mouse_x <= btn_x + 50 and btn_y <= mouse_y <= btn_y + 20) else color_value
        cv2.rectangle(frame_with_canvas, (btn_x, btn_y), (btn_x + 50, btn_y + 20), color_btn_color, -1)
        cv2.putText(frame_with_canvas, color_name, (btn_x + 5, btn_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

    # Quit button
    quit_btn_color = BUTTON_HOVER_COLOR if (10 <= mouse_x <= 150 and canvas_height - 30 <= mouse_y <= canvas_height - 10) else BUTTON_COLOR
    cv2.rectangle(frame_with_canvas, (10, canvas_height - 30), (150, canvas_height - 10), quit_btn_color, -1)
    cv2.putText(frame_with_canvas, "Quit", (15, canvas_height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BUTTON_TEXT_COLOR, 2)

    cv2.imshow("Air Drawing with Direct Image Search", frame_with_canvas)

    # Check for 'q' key to quit (as a fallback)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("Exiting...")
        if driver:
            driver.quit()
        break

cap.release()
cv2.destroyAllWindows()
clear_temp_files()
if driver:
    driver.quit()