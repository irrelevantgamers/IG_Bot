from fileinput import filename
import lovely_logger as log # pip install lovely-logger
from datetime import datetime
logfile = f"loggingtest-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log"
log.init(f'..\\logs\\{logfile}')
log.info('Hello World!')