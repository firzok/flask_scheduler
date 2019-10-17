from pymongo import MongoClient

from flask_scheduler.config import config


def get_database_instance():
    """
    Creates a mongodb connection
    :return:
    """
    __db = config['database']
    connection_str = "mongodb://{0}".format(__db['uri'])
    connection = MongoClient(connection_str)
    return connection
