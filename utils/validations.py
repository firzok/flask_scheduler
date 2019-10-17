
import os
import re

from bson import ObjectId
from bson.errors import InvalidId

from flask_scheduler.utils.errors import Error, HttpCode


def is_valid_object_id(_id):
    """
    return ObjectId if _id is valid
    Args:
        _id: str, id of document

    Returns: ObjectId, instance

    """
    try:
        new_id = ObjectId(_id)
        return new_id
    except (InvalidId, TypeError):
        return False


def is_file_exist(file_path):
    """
    if file exist return True else false
    Args:
        file_path: str, path of file

    Returns: boolean

    """
    return os.path.exists(file_path)


def is_dict(_object):
    """
    return true if type of object is dict
    Args:
        _object: any data

    Returns: boolean

    """
    return type(_object) is dict


def is_list(_object):
    """
    return true if type of object is list
    Args:
        _object: any data

    Returns: boolean

    """
    return type(_object) is list


def is_str(_object):
    """
    return true if type of object is str
    Args:
        _object: any data

    Returns: boolean

    """
    return type(_object) is str


def validate_fields(data, fields_list):
    if not is_list(fields_list):
        return Error(HttpCode.BAD_REQUEST, details='fields_list is not type list')
    if not is_dict(data):
        return Error(HttpCode.BAD_REQUEST, details='data is not type dict')
    for field in fields_list:
        if field not in data:
            return Error(HttpCode.BAD_REQUEST, details=f'`{field}` is missing')
    return True


def is_valid_email(email):

    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if re.search(regex, email):
        return True
    return False
