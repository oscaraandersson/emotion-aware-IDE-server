

ERR_SERVER = 400
ERR_INVALID_CMD = 401
ERR_PORT_OCCUPIED = 402
ERR_NOT_AN_ACTION = 420
ERR_NOT_A_SETTING = 425



# Class which have the same functionality as exceptions,
# Do not use as normal return to server

class ErrorHandler:
    def __init__(self):
        self.err_dict = {
            ERR_INVALID_CMD : "Invalid command.",
            ERR_SERVER : "Server side error, try restarting.",
            ERR_PORT_OCCUPIED : "The port is already in use, try restarting your computer.",
            ERR_NOT_AN_ACTION : "There is no action with the given name.",
            ERR_NOT_A_SETTING : "Settings are not available for action."
        }
        self.ERR_INVALID_CMD = ERR_INVALID_CMD
        self.ERR_SERVER = ERR_SERVER
        self.ERR_PORT_OCCUPIED = ERR_PORT_OCCUPIED
        self.ERR_NOT_AN_ACTION = ERR_NOT_AN_ACTION
        self.ERR_NOT_A_SETTING = ERR_NOT_A_SETTING

    def __getitem__(self, arg):
        if not isinstance(arg, int):
            raise TypeError("Key is supposed to be int.")
        
        if arg not in self.err_dict:
            raise KeyError(f" Error '{arg}' does not exist.")
        
        return f"ERR {arg} {self.err_dict[arg]}"
    