
import logging
_logger = logging.getLogger('INSPY_booking')
_logger.setLevel(logging.DEBUG)
_logger_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
_logger_file_handler = logging.FileHandler('/tmp/booking-error.log')
_logger_file_handler.setFormatter(_logger_formatter)
_logger.addHandler(_logger_file_handler)

# import res_config
import booking