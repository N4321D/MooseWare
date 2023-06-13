'''
This class sends sms alerts to defined phone numbers

'''
# logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("Messenger: ", *x)
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

# Download the helper library from https://www.twilio.com/docs/python/install
try:
    from twilio.rest import Client

except ImportError:
    logger.warning('Warning: Twilio not found, no SMS alerts available')

    def Client(*args, **kwargs):
        return


class Messenger():
    # Your Account Sid and Auth Token from twilio.com/console
    # DANGER! This is insecure. See http://twil.io/secure
    account_sid = 'ACdc5abdae97e0985933852054df5e94ee'
    auth_token = '8adb9ea3df096a63b0f81fb9e6e5d7e7'
    from_no = '+14243784888'                          # number to set text from
    to_no = []                                        # numbers to send text to
    base_text = "└┘┘┘┘=|◶◶|=└└└└┘\n"                 # header of sms
    errors = {}                                              # dict with errors

    def __init__(self):
        self.client = Client(self.account_sid, self.auth_token)

    def send_alert(self, alert):
        if not isinstance(alert, str):
            alert = str(alert)
        
        if not isinstance(self.to_no, list):
            self.to_no = [self.to_no]

        alert = self.base_text + alert

        self.errors = {}
        for no in self.to_no:
            try:
                message = self.client.messages.create(
                                                      body=alert,
                                                      from_=self.from_no,
                                                      to=no
                                                      )
                self.errors.update({no: ('Success', message.sid)})

            except Exception as e:
                self.errors.update({no: (e,)})
                logger.error("MESSENGER: {}".format(e))
