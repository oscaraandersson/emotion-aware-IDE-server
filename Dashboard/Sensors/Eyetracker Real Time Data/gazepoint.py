import time
import threading

from tools import OpenGazeTracker

class GazePoint(threading.Thread):
    def __init__(self, ip='127.0.0.1', port=4242):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.gaze_position = (None, None)

        self.open(ip, port)
        self.start()
        self.wait_until_running()

    def get_gaze_position(self):
        return self.gaze_position

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            self.gaze_position = self.tracker.sample()

    def stop(self):
        self.interrupted.release()
        self.close()

    def open(self, ip, port):
        print('Setting Up Gaze Point device, this takes about 58.5 seconds')
        self.tracker = OpenGazeTracker(ip=ip, port=port)
        self.tracker.calibrate()
        self.tracker.enable_send_data(True)

    def close(self):
        print('Closing connection to Gaze Point device, this takes about 5 seconds')
        self.tracker.enable_send_data(False)
        self.tracker.close()

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def wait_until_running(self, sleep_time=0.01):
        while not self.interrupted.locked():
            time.sleep(sleep_time)

    def stuck_check(self, xmin, xmax, ymin, ymax):
        xstuck = False
        ystuck = False

        if abs(xmin - xmax) <= 0.2:
            xstuck = True
        if abs(ymin - ymax) <= (1/3):
            ystuck = True
        if xstuck and ystuck:
            if xmax <= 1/2 and xmax >= 0:
                x_axis = 'left'
            elif xmax <= 1:
                x_axis = 'right'
            
            if ymax <= 1/4 and ymax >= 0:
                y_axis = 'top'
            elif ymax <=1/2:
                y_axis = 'middletop'
            elif ymax <=3/4:
                y_axis = 'middlebottom'
            elif ymax <= 1:
                y_axis = 'bottom'

            if (-0.1 > xmax or xmax > 1.1) or (-0.1 > ymax or ymax > 1.1):
                return 'You are currently looking away from the screen. This will result in a pay cut.'

            return ('ATTENTION! Your eyes seems to have gotten stuck '+str(y_axis + x_axis))

class Livestream():
    def __init__(self):
        self.stream = False

    def run(self, command):
        '''Starts or stops the streaming'''
        if command or not command:
            self.stream = command
        else:
            raise ValueError('Only Boolean values are allowed')

        if command:
            self.stream()

    def stream(self):
        '''Function for livestreaming the eyetracker'''
        gazetracker = GazePoint()  
        print("Done setting up connection to eyetracker")
        xcoords = []
        ycoords = []
        last_sec = []
        gazetracker.tracker.enable_send_time(state=True)
        while self.stream:
            time.sleep(1/60)
            coordinate = gazetracker.get_gaze_position()
            if coordinate[0] is not None and coordinate[1] is not None:
                last_sec.append(coordinate)
            if len(last_sec) >= 60:
                x_sum = 0
                y_sum = 0
                for coord in last_sec:
                    x_sum += coord[0]
                    y_sum += coord[1]
                coordinate = (x_sum/len(last_sec),y_sum/len(last_sec))
                last_sec = []
                print(coordinate)
                if coordinate[0] is not None: 
                    if len(xcoords) > 12:
                        xcoords.pop(0)
                    xcoords.append(coordinate[0])
                if coordinate[1] is not None:
                    if len(ycoords) > 12:
                        ycoords.pop(0)
                    ycoords.append(coordinate[1])
                if len(xcoords) > 8:
                    stuck = gazetracker.stuck_check(min(xcoords),max(xcoords),min(ycoords),max(ycoords))
                    if stuck is not None:
                        print(stuck)
        gazetracker.stop()


if __name__ == '__main__':
    stream = Livestream()  
