from enum import Enum


class HttpCode(Enum):
    SUCCESS_CODE = 200
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class Error:

    error_stores = {
        200: "okay",
        400: "Invalid request",
        403: "Request Not Allowed",
        404: "Record Not Found",
        500: "Internal server error",
        503: "Server is not responding"
    }

    def __init__(self, code, details=None, message=None):
        self._code = code.value
        if message is None:
            self._msg = Error.error_stores[code.value]
        else:
            self._msg = message
        self._details = details

    def update_msg(self, msg):
        self._msg = msg

    def get_code(self):
        return self._code

    def get_msg(self):
        return self._msg

    def get_details(self):
        return self._details

    def __str__(self):
        return f"[Code]: {self._code} - [Msg] : {self._msg} - [Details] : {self._details}"
