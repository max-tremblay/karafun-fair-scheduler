import functools
import os
import socketio
import threading


from qmgr import QueueManager
mtx = threading.Lock()
sio: socketio.Client

queue_handle_timer = threading.Timer(999.0, lambda: None)

class Scheduler(socketio.ClientNamespace, socketio.Client):
    def __init__(self, args) -> None:
        self.args = args
        self.lastQueue = None
        self.qm = QueueManager(args.hide_singers)
        socketio.ClientNamespace.__init__(self, "/")
        socketio.Client.__init__(self)
        socketio.Client.register_namespace(self, self)
        socketio.Client.connect(self, 'https://www.karafun.com/socket.io/?remote=kf%s' % args.channel)

    # Borrowed from https://stackoverflow.com/questions/60074810/python-3-mutex-equivalent
    def _mutex(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            res = None
            try:
                with mtx:
                    res = func(self, *args, **kwargs)             
            except Exception as e:
                print(e)
                pass

            if res is not None:
                return res

        return wrapper

    def on_connect(self):
        if self.args.verbose:
            print('connection established')
        socketio.Client.emit(self, 'authenticate', {
            'login': 'fair scheduler',
            'channel': self.args.channel,
            'role': 'participant',
            'app': 'karafun',
            'socket_id': None,
        })

    @_mutex
    def on_loginAlreadyTaken(self):
        if self.args.verbose:
            print('loginAlreadyTaken')
        socketio.Client.emit(self, 'authenticate', {
            'login': 'fair scheduler %d' % os.getpid(),
            'channel': self.args.channel,
            'role': 'participant',
            'app': 'karafun',
            'socket_id': None,
        })

    @_mutex
    def on_permissions(self, data):
        if self.args.verbose:
            print('permissions received ', data)

    @_mutex
    def on_preferences(self, data):
        if self.args.verbose:
            print('preferences received ', data)
        if not data['askSingerName']:
            print('You must turn on "Ask singer\'s name when adding to queue" in the Karafun remote control settings in order for the scheduler to work.')
            sio.disconnect()

    @_mutex
    def on_status(self, data):
        if self.args.verbose:
            print('status received ', data)

    queue_handle_timer = threading.Timer(999.0, lambda: None)

    @_mutex
    def handle(self, data):
        action = self.qm.reconcile(data)
        if action:
            print('sending ', action)
            socketio.Client.emit(self, action[0], action[1])

    @_mutex
    def on_queue(self, data):
        if self.args.verbose:
            print('queue received ', data)
        global queue_handle_timer
        queue_handle_timer.cancel()
        queue_handle_timer = threading.Timer(0.3, self.handle, [data])
        queue_handle_timer.start()

    @_mutex
    def on_serverUnreacheable(self):
        print('Server unreachable. Try restarting the Karafun App?')
        socketio.Client.disconnect(self)

    @_mutex
    def on_disconnect(self):
        print('Disconnected from server.')

    def get_current_queue(self):
        return self.qm.getQueue()
    
    def next(self, id):
        queue = self.get_current_queue()
        id -= 1

        if id > 0:
            socketio.Client.emit(self, "queueMove", {'queueId': queue[id], 'from': id, 'to': 1 + len(self.qm.skip)})
            self.qm.skip_this_one(queue[id])
