from pprint import pformat
import time
import threading
import json
import webbrowser

from Eyetracker.tools import OpenGazeTracker

class GazePoint(threading.Thread):
    def __init__(self, ip='127.0.0.1', port=4242):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()
        self.keywords = json.load(open("keywords.json"))

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

    def am_stuck(self,text:str,x:str,y:str):
        """
        args:\n
        text: Visible text\n
        y = top/middle/bottom\n
        x = left/right
        """
        code_words = text.split(' ')
        code_words = list(filter(lambda val: val !=  " ", code_words))
        code_words = list(filter(lambda val: val !=  "", code_words))
        found = False

        if y == "top":
            start = 0
            end = len(code_words)
            direction = 1
        elif y == "middle":
            start = len(code_words)//2
            end = len(code_words)
            direction = 1
        elif y == "bottom":
            start = len(code_words)-1
            end = 0
            direction = -1
        
        for index in range(start,end,direction):
            if code_words[index] in self.keywords and not found:
                link = "https://www.w3schools.com/python/" + self.keywords[code_words[index]] + ".asp"
                webbrowser.open(link, new=2)
                found = True
        
        if not found:
            webbrowser.open(r"https://upload.wikimedia.org/wikipedia/commons/1/14/Rubber_Duck_%288374802487%29.jpg", new=2)

    def get_text():
        """should retrieve the text from the server"""
        pass

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
            
            if ymax <= 1/3 and ymax >= 0:
                y_axis = 'top'
            elif ymax <=2/3:
                y_axis = 'middle'
            elif ymax <= 1:
                y_axis = 'bottom'

            if (-0.1 > xmax or xmax > 1.1) or (-0.1 > ymax or ymax > 1.1):
                return (-1,-1)

            return (y_axis, x_axis)

class Livestream():
    def __init__(self):
        self.stream = False
        self.gazetracker = None  
    def run(self, command):
        '''Starts or stops the streaming'''
        print("Started")
        if not isinstance(command, bool):
            raise ValueError('Only Boolean values are allowed')
        if command:
            self.gazetracker = GazePoint()
            self.stream = True
        else:
            if self.stream and self.gazetrack is not None:
                self.gazetracker.stop()
                self.stream = False

    def stream(self):
        '''Function for livestreaming the eyetracker'''
        print("Done setting up connection to eyetracker")
        xcoords = []
        ycoords = []
        last_sec = []
        coordinate = self.gazetracker.get_gaze_position()
        print(self.gazetracker.get_gaze_position())
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
            if coordinate[0] is not None: 
                if len(xcoords) > 12:
                    xcoords.pop(0)
                xcoords.append(coordinate[0])
            if coordinate[1] is not None:
                if len(ycoords) > 12:
                    ycoords.pop(0)
                ycoords.append(coordinate[1])
            if len(xcoords) > 8:
                y_stuck,x_stuck = self.gazetracker.stuck_check(min(xcoords),max(xcoords),min(ycoords),max(ycoords))
                if y_stuck is not None:
                    self.gazetracker.am_stuck(self.gazetracker.get_text(),x_stuck,y_stuck)
                    xcoords,ycoords = []

if __name__ == '__main__':
    stream = Livestream()  