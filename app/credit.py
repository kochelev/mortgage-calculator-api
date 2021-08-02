import math
from errors import CreditError

# TODO: get_debt_after_period remake test for negativation of debt
# TODO: remake "Not enough money" error handler in pay method

precision = 0


class Credit:

    # d, k, n
    @staticmethod
    def get_minimal_payment(current_debt, interest_rate, months_left):
        
        return interest_rate * current_debt / (1 - (1 / ((1 + interest_rate) ** months_left)))

    # d, k, p, m, n
    @staticmethod
    def get_minimal_payment_after_period(current_debt, interest_rate, months_left, month_payment, months_passed):

        MP = Credit.get_minimal_payment(
            current_debt=current_debt,
            interest_rate=interest_rate,
            months_left=months_left
        )

        if round(month_payment, 5) + 0.00001 < round(MP):
            raise CreditError('MP', {'need': MP, 'have': month_payment})

        return ((1 + interest_rate) ** months_passed * (interest_rate * current_debt - month_payment) + month_payment) \
               / (1 - (1 / ((1 + interest_rate) ** months_left)))

    # d, k, p, m, n
    @staticmethod
    def get_debt_after_period(current_debt, interest_rate, months_left, month_payment, months_passed):

        MP = Credit.get_minimal_payment(
            current_debt=current_debt,
            interest_rate=interest_rate,
            months_left=months_left
        )

        if round(month_payment, 2) + 0.01 < MP:
            raise CreditError('MP', {'need': MP, 'have': month_payment})

        if months_passed == 0:
            return current_debt
        
        return current_debt * (1 + interest_rate) ** months_passed \
               - month_payment * ((1 + interest_rate) ** months_passed - 1) / interest_rate

    # d, k, p
    @staticmethod
    def get_period(current_debt, interest_rate, month_payment):

        return math.log((month_payment / (month_payment - interest_rate * current_debt)), (1 + interest_rate))

    def __init__(self, name, debt, schedule):
        
        self.name = name
        self.debt = debt
        self.overpay = None
        self.schedule = schedule
        self.rate_change = False
        self.history = []

        if debt > 0:
            self.is_active = True
            self.schedule = schedule
            self.interest_rate = self.schedule[0]['interest_rate']
            self.months_left = sum([x['months'] for x in self.schedule])
            if len(self.schedule) > 1:
                self.rate_change = self.schedule[0]['months']
            self.minimal_payment = self.get_minimal_payment(
                current_debt = self.debt,
                interest_rate = self.schedule[0]['interest_rate'],
                months_left = self.months_left)
            self.closing_payment = self.debt + self.debt * self.interest_rate
            self.overpayed = 0
            self.__log_history('created')
        else:
            self.close()

    def __str__(self):
        return (
            'Name:\t\t\t' + str(self.name) + '\n' +
            'Is active:\t\t' + str(self.is_active) + '\n' +
            'Current debt:\t\t' + str(self.debt) + '\n' +
            'Interest rate:\t\t' + str(self.interest_rate) + '\n' +
            'Months left:\t\t' + str(self.months_left) + '\n' +
            'Minimal payment:\t' + str(self.minimal_payment) + '\n' +
            'Closing payment:\t' + str(self.closing_payment) + '\n' +
            'Already overpayed:\t' + str(self.overpayed))

    def __update_overpayed(self, overpay):
        self.overpayed += overpay

    def __update_schedule(self):
        if self.schedule[0]['months'] > 1:
            self.schedule[0]['months'] -= 1
        elif self.schedule[0]['months'] == 1:
            del self.schedule[0]

        self.interest_rate = self.schedule[0]['interest_rate']
        self.months_left = sum([x['months'] for x in self.schedule])
        self.minimal_payment = self.get_minimal_payment(
            current_debt=self.debt,
            interest_rate=self.schedule[0]['interest_rate'],
            months_left=self.months_left)
        self.closing_payment = self.debt + self.debt * self.interest_rate
        if len(self.schedule) > 1:
            self.rate_change = self.schedule[0]['months']
        else:
            self.rate_change = False

    def __log_history(self, action, data = None):
        self.history.append({
            'debt': self.debt,
            'interest_rate': self.interest_rate,
            'months_left': self.months_left,
            'minimal_payment': self.minimal_payment,
            'closing_payment': self.closing_payment,
            'action': action
        })
        if data is not None:
            self.history[len(self.history) - 1]['action_data'] = data

    def info(self):
        return {
            'name': self.name,
            'is_active': self.is_active,
            'debt': self.debt,
            'interest_rate': self.interest_rate,
            'months_left': self.months_left,
            'mininal_payment': self.minimal_payment,
            'closing_payment': self.closing_payment,
            'overpayed': self.overpayed
        }

    def close(self):
        self.is_active = False
        self.debt = 0
        self.schedule = []
        self.interest_rate = 0
        self.months_left = 0
        self.minimal_payment = 0
        self.closing_payment = 0

    # # If payment is set, then overpay, returns 0
    # # If payment doesn't set, pays minimal payment and return negative
    # # If payment is too much (after closing), returns positive
    
    def pay(self, payment=False):
        
        if self.is_active:
            
            # Payment wasn't set, minimal payment, return negative value
            
            if not payment:

                current_minimal_payment = self.minimal_payment

                previous_debt = self.debt

                self.debt = self.get_debt_after_period(
                    current_debt=self.debt,
                    interest_rate=self.interest_rate,
                    month_payment=current_minimal_payment,
                    months_passed=1,
                    months_left=self.months_left)

                self.__update_overpayed(current_minimal_payment - previous_debt + self.debt) 
                self.__update_schedule()
                self.__log_history('payment', {
                    'type': 'minimal_payment',
                    'sum': current_minimal_payment
                })

                return -self.minimal_payment

            # Payment was set, but payment is less than minimal payment
            
            x = math.floor(self.minimal_payment * 10e6)/10e6

            if payment and round(payment, precision) < round(x, precision):
                assert False, 'Not enough money:( Need: ' + str(x) + ', but have: ' + str(payment)
                return payment
            
            # Payment was set, payment is more than minimal payment (2 cases: overpay, closing pay)

            if payment < self.closing_payment:
                
                self.debt = self.get_debt_after_period(
                    current_debt=self.debt,
                    interest_rate=self.interest_rate,
                    month_payment=payment,
                    months_passed=1,
                    months_left=self.months_left)
                
                self.__update_schedule()
                self.__log_history('payment', {
                    'type': 'overpayment',
                    'sum': payment
                })

                return 0

            else:
                current_closing_payment = self.closing_payment
                change = payment - self.closing_payment
                self.close()
                self.__log_history('payment', {
                    'type': 'closing_payment',
                    'sum': current_closing_payment
                })
                return change
        
        else:
            return payment

    def get_history(self):
        return self.history
