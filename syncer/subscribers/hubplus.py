import bases, utils, errors

class HubPlus(bases.WebApp):

    def makeLoginDict(self, username, password):
       return dict (
            username = username,
            password = password )

