from threading import Thread

from flask import current_app


class FlaskThread(Thread):
    """
        This class override the base class of Thread just to make flask.current_app accessible in a Thread
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = current_app._get_current_object()

    def run(self):
        with self.app.app_context():
            with self.app.test_request_context():
                super().run()
