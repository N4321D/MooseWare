"""
The network function here can be added to a widget to send interaction
over the network to the client

specific function can be called or settings set; Examples:
 x.send_interaction(widget, x.cr_cmd('dispatch', ar = ('on_text',))
 -> remotely triggers on_text func of widget

 x.send_interaction(widget, x.cr_cmd('text', widget.text)
 -> sends text

 x.send_interaction(widget,
                     x.cr_cmd('trigger_action',
                              kwa={'duration': touch_duration}))
 -> sends last click (can be retrieved using widget.last_touch, see
    Server_Button.py)



send_interaction:
    call this method from the widget upon click, textinput, etc,
    label is the label or command which is send to the client to identify
    the type of widget interaction



get_id:
    gets the id name of the widget as registered in
    app.root.get_screen(screen).ids and sets the idName and screen
    NOTE: the widget must have the vars:
    idName = None
    scr = None
    on initiation

send_2_server:
    sends the button press to the server

cr_cmd:
    creates a command to send to the server (a dict with the par/func name
    and args and kwargs or a value)
    use:
        cr_cmd(parname, value, as = args, kwas = kwargs)
            parname should be str
            args should be list
            kwargs should be dict


"""
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("NETWORK FUNCTIONS (BUTTONS): ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("NETWORK FUNCTIONS (BUTTONS): {}".format(message))  # change RECORDER SAVER IN CLASS NAME


def send_interaction(cls, action):
    try:
        get_id(cls)
        if cls.scr.app.SERVER:
            send(cls, cls.scr, cls.idName, action)

    except AttributeError as e:
        log("Cannot send command to client: \n"
            "     Button: {} on {} \n"
            "{}".format(cls, cls.scr, e), "warning")


def get_id(cls):
    """this method sets the class id name
    and parent name.
    It starts from the widget and walks up until a dict with ids is found
    which is the screen, This is set as widget.scr in the widget class
    then in the ids dict, it looks for the widget and sets the key as
    widget.idName
    """
    idName = None
    if cls.idName is None or cls.scr is None:
        scr = cls
        while not scr.ids:
            scr = scr.parent
        for i in scr.ids.items():
            if cls == i[1]:
                idName = i[0]
                break
        cls.idName = idName
        cls.scr = scr


def send(cls, scr, idName, action):
    if idName is not None:
        scr.app.IO.send(('VAR', 
                          (scr.name, 'ids.{}.{}'.format(idName, 
                           action[0]), *action[1:])))               # action [1] = args, action[2] = kwargs

def cr_cmd(varname, *value, a=(), kwa={}):
    """
    this method takes a command name and a
    dict of kwargs and/or list of args and returns a dict to send to client
    if values are passed it is returned as a dict which would set a par to
    the specific value in the client
    """
    if not a and not kwa and value:
        out = (varname, (value[0], ), {})
    else:
        out = (varname, a, kwa)
    return out
