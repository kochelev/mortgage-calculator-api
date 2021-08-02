
# TODO: create a ancestor class for exceptions and inherit it's methods


class PlanError(BaseException):
    messages = {
        'S_i < IP_min + R': lambda payload: 'Too big IP: need %d but have %d' % (payload['need'], payload['have']),
    }

    def __init__(self, code, payload):
        self.code = code
        self.payload = payload
        self.message = self.messages[self.code](self.payload)

    def __str__(self):
        return self.message


class BudgetError(BaseException):
    messages = {
        'MRG_MP': lambda payload: 'Mortgage MP: not enough money for minimal payment: need %d but have %d' \
                              % (payload['need'], payload['have']),
        'CRD_MP': lambda payload: 'Credit MP: not enough money for minimal payment: need %d but have %d' \
                                  % (payload['need'], payload['have']),
        'MRG_MP + CRD_MP': lambda payload: 'Mortgage and Credit MP: not enough money for minimal payments: need %d but have %d' \
                              % (payload['need'], payload['have']),
        'EXP': lambda payload: 'Not enough money for EXTRA expencies: need %f, but have %f' \
                               % (payload['need'], payload['have'])
    }

    def __init__(self, code, payload):
        self.code = code
        self.payload = payload
        self.message = self.messages[self.code](self.payload)

    def __str__(self):
        return self.message


class CreditError(BaseException):
    messages = {
        'MP': lambda payload: 'MP: need %d but have %d' % (payload['need'], payload['have']),
        'MP1': lambda payload: 'MP1: need %d but have %d' % (payload['need'], payload['have']),
        'MP2': lambda payload: 'MP2: need %d but have %d' % (payload['need'], payload['have']),
        'IP': lambda payload: 'IP: need %d but have %d' % (payload['need'], payload['have']),
    }

    def __init__(self, code, payload):
        self.code = code
        self.payload = payload
        self.message = self.messages[self.code](self.payload)

    def __str__(self):
        return self.message


class SavingsError(BaseException):

    messages = {
        'S': lambda payload: 'S: need %d but have %d' % (payload['need'], payload['have']),
        'PARAMS': lambda payload: payload,
        'NOMORTGAGE': lambda payload: 'Realty can be bought and repairing can be payed without credits, need %d, but can save more: %d' % (payload['need'], payload['have'])
    }

    def __init__(self, code, payload):

        self.code = code
        self.payload = payload
        self.message = self.messages[self.code](self.payload)

    def __str__(self):
        return self.message


class ComputationError(BaseException):

    messages = {
        1: lambda payload: 'S_0_min is %d and S_0_max is %d' % (payload[0], payload[1]),
        2: lambda payload: 'Problem infeasible, can\'t save %d' % (payload[0])
    }

    def __init__(self, code, *payload):

        self.code = code
        self.payload = payload
        self.message = self.messages[self.code](self.payload)

    def __str__(self):
        return self.message
