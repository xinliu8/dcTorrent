import logging.handlers

def setRootLogger(filename, level):
    rootLogger = logging.root
    rootLogger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
    for handler in logging.root.handlers:
        rootLogger.removeHandler(handler)
    trfHandler = logging.handlers.TimedRotatingFileHandler(filename)
    trfHandler.setFormatter(formatter)
    rootLogger.addHandler(trfHandler)
