from utils import log_print


class Sorry(Exception):
    def __init__(self):
        super().__init__("Soorryyy. Not implemented yet.")
        log_print("Soorryyy. Not implemented yet.")
