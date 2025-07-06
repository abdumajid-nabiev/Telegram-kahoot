import time

def start_timer():
    return time.time()

def stop_timer(start):
    return time.time() - start

def format_time(seconds):
    return f"{int(seconds)}s"
