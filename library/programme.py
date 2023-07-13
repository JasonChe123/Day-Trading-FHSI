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
    programme_name = 'FutuOpenD.exe'
    programme_path = os.path.join(project_dir, 'futu_openD', programme_name)

    # check if already run
    if is_running(programme_name):
        logging.debug(f"{programme_name} is already run.")
    else:
        logging.debug(f"Launch Futu-OpenD.")
        os.system(os.path.splitext(programme_path)[0]) if operation_system == 'linux' else os.startfile(programme_path)


def launch_tws(project_dir, user_name: str, password: str):
    if is_running(programme_name='tws'):
        logging.critical(f"TWS is already run.")
        return

    # define path
    if sys.platform == 'win32':
        tws_path = r'C:\Jts\tws.exe'
        init_file = r'C:\Jts\jts.ini'
    elif sys.platform == 'linux':
        tws_path = os.path.join(project_dir, 'ib_tws', 'Jts', 'tws')
        init_file = os.path.join(project_dir, 'ib_tws', 'Jts', 'jts.ini')
    else:
        raise RuntimeError(f"This OS is {sys.platform}, please check the TWS file location.")

    # remove the initial setup file
    if os.path.isfile(init_file):
        logging.debug("Deleting setup file...")
        os.remove(init_file)

    # launch TWS
    subprocess.Popen([tws_path, f'username={user_name}', f'password={password}', 'enter-readonly=true'])
    logging.info("Allow 60 seconds for TWS startup...")
    time.sleep(10)

    # search 2-factors authentication
    img_path = os.path.join(project_dir, 'library', 'images', 'ib_2_factors_authentication.png')
    while True:
        element = search_image_on_screen(img_path, confidence=0.9, grayscale=True)
        if element:
            break
        logging.info("IB TWS 2 factors authentication not found, try again after 5 seconds.")
        print("IB TWS 2 factors authentication not found, try again after 5 seconds.")
        time.sleep(5)

    # simulate clicking event
    left, top, width, height = element
    auto_gui.moveTo((left, top), duration=0.2, tween=auto_gui.easeInOutQuad)
    auto_gui.moveTo((left + width, top), duration=0.2, tween=auto_gui.easeInOutQuad)
    auto_gui.moveTo((left + width, top + height), duration=0.2, tween=auto_gui.easeInOutQuad)
    auto_gui.moveTo((left, top + height), duration=0.2, tween=auto_gui.easeInOutQuad)
    auto_gui.moveTo((left, top), duration=0.2, tween=auto_gui.easeInOutQuad)
    x = left + width*5/6
    y = top + height*15/16
    auto_gui.moveTo((x, y), duration=0.2, tween=auto_gui.easeInOutQuad)
    auto_gui.click()


def is_running(programme_name: str = '') -> bool:
    programme_name = (os.path.splitext(programme_name)[0].lower())
    for process in psutil.process_iter(['pid', 'name']):
        if os.path.splitext(process.info['name'])[0].lower() == programme_name:
            if process.status() in ['running', 'sleeping']:
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
    vector = 1  # to define searching for enlarged size or reduced size
    tried = 0
    while True:
        logging.info(f"Searching {os.path.basename(img_path)}, size: {searching_w}x{searching_h}")
        print(f"Searching {os.path.basename(img_path)}, size: {image.size}")
        element = auto_gui.locateOnScreen(image, confidence=confidence, grayscale=grayscale)
        if element:
            print(f"{image} found.")
            return element

        # searching for different sizes
        tried += 1
        searching_w = image_width * (1 + tried*scale_factor*vector)
        searching_h = image_height * (1 + tried*scale_factor*vector)

        # if searching size is too large
        if vector == 1 and any([searching_w >= screen_width,
                                searching_h >= screen_height,
                                searching_w >= image_width * max_scale]):
            vector = -1  # search for reduced size
            tried = 0
            # reset size
            searching_w = image_width
            searching_h = image_height

        # if search size is too small, end searching loop
        elif searching_w < image_width / max_scale:
            return None

        # resize for the next loop
        image = image.resize((int(searching_w), int(searching_h)))
