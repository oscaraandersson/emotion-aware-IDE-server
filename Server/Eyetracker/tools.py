import copy
import time
import socket
import lxml.etree

from multiprocessing import Queue
from threading import Event, Lock, Thread

# The OpenGazeTracker class communicates to the GazePoint Server through a TCP/IP socket.
class OpenGazeTracker:
    def __init__(self, ip='127.0.0.1', port=4242):

        """The OpenGazeTracker class communicates to the GazePoint
        server through a TCP/IP socket. Incoming samples will be written
        to a log at the specified path.
        Keyword Arguments
        ip	-	The IP address of the computer that is running the
                OpenGaze server. This will usually be the localhost at
                127.0.0.1. Type: str. Default = '127.0.0.1'
        port	-	The port number that the OpenGaze server is on; usually
                this will be 4242. Type: int. Default = 4242
        """

        # CONNECTION
        # Save the ip and port numbers.
        self.host = ip
        self.port = port
        # Start a new TCP/IP socket. It is curcial that it has a timeout,
        # as timeout exceptions will be handled gracefully, and are in fact
        # necessary to prevent the incoming Thread from freezing.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self.host, self.port))
        self._sock.settimeout(1.0)
        self._maxrecvsize = 4096
        # Create a socket Lock to prevent simultaneous access.
        self._socklock = Lock()
        # Create an event that should remain set until the connection is
        # closed. (This is what keeps the Threads running.)
        self._connected = Event()
        self._connected.set()
        # Set the current calibration point.
        self._current_calibration_point = None

        # INCOMING
        # Start a new dict for the latest incoming messages, and for
        # incoming acknowledgements.
        self._incoming = {}
        self._acknowledgements = {}
        # Create a Lock for the incoming message and acknowledgement dicts.
        self._inlock = Lock()
        self._acklock = Lock()
        # Create an empty string for the current unfinished message. This
        # is to prevent half a message being parsed when it is cut off
        # between two 'self._sock.recv' calls.
        self._unfinished = ''
        # Start a new Thread that processes the incoming messages.
        self._inthread = Thread(
            target=self._process_incoming,
            name='PyGaze_OpenGazeConnection_incoming',
            args=[])

        # OUTGOING
        # Start a new outgoing Queue (Thread safe, woop!).
        self._outqueue = Queue()
        # Set an event that is set when all queued outgoing messages have
        # been processed.
        self._sock_ready_for_closing = Event()
        self._sock_ready_for_closing.clear()
        # Create a new Thread that processes the outgoing queue.
        self._outthread = Thread(
            target=self._process_outgoing,
            name='PyGaze_OpenGazeConnection_outgoing',
            args=[])
        # Create a dict that will keep track of at what time which command
        # was sent.
        self._outlatest = {}
        # Create a Lock to prevent simultaneous access to the outlatest
        # dict.
        self._outlock = Lock()

        # RUN THREADS
        # Set a signal that will kill all Threads when they receive it.
        self._thread_shutdown_signal = 'KILL_ALL_HUMANS'
        # Start the threads.
        self._inthread.start()
        self._outthread.start()

        # SET UP LOGGING
        # Wait for a bit to allow the Threads to start.
        time.sleep(0.5)
        # Enable the tracker to send ALL the things.
        self.enable_send_time(True)
        self.enable_send_time_tick(True)
        time.sleep(1.0)

    def calibrate(self):

        """Calibrates the eye tracker.
        """

        # Reset the calibration.
        self.clear_calibration_result()
        # Show the calibration screen.
        self.calibrate_show(True)
        # Start the calibration.
        self.calibrate_start(True)
        # Wait for the calibration result.
        result = None
        while result is None:
            result = self.get_calibration_result()
            time.sleep(0.1)
        # Hide the calibration window.
        self.calibrate_show(False)

        return result

    def close(self):
        """Closes the connection to the tracker, closes the log files, and
        ends the Threads that process the incoming and outgoing messages,
        and the logging of samples.
        """

        # Reset the user-defined value.
        self.user_data('0')

        # Unset the self._connected event to stop the incoming Thread.
        self._connected.clear()

        # Queue the stop signal to stop the outgoing and logging Threads.
        self._outqueue.put(self._thread_shutdown_signal)

        # Wait for the outgoing Queue to be fully processed.
        self._sock_ready_for_closing.wait()

        # Close the socket connection to the OpenGaze server.
        self._sock.close()

        # Join the Threads.
        self._outthread.join()
        self._inthread.join()


    def enable_send_time(self, state):

        """Enable (state=True) or disable (state=False) the inclusion of
        the send time in the data record string.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'ENABLE_SEND_TIME', values=[('STATE', int(state))], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def enable_send_time_tick(self, state):

        """Enable (state=True) or disable (state=False) the inclusion of
        the send time tick in the data record string.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'ENABLE_SEND_TIME_TICK', values=[('STATE', int(state))], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def calibrate_start(self, state):

        """Starts (state=1) or stops (state=0) the calibration procedure.
        Make sure to call the 'calibrate_show' function beforehand, or to
        implement your own calibration visualisation; otherwise a call to
        this function will make the calibration run in the background.
        """

        # Reset the current calibration point.
        if state:
            self._current_calibration_point = 0
        else:
            self._current_calibration_point = None

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'CALIBRATE_START', values=[('STATE', int(state))], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def calibrate_show(self, state):

        """Shows (state=1) or hides (state=0) the calibration window on the
        tracker's display window. While showing the calibration window, you
        can call 'calibrate_start' to run the calibration procedure.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'CALIBRATE_SHOW', values=[('STATE', int(state))], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def calibrate_timeout(self, value):

        """Set the duration of the calibration point (not including the
        animation time) in seconds. The value can be an int or a float.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'CALIBRATE_TIMEOUT', values=[('VALUE', float(value))], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def calibrate_delay(self, value):

        """Set the duration of the calibration animation (before
        calibration at a point begins) in seconds. The value can be an int
        or a float.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'CALIBRATE_DELAY', values=[('VALUE', float(value))], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def calibrate_result_summary(self):

        """Returns a summary of the calibration results, which consists of
        the following values:
        AVE_ERROR:    Average error over all calibrated points.
        VALID_POINTS: Number of successfully calibrated points.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('GET', 'CALIBRATE_RESULT_SUMMARY', values=None, wait_for_acknowledgement=True)

        # Return the results.
        ave_error = None
        valid_points = None
        if acknowledged:
            self._inlock.acquire()
            ave_error = copy.copy(
                self._incoming['ACK']['CALIBRATE_RESULT_SUMMARY']['AVE_ERROR'])
            valid_points = copy.copy(
                self._incoming['ACK']['CALIBRATE_RESULT_SUMMARY']['VALID_POINTS'])
            self._inlock.release()

        return ave_error, valid_points

    def calibrate_clear(self):

        """Clear the internal list of calibration points.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'CALIBRATE_CLEAR', values=None, wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def calibrate_reset(self):

        """Reset the internal list of calibration points to the default
        values.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'CALIBRATE_RESET', values=None, wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def calibrate_addpoint(self, x, y):

        """Add a calibration point at the passed horizontal (x) and
        vertical (y) coordinates. These coordinates should be as a
        proportion of the screen resolution, where (0,0) is the top-left,
        (0.5,0.5) is the screen centre, and (1,1) is the bottom-right.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'CALIBRATE_ADDPOINT', values=[('X', x), ('Y', y)], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def get_calibration_points(self):

        """Returns a list of the current calibration points.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('GET', 'CALIBRATE_ADDPOINT', values=None, wait_for_acknowledgement=True)

        # Return the result.
        points = None
        if acknowledged:
            points = []
            self._inlock.acquire()
            for i in range(self._incoming['ACK']['CALIBRATE_ADDPOINT']['PTS']):
                points.append(
                    copy.copy(float(
                        self._incoming['ACK']['CALIBRATE_ADDPOINT']['X%d' % i + 1])),
                    copy.copy(float(
                        self._incoming['ACK']['CALIBRATE_ADDPOINT']['Y%d' % i + 1]))
                )
            self._inlock.release()

        return points

    def clear_calibration_result(self):

        """Clears the internally stored calibration result.
        """

        # Clear the calibration results.
        self._inlock.acquire()
        if 'CAL' in self._incoming.keys():
            if 'CALIB_RESULT' in self._incoming['CAL'].keys():
                self._incoming['CAL'].pop('CALIB_RESULT')
        self._inlock.release()

    def get_calibration_result(self):

        """Returns the latest available calibration results as a list of
        dicts, each with the following keys:
        CALX: Calibration point's horizontal coordinate.
        CALY: Calibration point's vertical coordinate
        LX:   Left eye's recorded horizontal point of gaze.
        LY:   Left eye's recorded vertical point of gaze.
        LV:   Left eye's validity status (1=valid, 0=invalid)
        RX:   Right eye's recorded horizontal point of gaze.
        RY:   Right eye's recorded vertical point of gaze.
        RV:   Right eye's validity status (1=valid, 0=invalid)
        Returns None if no calibration results are available.
        """

        # Parameters of the 'CALIB_RESULT' dict.
        params = ['CALX', 'CALY', 'LX', 'LY', 'LV', 'RX', 'RY', 'RV']

        # Return the result.
        points = None
        self._inlock.acquire()
        if 'CAL' in self._incoming.keys():
            if 'CALIB_RESULT' in self._incoming['CAL'].keys():
                # Get the latest calibration results.
                cal = copy.deepcopy(self._incoming['CAL']['CALIB_RESULT'])
                # Compute the number of fixation points by dividing the
                # total number of parameters in the 'CALIB_RESULT' dict
                # by 8 (the number of parameters per point). Note that
                # the 'CALIB_RESULT' dict also has an 'ID' parameter,
                # which we should account for by subtracting 1 from the
                # length of the list of keys in the dict.
                n_points = (len(cal.keys()) - 1) // len(params)
                # Put the results in a different format.
                points = []
                for i in range(1, n_points + 1):
                    p = {}
                    for par in params:
                        if par in ['LV', 'RV']:
                            p['%s' % (par)] = cal['%s%d' % (par, i)] == '1'
                        else:
                            p['%s' % (par)] = float(cal['%s%d' % (par, i)])
                    points.append(copy.deepcopy(p))
        self._inlock.release()

        return points

    def wait_for_calibration_point_start(self, timeout=10.0):

        """Waits for the next calibration point start, which is defined as
        the first unregistered point after the latest calibration start
        message. This function allows for setting a timeout in seconds
        (default = 10.0). Returns the (x,y) coordinate in relative
        coordinates (proportions of the screen width and height) if the
        point started, and None after a timeout. (Also updates the
        internally stored latest registered calibration point number.)
        """

        # Get the start time of this function.
        start = time.time()

        # Get the most recent calibration start time.
        t0 = None
        while (t0 is None) and (time.time() - start < timeout):
            self._inlock.acquire()
            if 'ACK' in self._incoming.keys():
                if 'CALIBRATE_START' in self._incoming['ACK'].keys():
                    t0 = copy.copy(
                        self._incoming['ACK']['CALIBRATE_START']['t'])
            self._inlock.release()
            if t0 is None:
                time.sleep(0.001)

        # Return None if there was no calibration start.
        if t0 is None:
            return None

        # Wait for a new calibration point start, or a timeout.
        pos = None
        pt_nr = None
        started = False
        timed_out = False
        while (not started) and (not timed_out):
            # Get the latest calibration point start.
            t1 = 0
            self._inlock.acquire()
            if 'CAL' in self._incoming.keys():
                if 'CALIB_START_PT' in self._incoming['CAL'].keys():
                    t1 = copy.copy(
                        self._incoming['CAL']['CALIB_START_PT']['t'])
            self._inlock.release()
            # Check if the point is later than the most recent
            # calibration start.
            if t1 >= t0:
                # Check if the current point is already the latest
                # registered point.
                self._inlock.acquire()
                pt_nr = int(copy.copy(self._incoming['CAL']['CALIB_START_PT']['PT']))
                x = float(copy.copy(self._incoming['CAL']['CALIB_START_PT']['CALX']))
                y = float(copy.copy(self._incoming['CAL']['CALIB_START_PT']['CALY']))
                self._inlock.release()
                if pt_nr != self._current_calibration_point:
                    self._current_calibration_point = copy.copy(pt_nr)
                    pos = (x, y)
                    started = True
            # Check if there is a timeout.
            if time.time() - start > timeout:
                timed_out = True
            # Wait for a short bit to avoid wasting too many resources,
            # and to avoid hogging the incoming messages Lock.
            if not timed_out:
                time.sleep(0.001)

        if started:
            return pt_nr, pos
        else:
            return None, None

    def tracker_display(self, state):

        """Shows (state=1) or hides (state=0) the eye tracker display
        window.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'TRACKER_DISPLAY', values=[('STATE', int(state))], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def time_tick_frequency(self):

        """Returns the time-tick frequency to convert the TIME_TICK
        variable to seconds.
        """

        return self.get_time_tick_frequency()

    def get_time_tick_frequency(self):

        """Returns the time-tick frequency to convert the TIME_TICK
        variable to seconds.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('GET', 'TIME_TICK_FREQUENCY', values=None, wait_for_acknowledgement=True)

        # Return the result.
        freq = None
        if acknowledged:
            self._inlock.acquire()
            freq = copy.copy(self._incoming['ACK']['TIME_TICK_FREQUENCY']['FREQ'])
            self._inlock.release()

        return freq

    def screen_size(self, x, y, w, h):

        """Set the gaze tracking screen position (x,y) and size (w, h). You
        can use this to work with multi-monitor systems. All values are in
        pixels.
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('SET', 'SCREEN_SIZE', values=[('X', x), ('Y', y), ('WIDTH', w), ('HEIGHT', h)], wait_for_acknowledgement=True)

        # Return a success Boolean.
        return acknowledged and (timeout is False)

    def get_screen_size(self):

        """Returns the x and y coordinates of the top-left of the screen in
        pixels, as well as the screen width and height in pixels. The
        result is returned as [x, y, w, h].
        """

        # Send the message (returns after the Server acknowledges receipt).
        acknowledged, timeout = self._send_message('GET', 'SCREEN_SIZE', values=None, wait_for_acknowledgement=True)

        # Return the result.
        x = None
        y = None
        w = None
        h = None
        if acknowledged:
            self._inlock.acquire()
            x = copy.copy(self._incoming['ACK']['SCREEN_SIZE']['X'])
            y = copy.copy(self._incoming['ACK']['SCREEN_SIZE']['Y'])
            w = copy.copy(self._incoming['ACK']['SCREEN_SIZE']['WIDTH'])
            h = copy.copy(self._incoming['ACK']['SCREEN_SIZE']['HEIGHT'])
            self._inlock.release()

        return [x, y, w, h]