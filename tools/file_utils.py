import _pickle as pickle
import datetime as dt
import json
import os

from flask import current_app

from flask_scheduler import constants


def check_and_create_dir(dir_path):
    """
    check if directory exist, if not then create directory
    Args:
        dir_path: path to directory
    Returns: None
    """
    if not os.path.isdir(dir_path):
        current_app.config[constants.FLASK_LOGGER].make_log(
            msg=f"check_and_create_dir - dir: {dir_path} does not exist, creating one.")
        os.makedirs(dir_path)


def load_json_file(filename):
    """
    return json file as an object
    Args:
        filename: path of json file
    Returns: JSON/dictionary object
    """
    try:
        with open(filename) as j:
            data = json.load(j)
        return data
    except FileNotFoundError as err:
        current_app.config[constants.FLASK_LOGGER].make_error(
            msg=f"load_json_file camera - Error in loading json file: {filename}, error: {err}")
        return None


def get_num_files(folder_path):
    """
    return number of files in then given path
    Args:
        folder_path: path to folder
    Returns: integer number of files
    """
    return len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])


def create_dir_wrt_date(base_path):
    """
    create directory in the base path according to system date
    Args:
        base_path: string, path of folder
    Returns:
    """
    check_and_create_dir(os.path.join(base_path, dt.datetime.now().now().strftime(constants.DATE_FORMAT_D_M_Y)))


def load_pkl_as_dict(filename):
    """
    load pkl file as dictionary object
    Args:
           filename: string name of file    Returns:
        dictionary object
        """

    with open(filename, 'rb') as handler:
        data = pickle.load(handler)
    return data


def save_dict_as_pkl(data, filename, target_path=None):
    """
    save object 'data' as pkl file
    Args:
       data: dictionary object
       filename: name of the pickle file
       target_path: location of directory to save pickle file
    Returns:
    """
    if target_path is None:
        target_path = './'
    if filename.split('.')[-1] not in ['.p', 'pkl']:
        filename += '.pkl'
    with open(os.path.join(target_path, filename), 'wb') as handler:
        pickle.dump(data, handler)


def remove_file(file_path):
    """
    delete/remove the file from storage
    Args:
        file_path: str, path of file
    """
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
    except PermissionError:
        pass
