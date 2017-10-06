from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from threading import Thread
import queue



class TestWrapper(EWrapper):
    """
    Wrapper function is used to interpret data coming from the server.
    appropriate functions are called automatically if a specific event occurs.
    To do anything with the data these functions need to be overridden
    See the Documentation for possible functions
    """

    def init_error(self):
        """
        init error queue
        """
        error_queue = queue.Queue()
        self._my_errors = error_queue


    def get_error(self, timeout=5):
        """
        obtain the last error
        """
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None
        return None

    def is_error(self):
        """
        Has there been an error?
        """
        return not self._my_errors.empty()

    def error(self, id, errorCode, errorString):
        """ 
        Overriden method from the original API. This method
        gets called when the server message was interpreted 
        as an error and is handled here.
        """
        if (errorCode==2106):
            # just notification messages
            return

        if (errorCode==2104):
            # bug in IB API doesn't affect anything
            return

        errormsg = "IB error id %d errorcode %d string %s" %(id,errorCode,errorString)
        self._my_errors.put(errormsg)


    def init_time(self):
        """
        Initialize a queue for the time (shared with the app)
        """
        time_queue=queue.Queue()
        self._time_queue = time_queue
        return time_queue


    def currentTime(self, time_from_server):
        """
        Overridden method that handles the time.
        It gets automatically called when the server
        packet was interpreted as time information
        """
        self._time_queue.put(time_from_server)





class TestClient(EClient):
    """
    This client function serves as the outgoing connection.
    All messages that are send from this side need to call EClient functions.
    See the documentation for all possible funcitons. The additional functions
    here are only written for convinience later on.
    """
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def speaking_clock(self):
        """
        Sends a request for time to the server. Then prints out the time.the
        """


        print("Getting the time from the server... ")

        # creates a shared queue object in which the time will be deposited
        time_storage=self.wrapper.init_time()

        ## This is the native method in EClient, asks the server to send us the time please
        self.reqCurrentTime()

        ## Try and get a valid time
        MAX_WAIT_SECONDS = 10

        try:
            #wait MAX_WAIT_SECONDS for the queue to get filled 
            current_time = time_storage.get(timeout=MAX_WAIT_SECONDS)

        except queue.Empty:
            print("Exceeded maximum wait for wrapper to respond")
            current_time = None


        while self.wrapper.is_error():
            print(self.get_error())

        return current_time


class TestApp(TestWrapper, TestClient):
    """
    This is the actual interface that we will use.
    It inherits from both the client and the wrapper.
    Thus we have a simple unified interface.
    """

    def __init__(self, ipaddress, portid, clientid):
        """
        Here the connection gets established.
        Another thread is startde
        """
        # initialization
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        # connect to the server
        try:
            self.connect(ipaddress, portid, clientid)
        except:
            print("No connection to server could be established")
            exit(1)

        # start the Eclient.run method in a separate thread
        # that listens for messages and calls appropiate wrapper functions
        thread = Thread(target = self.run)
        thread.start()

        setattr(self, "_thread", thread)
        self.init_error()



if __name__ == '__main__':

    # initialize app interface, everything else is not needed
    app = TestApp("127.0.0.1", 7496, 10)

    # very complicated way to get time
    print(app.speaking_clock())

    # and finnish
    app.disconnect()