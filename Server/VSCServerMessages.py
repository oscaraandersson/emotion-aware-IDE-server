#                     #
#   Client commands   #
#                     #
HANDLE_FORM = "FRM"

CONNECT_E4 = "CE4"
DISCONNECT_E4 = "DE4"
SCAN_E4 = "SCE4"

START_EYE = "ONEY"
STOP_EYE = "OFEY"
RECALIBRATE_EYE = "RCEY"

END_SERVER = "END" 
START_BASELINE = "SBL" 
ACTIVATE_ACTION = "AACT"
DEACTIVATE_ACTION = "DACT"
EDIT_ACTION = "EACT"


#                     #
#   Server commands   #
#                     #
SUCCESS_STR = "SUCC"
FAIL_STR = "FAIL"

INIT_FORM = "IFRM"
E4_LOST_CONNECTION = "LCE4"
ACTION_STR = "ACT"


#                     #
#   Errors messages   #
#                     #
ERR_SERVER = 400
ERR_INVALID_CMD = 401
ERR_PORT_OCCUPIED = 402
ERR_NOT_AN_ACTION = 420
ERR_NOT_A_SETTING = 425
ERR_E4_DATA_RAISE = 430