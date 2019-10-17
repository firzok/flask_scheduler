"""
Configurations for mongodb

Add your own details for database

"""

config = {
    "database": {
        "required": True,
        "uri": "localhost:27017",
        "name": "DatabaseName",
        "collection": "emailing_events",
        "collection_scheduled_jobs": "scheduled_jobs"
    }
}
