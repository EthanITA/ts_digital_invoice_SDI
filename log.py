import logging

log_name = "send_invoice.log"
logging.basicConfig(
    handlers=[
        logging.FileHandler(log_name),
        logging.StreamHandler()
    ],
    format='%(asctime)s [%(module)s/%(lineno)d] [%(levelname)-5.5s]:  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)
