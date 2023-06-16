import psutil
import logging
import os
import sys


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


def is_running(programme_name: str = '') -> bool:
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == programme_name and process.status() in ['running', 'sleeping']:
            return True
    return False
