import logging

logging.basicConfig(
    filename='test/logs/llm_logs.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def LOGD(log):
    logging.debug(log)
