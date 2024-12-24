
class Account(object):

    def __init__(self, name, email, password, invited_by, proxy):
        self.name = name
        self.email = email
        self.password = password
        self.invited_by = invited_by
        self.proxy = proxy
        self.address = None
        self.private_key = None
        self.registered = False
        self.wallet_linked = False


