from VSCServerMessages import *



# Class which have the same functionality as exceptions,
# Do not use as normal return to server

class ErrorHandler:
    def __init__(self):
        self.err_dict = {
            ERR_INVALID_CMD : "Invalid command.",
            ERR_SERVER : "Server side error, try restarting.",
            ERR_PORT_OCCUPIED : "The port is already in use, try restarting your computer.",
            ERR_NOT_AN_ACTION : "There is no action with the given name.",
            ERR_NOT_A_SETTING : "Settings are not available for action.",
            ERR_E4_DATA_RAISE : "Problem with getting data from the E4 device."
        }

    def __getitem__(self, arg):
        if not isinstance(arg, int):
            raise TypeError("Key is supposed to be int.")
        
        if arg not in self.err_dict:
            raise KeyError(f" Error '{arg}' does not exist.")
        
        return f"ERR {arg} {self.err_dict[arg]}"
    