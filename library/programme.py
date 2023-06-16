from PIL import Image
import psutil
import pyautogui as auto_gui
import logging
import os
import sys
import socket
import subprocess
import time


def launch_futu_opend(project_dir):
    logging.debug("Start launching Futu-OpenD.")

    # define programme name (only concern linux and windows)
    operation_system = sys.platform
    programme_name = 'FutuOpenD' if operation_system == 'linux' else 'FutuOpenD.exe'
    programme_path = os.path.join(project_dir, 'futu_openD', programme_name)

    # check if already run
    if is_running(programme_name):
        logging.debug(f"{programme_name} is already run.")
    else:
        logging.debug(f"Launch Futu-OpenD.")
        os.system(programme_path) if operation_system == 'linux' else os.startfile(programme_path)


def launch_tws(project_dir, user_name: str, password: str):
    # check host
    server_address = '192.168.1.101'
    if socket.gethostbyname(socket.gethostname()) != server_address:
        logging.debug("This is not a server, please make sure IB TWS is running and accepted this connection.")
        return

    # delete 'setup' file in order not to affected by the size of the TWS app
    file_path = r'c:\Jts\jts.ini'
    if os.path.isfile(file_path):
        logging.debug("Deleting setup file...")
        os.remove(file_path)

    # launch TWS
    subprocess.Popen([r'C:\Jts\tws.exe',
                      f'username={user_name}',
                      f'password={password}',
                      'enter-readonly=True'])
    logging.info("Allow 30 seconds for TWS startup...")
    time.sleep(30)

    # search 2-factors authentication
    img_path = os.path.join(project_dir, 'library', 'images', 'ib_2_factors_authentication.png')
    while True:
        element = search_image_on_screen(img_path, confidence=0.95, grayscale=True)
        if element:
            break
        logging.info("IB TWS 2 factors authentication not found, try again after 5 seconds.")
        time.sleep(5)


def is_running(programme_name: str = '') -> bool:
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == programme_name and process.status() in ['running', 'sleeping']:
            return True
    return False


def search_image_on_screen(img_path: os.path, confidence: float, grayscale: bool,
                           max_scale: float = 1.5, scale_factor: float = 0.01):
    # open image, define size
    image = Image.open(img_path)
    image_width, image_height = image.size
    searching_w, searching_h = image.size
    screen_width, screen_height = auto_gui.size()

    # search
    vector = 1
    for index in range(1, 9999):
        logging.info(f"Searching {os.path.basename(img_path)}, size: {searching_w}x{searching_h}")
        element = auto_gui.locateOnScreen(image, confidence=confidence, grayscale=grayscale)
        if element:
            return element

        # searching
        searching_w = image_width * (1 + index*scale_factor) * vector
        searching_h = image_height * (1 + index*scale_factor) * vector

        # if searching size is too large
        if any([searching_w >= screen_width,
                searching_h >= screen_height,
                searching_w >= image_width * max_scale]):
            vector = -1
            searching_w = image_width
            searching_h = image_height

        # if search size is too small
        elif searching_w <= image_width / max_scale:
            return None

        image = image.resize(
            (int(searching_w), int(searching_h))
        )
