import logging
import logging.handlers
import inspect
import os


def get_caller():
    """
    Get the name of the function who called Logger to improve log content
    :return: the filename of the Python file that called the log
    """
    # First get the full filename (including path and file extension)
    try:
        caller_frame = inspect.stack()[2]
        caller_filename = caller_frame.filename
        # Now get rid of the directory and extension
        filename = os.path.splitext(os.path.basename(caller_filename))[0]
        parent_directory = os.path.basename(os.path.dirname(caller_filename))
        return "{0}-{1}".format(parent_directory, filename)
    except Exception:
        return ""


class Logger:
    def __init__(self):
        self.logger = logging.getLogger()

    def info(self, message):
        self.logger.info("[{0}] {1}".format(get_caller(), message))

    def debug(self, message):
        self.logger.debug("[{0}] {1}".format(get_caller(), message))

    def warning(self, message):
        self.logger.warning("[{0}] {1}".format(get_caller(), message))

    def error(self, message):
        self.logger.error("[{0}] {1}".format(get_caller(), message))

    def critical(self, message):
        self.logger.critical("[{0}] {1}".format(get_caller(), message))
