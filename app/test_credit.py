import unittest
from credit import Credit
from errors import CreditError
from savings import precision


# TODO: problem with public functions, don't fit expected and gotten values

# STATIC METHODS


class TestGetMinimalPayment(unittest.TestCase):

    def test(self):
        expected = 55054.30667848049
        result = Credit.get_minimal_payment(current_debt=5000000,
                                            interest_rate=12/1200,
                                            months_left=240)
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)


class TestGetMinimalPaymentAfterPeriod(unittest.TestCase):

    def test__positive(self):
        expected = 49294.40810073759
        result = Credit.get_minimal_payment_after_period(current_debt=5000000,
                                                         interest_rate=12/1200,
                                                         months_left=240,
                                                         month_payment=100000,
                                                         months_passed=10)
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)

    def test__negative(self):
        expected = 'MP: need 55054 but have 30000'
        try:
            Credit.get_minimal_payment_after_period(current_debt=5000000,
                                                    interest_rate=12/1200,
                                                    months_left=240,
                                                    month_payment=30000,
                                                    months_passed=10)
        except CreditError as e:
            self.assertEqual(e.message, expected, 'Should be %s' % expected)


class TestGetDebtAfterPeriod(unittest.TestCase):

    def test__positive(self):
        expected = 4476889.372943977
        result = Credit.get_debt_after_period(current_debt=5000000,
                                              interest_rate=12/1200,
                                              months_left=240,
                                              month_payment=100000,
                                              months_passed=10)
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)

    def test__negative(self):
        expected = 'MP: need 55054 but have 30000'
        try:
            Credit.get_debt_after_period(current_debt=5000000,
                                         interest_rate=12/1200,
                                         months_left=240,
                                         month_payment=30000,
                                         months_passed=10)
        except CreditError as e:
            self.assertEqual(e.message, expected, 'Should be %s' % expected)

    def test__0_months_passed__positive(self):
        expected = 5000000
        result = Credit.get_debt_after_period(current_debt=5000000,
                                              interest_rate=12 / 1200,
                                              months_left=240,
                                              month_payment=100000,
                                              months_passed=0)
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)

    def test__0_months_passed__negative(self):
        expected = 'MP: need 55054 but have 30000'
        try:
            Credit.get_debt_after_period(current_debt=5000000,
                                         interest_rate=12 / 1200,
                                         months_left=240,
                                         month_payment=30000,
                                         months_passed=0)
        except CreditError as e:
            self.assertEqual(e.message, expected, 'Should be %s' % expected)


class TestGetPeriod(unittest.TestCase):

    def test(self):
        expected = 69.66071689357483
        result = Credit.get_period(current_debt=5000000,
                                   interest_rate=12/1200,
                                   month_payment=100000)
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)


# INSTANCE


class TestCreateInstance(unittest.TestCase):

    def test(self):
        crdt = Credit('name', 5000000, [
            {
                'interest_rate': 10 / 1200,
                'months': 12
            },{
                'interest_rate': 15 / 1200,
                'months': 228
            }
        ])
        self.assertEqual(isinstance(crdt, Credit), True, 'Should be %s' % True)


# METHODS


class TestInfoMethod(unittest.TestCase):

    def test(self):
        crdt = Credit('name', 5000000, [
            {
                'interest_rate': 10 / 1200,
                'months': 12
            }, {
                'interest_rate': 15 / 1200,
                'months': 228
            }
        ])
        crdt.pay(200000)
        crdt.pay()
        expected = {
            'name': 'name',
            'is_active': True,
            'debt': 4835229.147537185,
            'interest_rate': 0.008333333333333333,
            'months_left': 238,
            'mininal_payment': 46784.741351704906,
            'closing_payment': 4875522.723766661,
            'overpayed': 40347.222222222015
        }
        self.assertEqual(crdt.info(), expected, 'Should be %s' % expected)


class TestPayMethod(unittest.TestCase):

    def test__overpay(self):
        crdt = Credit('name', 5000000, [
            {
                'interest_rate': 10 / 1200,
                'months': 12
            },{
                'interest_rate': 15 / 1200,
                'months': 228
            }
        ])
        expected = 0
        result = crdt.pay(200000)
        self.assertEqual(result, expected, 'Should be %s' % expected)

    def test__minimal_pay(self):
        crdt = Credit('name', 5000000, [
            {
                'interest_rate': 10 / 1200,
                'months': 12
            }, {
                'interest_rate': 15 / 1200,
                'months': 228
            }
        ])
        expected = -46784.741351704906
        crdt.pay(200000)
        result = crdt.pay()
        self.assertEqual(result, expected, 'Should be %s' % expected)

    def test__closing_pay(self):
        crdt = Credit('name', 5000000, [
            {
                'interest_rate': 10 / 1200,
                'months': 12
            }, {
                'interest_rate': 15 / 1200,
                'months': 228
            }
        ])
        expected = 1000
        crdt.pay(200000)
        crdt.pay()
        result = crdt.pay(crdt.closing_payment + 1000)
        self.assertEqual(result, expected, 'Should be %s' % expected)


class TestGetHistory(unittest.TestCase):

    def test(self):
        crdt = Credit('name', 5000000, [
            {
                'interest_rate': 10 / 1200,
                'months': 12
            }, {
                'interest_rate': 15 / 1200,
                'months': 228
            }
        ])
        crdt.pay(200000)
        crdt.pay()
        expected = [
            {
                'action': 'created',
                'closing_payment': 5041666.666666667,
                'debt': 5000000,
                'interest_rate': 0.008333333333333333,
                'minimal_payment': 48251.08225370044,
                'months_left': 240
            },
            {
                'action': 'payment',
                'action_data': {
                    'sum': 200000,
                    'type': 'overpayment'
                },
                'closing_payment': 4882013.88888889,
                'debt': 4841666.666666668,
                'interest_rate': 0.008333333333333333,
                'minimal_payment': 46784.74135170491,
                'months_left': 239
            },
            {
                'action': 'payment',
                'action_data': {
                    'sum': 46784.74135170491,
                    'type': 'minimal_payment'
                },
                'closing_payment': 4875522.723766661,
                'debt': 4835229.147537185,
                'interest_rate': 0.008333333333333333,
                'minimal_payment': 46784.741351704906,
                'months_left': 238
            }
        ]
        self.assertEqual(crdt.get_history(), expected, 'Should be %s' % expected)
