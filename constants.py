# ==============================================
# FLASK APP constants
# ==============================================
import os

FLASK_LOGGER = 'LOGGER'
FLASK_DATABASE = 'DATABASE_INSTANCE'


# ==============================================
# Database constants
# ==============================================
URI = "uri"
LOCALHOST = "localhost"
COLLECTION_SCHED_JOBS = "collection_scheduled_jobs"


# ==============================================
# GLOBAL constants
# ==============================================
IP = 'ip'
ID = '_id'
PORT = 'port'
DATA = 'data'
ERROR = 'error'
STATUS = 'status'
DETAILS = 'details'
USER_ID = "user_id"
MATCHED = 'matched'
DATABASE = "database"
MESSAGING = 'messaging'

# ==============================================
# Mailing Event constants
# ==============================================
DAY = "day"
NAME = "name"
TEXT = "text"
DATE = "date"
TIME = "time"
TYPE = "type"
BODY = "body"
DAILY = "daily"
WEEKLY = "weekly"
REPEAT = "repeat"
ACTIVE = "active"
SUBJECT = "subject"
SERVICE = "service"
MONTHLY = "monthly"
SEND_TO = "send_to"
RESPONSE = "response"
DOWNLOAD = "download"
FREQUENCY = "frequency"
END_POINT = "end_point"
ATTACHMENT = "attachment"
SERVICE_NAME = "service_name"
DOWNLOADABLE = "downloadable"
MAILING_EVENT_ID = "mailing_event_id"


# ==============================================
# Mailing Event Scheduler constants
# ==============================================
INTERVAL = "interval"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==============================================
# Report Directory constants
# ==============================================
DIR_EMAIL_SERVICE = os.path.abspath(os.path.join(os.getcwd()))
DIR_STATIC = os.path.join(DIR_EMAIL_SERVICE, 'static')
DIR_TEMP = os.path.join(DIR_STATIC, 'temp')

# ==============================================
# TIME AND DATE CONSTANTS
# ==============================================
TIME_FORMAT_H_M_S_COLON = '%H:%M:%S'
TIME_FORMAT_H_M_S_DASH = '%H-%M-%S'
TIME_FORMAT_H_M_COLON = '%H:%M'
TIME_FORMAT_H_M_DASH = '%H-%M'
DATE_FORMAT_D_M_Y = '%d-%m-%Y'
DATE_FORMAT_Y_M_D = '%Y-%m-%d'
DATE_TIME_FORMAT_D_M_Y_H_M_S_COLON = '%d-%m-%Y %H:%M:%S'
DATE_TIME_FORMAT_D_M_Y_H_M_S_DASH = '%d-%m-%Y %H-%M-%S'
