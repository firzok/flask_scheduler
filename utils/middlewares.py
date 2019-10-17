import inspect

import bson
from bson import ObjectId
from flask import current_app
from pymongo.errors import (
    ConnectionFailure,
    CursorNotFound,
    DuplicateKeyError
)
from werkzeug.exceptions import BadRequest
from werkzeug.routing import BaseConverter

from flask_scheduler import constants
from flask_scheduler.utils.errors import HttpCode, Error
from flask_scheduler.utils.validations import is_valid_object_id


class ObjectIdConverter(BaseConverter):

    def to_python(self, value):
        try:
            return bson.ObjectId(value)
        except bson.errors.InvalidId as e:
            raise BadRequest(e)

    def to_url(self, value):
        return str(value)

    @classmethod
    def register_in_flask(cls, flask_app):
        flask_app.url_map.converters['ObjectId'] = cls


class DatabaseMiddleware:
    leave_it = [dict]

    def __init__(self):
        pass

    @staticmethod
    def exec_query(function, **kwargs):
        output = DatabaseMiddleware.process_query(function, **kwargs)

        if type(output) is Error:
            # current_app.config['LOGGER'].make_error(output)
            return output

        if output is None:
            output = dict({})

        return output

    @staticmethod
    def process_query(function, **kwargs):
        try:
            if constants.ID in kwargs['filter'] and type(kwargs['filter'][constants.ID]) is str:
                _id = is_valid_object_id(kwargs['filter'][constants.ID])
                if not _id:
                    return Error(code=HttpCode.BAD_REQUEST, details="Invalid ID")

                kwargs['filter'][constants.ID] = _id

            output = function(**kwargs)
            return DatabaseMiddleware.post_processing(output)

        except ConnectionFailure as e:
            print("Connection Failure in DatabaseMiddleware > process_query")
            return Error(code=HttpCode.SERVICE_UNAVAILABLE, details=str(e))

        except CursorNotFound as e:
            print("Cursor Error in DatabaseMiddleware > process_query")
            return Error(code=HttpCode.NOT_FOUND, details=str(e))

        except DuplicateKeyError:
            print("Duplicate Key Error in DatabaseMiddleware > process_query")
            return Error(HttpCode.BAD_REQUEST, details='Duplicate key error')

        except Exception as e:
            # current_app.config[constants.FLASK_LOGGER].make_log(str(e))
            return Error(code=HttpCode.INTERNAL_SERVER_ERROR, details=str(e))

    @staticmethod
    def post_processing(data):
        if type(data) is Error:
            return data

        if data is not None:
            _output = []

            if type(data) in DatabaseMiddleware.leave_it:
                _output = data
            else:
                for out in data:
                    if constants.ID in out and type(out[constants.ID]) is ObjectId:
                        out['_id'] = str(out['_id'])
                    _output.append(out)

            return _output


class Inspection(object):

    def __init__(self, meta=None):
        if 'log_args' not in meta.keys():
            meta['log_args'] = True

        if 'log_kwargs' not in meta.keys():
            meta['log_kwargs'] = True

        assert ("cls_name" in meta.keys()), "CLASS NAME IS MISSING, PLEASE PROVIDE CLASS NAME IN META DATA"

        self.__meta = meta

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)

        if inspect.ismethod(attr):
            def log_function_call(*args, **kwargs):
                _base_str = f"Class Name={self.__meta['cls_name']} " \
                            f"| Function Name={attr.__name__} "

                _str = _base_str

                if self.__meta['log_args']:
                    _str = _base_str + f"| Args={args} "

                if self.__meta['log_kwargs']:
                    _str += f"| kwargs = {kwargs}"

                # current_app.config[constants.FLASK_LOGGER].make_log(_str)
                result = attr(*args, **kwargs)

                if type(result) is Error:
                    print(f'{_base_str}- Error: {result.get_code()} - {result.get_msg()}')
                else:
                    _log_result = f'{result}'
                    if len(_log_result) > 100:
                        _log_result = _log_result[:20] + '.' * 10 + _log_result[-20:]
                    print(f'{_base_str}- output: {_log_result}')

                return result

            return log_function_call
        return attr


class ResponseWrapper:

    @staticmethod
    def make_response(output):
        if type(output) is Error:
            if output.get_details():
                return {constants.ERROR: output.get_details()}, output.get_code()
            return {constants.ERROR: output.get_msg()}, output.get_code()

        if type(output) is not dict:
            return {constants.DATA: output}, HttpCode.SUCCESS_CODE.value

        if constants.DATA not in output:
            return {constants.DATA: output}, HttpCode.SUCCESS_CODE.value

        return output, HttpCode.SUCCESS_CODE.value
