"""

[Original] https://schedule.readthedocs.io/en/stable/
Eddied to make it usable with flask threads.


An in-process scheduler for periodic jobs that uses the builder pattern
for configuration. Schedule lets you run Python functions (or any other
callable) periodically at pre-determined intervals using a simple,
human-friendly syntax.

Requirement:
Database with configurations in config

Usage:
    # >>> import schedule
    # >>> import time
    #
    # >>> def job(message='stuff'):
    # >>>     print("I'm working on:", message)
    #
    # >>> schedule.every(10).minutes.do(job)
    # >>> schedule.every().hour.do(job, message='things')
    # >>> schedule.every().day.at("10:30").do(job)
    #
    # >>> while True:
    # >>>     schedule.run_pending()
    # >>>     time.sleep(1)
"""
import datetime
import functools
import random
import re
import threading
import time
from builtins import Exception, object, exit, type

from flask_scheduler import constants
from flask_scheduler.tools.file_utils import check_and_create_dir
from flask_scheduler.utils.errors import HttpCode, Error
from flask_scheduler.utils.flask_thread import FlaskThread
from flask_scheduler.utils.middlewares import DatabaseMiddleware
from flask import current_app
from pymongo import ASCENDING, errors

from flask_scheduler.config import config


class ScheduleError(Exception):
    """Base schedule exception"""
    pass


class ScheduleValueError(ScheduleError):
    """Base schedule value error"""
    pass


class IntervalError(ScheduleValueError):
    """An improper interval was used"""
    pass


class Scheduler(object):
    COLLECTION_NAME = config['database']['collection']
    __index_key = [(constants.NAME, ASCENDING)]
    __index_name = 'mailing_events_index'
    __index_unique = True

    FILTER_KEY_NAME = 'filter'

    def __init__(self):

        self.jobs = []

        __res = Scheduler.create_collection()
        if type(__res) is Error:
            print("Unable to create a db connection.")
            exit(0)

        self.__create_all_pre_req_directories()

    def __create_all_pre_req_directories(self):
        """
        Creates all pre requisite directories
        Returns:

        """

        # For storing temporary files like reports for sending email attachment
        check_and_create_dir(constants.DIR_TEMP)

    def remove_job(self, job_id):
        """
            Removes a job in DB and from the schedule

            Loops over all jobs to get the job that needs to be removed then removes it from the DB,
            if that is successful then it is removed from the list of jobs too.

            Args:
                job_id: str

            Returns:
                True if successfully removed /False if no job was found or Error if DB operation failed
            """

        for idx, job in enumerate(self.jobs):

            if job.id == job_id:

                _output = DatabaseMiddleware.exec_query(Scheduler.__remove_mailing_event, filter={constants.ID: job_id})

                if isinstance(_output, Error):
                    print(f"Scheduler#remove_job - Error in removing scheduled job, details: {_output.get_details()}")
                    return _output

                self.jobs.pop(idx)
                print(f"Scheduler#remove_job - Scheduled job with id:'{job_id}' removed.")

                return True
        return False

    def get_mailing_event(self, filter):
        """
        Gets the mailing events from DB, if _id is not provided all mailing events are get
        Args:
            filter: filter for DB

        Returns:
            mailing events
        """

        _output = DatabaseMiddleware.exec_query(Scheduler.__get_mailing_event, filter=filter)

        if isinstance(_output, Error):
            print(f"Scheduler#get_mailing_event - Error getting scheduled job from DB, details: {_output.get_details()}")
        return _output

    @staticmethod
    def create_collection():
        try:
            __database = config['database']['name']
            __db = current_app.config[constants.FLASK_DATABASE][__database]
            # check if collection already exist
            __collections_list = __db.list_collection_names()
            if Scheduler.COLLECTION_NAME not in __collections_list:
                # creating collection
                __db.create_collection(Scheduler.COLLECTION_NAME)
                Scheduler.get_connection().create_index(Scheduler.__index_key,
                                                        name=Scheduler.__index_name,
                                                        unique=Scheduler.__index_unique)
        except errors.ConnectionFailure:
            return Error(code=HttpCode.SERVICE_UNAVAILABLE, details='Unable to Connect to database')

    @staticmethod
    def get_connection():
        __database = config['database']['name']
        return current_app.config[constants.FLASK_DATABASE][__database][Scheduler.COLLECTION_NAME]

    @staticmethod
    def __get_mailing_event(**kwargs):
        return Scheduler.get_connection().find(kwargs[Scheduler.FILTER_KEY_NAME])

    @staticmethod
    def __add_mailing_event(**kwargs):
        return {constants.ID: str(Scheduler.get_connection().save(kwargs[Scheduler.FILTER_KEY_NAME]))}

    @staticmethod
    def __remove_mailing_event(**kwargs):
        return Scheduler.get_connection().remove(kwargs[Scheduler.FILTER_KEY_NAME])

    @staticmethod
    def update_mailing_event(**kwargs):
        return {constants.MATCHED: Scheduler.get_connection().update_many(**kwargs).matched_count}

    def run_all(self, delay_seconds=0):
        """Run all jobs regardless if they are scheduled to run or not.

        A delay of `delay` seconds is added between each job. This helps
        distribute system load generated by the jobs more evenly
        over time."""
        print(f"Scheduler#run_all - Running *all* {len(self.jobs)} jobs with {delay_seconds} delay in between")

        for job in self.jobs:
            job.run()
            time.sleep(delay_seconds)

    def run_pending(self):
        """Run all jobs that are scheduled to run.

        Please note that it is *intended behavior that tick() does not
        run missed jobs*. For example, if you've registered a job that
        should run every minute and you only call tick() in one hour
        increments then your job won't be run 60 times in between but
        only once.
        """
        runnable_jobs = (job for job in self.jobs if job.should_run)
        for job in sorted(runnable_jobs):
            job.run()

    def run_continuously(self, interval=1):
        """Continuously run, while executing pending jobs at each elapsed
        time interval.

        @return cease_continuous_run: threading.Event which can be set to
        cease continuous run.

        Please note that it is *intended behavior that run_continuously()
        does not run missed jobs*. For example, if you've registered a job
        that should run every minute and you set a continuous run interval
        of one hour then your job won't be run 60 times at each interval but
        only once.
        """
        cease_continuous_run = threading.Event()

        class ScheduleThread(FlaskThread):

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.app = current_app._get_current_object()

            def run(cls):
                with cls.app.app_context():
                    with cls.app.test_request_context():
                        while not cease_continuous_run.is_set():
                            self.run_pending()
                            time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()

    def add_to_db(self, _data):
        """
        Adds the current job to db so to load them again when the service restarts
        Args:
            _data:

        Returns:
            ID of job or Error
        """

        _output = DatabaseMiddleware.exec_query(Scheduler.__add_mailing_event, filter=_data)

        if isinstance(_output, Error):
            print(f"Scheduler#add_to_db - Error in saving scheduled job, details: {_output.get_details()}")
            return {constants.ERROR: _output.get_msg(), constants.DETAILS: _output.get_details()}

        return _output[constants.ID]

    def clear(self):
        """Deletes all scheduled jobs but keeps them in the DB"""
        del self.jobs[:]

    def every(self, data=None, interval=1):
        """Schedule a new periodic job. Also adds the job to db."""
        _id = self.add_to_db(data)

        if isinstance(_id, Error):
            print(f"Scheduler#every - Error in saving scheduled job to DB")

        job = Job(interval, _id=_id)
        self.jobs.append(job)
        return job

    @property
    def next_run(self):
        """Datetime when the next job should run."""
        return min(self.jobs).next_run

    @property
    def idle_seconds(self):
        """Number of seconds until `next_run`."""
        return (self.next_run - datetime.datetime.now()).total_seconds()


class Job(object):
    """A periodic job as used by `Scheduler`."""

    def __init__(self, interval, _id=None):
        self.interval = interval  # pause interval * unit between runs
        self.latest = None  # upper limit to the interval
        self.job_func = None  # the job job_func to run
        self.unit = None  # time units, e.g. 'minutes', 'hours', ...
        self.at_time = None  # optional time at which this job runs
        self.last_run = None  # datetime of the last run
        self.next_run = None  # datetime of the next run
        self.period = None  # timedelta between runs, only valid for
        self.start_day = None  # Specific day of the week to start on
        self.tags = set()  # unique set of tags for the job

        self.id = _id

    def __lt__(self, other):
        """PeriodicJobs are sortable based on the scheduled time
        they run next."""
        return self.next_run < other.next_run

    def __repr__(self):
        def format_time(t):
            return t.strftime('%Y-%m-%d %H:%M:%S') if t else '[never]'

        timestats = '(last run: %s, next run: %s)' % (
            format_time(self.last_run), format_time(self.next_run))

        if hasattr(self.job_func, '__name__'):
            job_func_name = self.job_func.__name__
        else:
            job_func_name = repr(self.job_func)
        args = [repr(x) for x in self.job_func.args]
        kwargs = ['%s=%s' % (k, repr(v))
                  for k, v in self.job_func.keywords.items()]
        call_repr = job_func_name + '(' + ', '.join(args + kwargs) + ')'

        if self.at_time is not None:
            return 'Every %s %s at %s do %s %s' % (
                self.interval,
                self.unit[:-1] if self.interval == 1 else self.unit,
                self.at_time, call_repr, timestats)
        else:
            fmt = (
                    'Every %(interval)s ' +
                    ('to %(latest)s ' if self.latest is not None else '') +
                    '%(unit)s do %(call_repr)s %(timestats)s'
            )

            return fmt % dict(
                interval=self.interval,
                latest=self.latest,
                unit=(self.unit[:-1] if self.interval == 1 else self.unit),
                call_repr=call_repr,
                timestats=timestats
            )

    @property
    def second(self):
        assert self.interval == 1
        return self.seconds

    @property
    def seconds(self):
        self.unit = 'seconds'
        return self

    @property
    def minute(self):
        assert self.interval == 1
        return self.minutes

    @property
    def minutes(self):
        self.unit = 'minutes'
        return self

    @property
    def hour(self):
        assert self.interval == 1
        return self.hours

    @property
    def hours(self):
        self.unit = 'hours'
        return self

    @property
    def day(self):
        assert self.interval == 1
        return self.days

    @property
    def days(self):
        self.unit = 'days'
        return self

    @property
    def week(self):
        assert self.interval == 1
        return self.weeks

    @property
    def weeks(self):
        self.unit = 'weeks'
        return self

    @property
    def monday(self):
        assert self.interval == 1
        self.start_day = 'monday'
        return self.weeks

    @property
    def tuesday(self):
        assert self.interval == 1
        self.start_day = 'tuesday'
        return self.weeks

    @property
    def wednesday(self):
        assert self.interval == 1
        self.start_day = 'wednesday'
        return self.weeks

    @property
    def thursday(self):
        assert self.interval == 1
        self.start_day = 'thursday'
        return self.weeks

    @property
    def friday(self):
        assert self.interval == 1
        self.start_day = 'friday'
        return self.weeks

    @property
    def saturday(self):
        assert self.interval == 1
        self.start_day = 'saturday'
        return self.weeks

    @property
    def sunday(self):
        assert self.interval == 1
        self.start_day = 'sunday'
        return self.weeks

    def at(self, time_str):
        """
        Specify a particular time that the job should be run at.

        :param time_str: A string in one of the following formats: `HH:MM:SS`,
            `HH:MM`,`:MM`, `:SS`. The format must make sense given how often
            the job is repeating; for example, a job that repeats every minute
            should not be given a string in the form `HH:MM:SS`. The difference
            between `:MM` and `:SS` is inferred from the selected time-unit
            (e.g. `every().hour.at(':30')` vs. `every().minute.at(':30')`).
        :return: The invoked job instance
        """
        if (self.unit not in ('days', 'hours', 'minutes')
                and not self.start_day):
            raise ScheduleValueError('Invalid unit')
        if not isinstance(time_str, str):
            raise TypeError('at() should be passed a string')
        if self.unit == 'days' or self.start_day:
            if not re.match(r'^([0-2]\d:)?[0-5]\d:[0-5]\d$', time_str):
                raise ScheduleValueError('Invalid time format')
        if self.unit == 'hours':
            if not re.match(r'^([0-5]\d)?:[0-5]\d$', time_str):
                raise ScheduleValueError(('Invalid time format for'
                                          ' an hourly job'))
        if self.unit == 'minutes':
            if not re.match(r'^:[0-5]\d$', time_str):
                raise ScheduleValueError(('Invalid time format for'
                                          ' a minutely job'))
        time_values = time_str.split(':')
        if len(time_values) == 3:
            hour, minute, second = time_values
        elif len(time_values) == 2 and self.unit == 'minutes':
            hour = 0
            minute = 0
            _, second = time_values
        else:
            hour, minute = time_values
            second = 0
        if self.unit == 'days' or self.start_day:
            hour = int(hour)
            if not (0 <= hour <= 23):
                raise ScheduleValueError('Invalid number of hours')
        elif self.unit == 'hours':
            hour = 0
        elif self.unit == 'minutes':
            hour = 0
            minute = 0
        minute = int(minute)
        second = int(second)
        self.at_time = datetime.time(hour, minute, second)
        return self

    def do(self, job_func, *args, **kwargs):
        """Specifies the job_func that should be called every time the
        job runs.

        Any additional arguments are passed on to job_func when
        the job runs.
        """
        self.job_func = functools.partial(job_func, *args, **kwargs)
        functools.update_wrapper(self.job_func, job_func)
        self._schedule_next_run()
        return self

    @property
    def should_run(self):
        """True if the job should be run now."""
        return datetime.datetime.now() >= self.next_run

    def run(self):
        """Run the job and immediately reschedule it."""
        print(f"Job#run - Running job {self}")

        self.job_func()
        self.last_run = datetime.datetime.now()
        self._schedule_next_run()

    def _schedule_next_run(self):
        """
        Compute the instant when this job should run next.
        """
        if self.unit not in ('seconds', 'minutes', 'hours', 'days', 'weeks'):
            raise ScheduleValueError('Invalid unit')

        if self.latest is not None:
            if not (self.latest >= self.interval):
                raise ScheduleError('`latest` is greater than `interval`')
            interval = random.randint(self.interval, self.latest)
        else:
            interval = self.interval

        self.period = datetime.timedelta(**{self.unit: interval})
        self.next_run = datetime.datetime.now() + self.period
        if self.start_day is not None:
            if self.unit != 'weeks':
                raise ScheduleValueError('`unit` should be \'weeks\'')
            weekdays = (
                'monday',
                'tuesday',
                'wednesday',
                'thursday',
                'friday',
                'saturday',
                'sunday'
            )
            if self.start_day not in weekdays:
                raise ScheduleValueError('Invalid start day')
            weekday = weekdays.index(self.start_day)
            days_ahead = weekday - self.next_run.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            self.next_run += datetime.timedelta(days_ahead) - self.period
        if self.at_time is not None:
            if (self.unit not in ('days', 'hours', 'minutes')
                    and self.start_day is None):
                raise ScheduleValueError(('Invalid unit without'
                                          ' specifying start day'))
            kwargs = {
                'second': self.at_time.second,
                'microsecond': 0
            }
            if self.unit == 'days' or self.start_day is not None:
                kwargs['hour'] = self.at_time.hour
            if self.unit in ['days', 'hours'] or self.start_day is not None:
                kwargs['minute'] = self.at_time.minute
            self.next_run = self.next_run.replace(**kwargs)
            # If we are running for the first time, make sure we run
            # at the specified time *today* (or *this hour*) as well
            if not self.last_run:
                now = datetime.datetime.now()
                if (self.unit == 'days' and self.at_time > now.time() and
                        self.interval == 1):
                    self.next_run = self.next_run - datetime.timedelta(days=1)
                elif self.unit == 'hours' \
                        and self.at_time.minute > now.minute \
                        or (self.at_time.minute == now.minute
                            and self.at_time.second > now.second):
                    self.next_run = self.next_run - datetime.timedelta(hours=1)
                elif self.unit == 'minutes' \
                        and self.at_time.second > now.second:
                    self.next_run = self.next_run - \
                                    datetime.timedelta(minutes=1)
        if self.start_day is not None and self.at_time is not None:
            # Let's see if we will still make that time we specified today
            if (self.next_run - datetime.datetime.now()).days >= 7:
                self.next_run -= self.period
