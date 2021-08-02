from copy import deepcopy
from prettytable import PrettyTable
from utils import is_equal
from credit import Credit
from errors import BudgetError


precision = 0


class Budget:

    def __init__(self, savings=0, credits={}):
        # TODO: get rid of credits here
        self.savings = savings
        self.balance = 0
        self.months = 0
        self.scenario = []
        # TODO: make adding credits through the function
        self.credits = credits
        self.scenario.append({'cmd': 'initiate', 'payload': {'savings': savings}})
        # TODO: place correct debts to make possible work with debts not from the begining
        self.history = [{
            "incomes": {
                "before_savings": self.savings,
                "regular_income": 0,
                "irregular_income": 0,
            },
            "expenses": {
                "regular_expenses": 0,
                "irregular_expenses": 0,
            },
            "to_save": 0,
            "last_save": 0,
            "after_savings": self.savings,
        }]

    def __str__(self):
        credits_list = ''
        for _, credit in self.credits.items():
            credits_list += credit.name + \
                ' debt: ' + str(credit.debt) + \
                ' interest rate: ' + str(credit.interest_rate) + \
                ' minimal payment: ' + str(credit.minimal_payment) + \
                ' closing payment: ' + str(credit.closing_payment) + '\n'

        return (
            'Balance:\t\t' + str(self.balance) + '\n' +
            'Savings:\t\t' + str(self.savings) + '\n' +
            'Months:\t\t' + str(self.months) + '\n' +
            'Scenario:\t\t' + str(self.scenario) + '\n' +
            'Month history:\t\t' + str(self.history) + '\n' +
            credits_list
        )

    def add_savings(self, savings=0):
        self.savings += savings
        self.scenario.append({'cmd': 'add_savings', 'payload': {'savings': savings}})
        l_m = self.history[len(self.history) - 1]
        l_m['incomes']['irregular_income'] += savings
        l_m['after_savings'] += savings

    def get_credit(self, name, requested_sum, schedule, minimal_initial_sum=0, expenses=0):
        assert self.savings >= minimal_initial_sum + expenses, 'Not enough money to start credit....'
        self.savings -= expenses
        self.credits[name] = Credit(name=name, debt=requested_sum, schedule=schedule)
        self.savings += requested_sum
        self.scenario.append({'cmd': 'get_credit',
                              'payload': {'name': name,
                                          'requested_sum': requested_sum,
                                          'schedule': deepcopy(schedule),
                                          'minimal_initial_sum': minimal_initial_sum,
                                          'expenses': expenses}})
        l_m = self.history[len(self.history) - 1]
        if 'debts' not in l_m:
            l_m['debts'] = {}
        l_m['debts'][name] = {
            'interest_rate': self.credits[name].interest_rate,
            'before_debt': 0,
            'before_minimal_payment': 0,
            'before_closing_payment': 0,
            'actual_payment': 0,
            'after_debt': self.credits[name].debt,
            'after_minimal_payment': self.credits[name].minimal_payment,
            'after_closing_payment': self.credits[name].closing_payment,
        }
        l_m['incomes']['irregular_income'] = requested_sum
        l_m['expenses']['irregular_expenses'] += expenses
        l_m['after_savings'] += requested_sum
        l_m['after_savings'] -= expenses

    def spend_savings(self, **extra_expencies):

        total_expencies = sum([x for x in extra_expencies.values()])
        if round(total_expencies, precision) > round(self.savings, precision):
            raise BudgetError('EXP', {'have': self.savings, 'need': total_expencies})
        self.savings -= total_expencies
        self.scenario.append({'cmd': 'spend_savings', 'payload': {**extra_expencies}})

        l_m = self.history[len(self.history) - 1]
        for key, value in extra_expencies.items():
            self.history[len(self.history) - 1]['expenses']['irregular_expenses'] += value
            l_m['after_savings'] -= value

    def make_month(self, earned=0, month_rent=None, month_expenses=None, to_save=None):

        l_m = {
            "debts": {},
            "incomes": {
                "before_savings": self.savings,
                "regular_income": earned,
                "irregular_income": 0,
            },
            "expenses": {
                "regular_expenses": 0,
                "irregular_expenses": 0,
            },
            "to_save": 0,
            "last_save": 0,
            "after_savings": 0,
        }

        self.balance += earned

        # TODO: get rid of that shit
        expenses = {}
        if month_expenses is not None:
            expenses.update({"month_expenses": month_expenses})
        if month_rent is not None:
            expenses.update({"month_rent": month_rent})

        if expenses is not None:
            total_expencies = sum([x for x in expenses.values()])
            assert round(total_expencies, precision) < round(self.balance, precision), 'Not enough money for expencies'
            self.balance -= total_expencies

            if 'month_expenses' in expenses:
                l_m['expenses']['regular_expenses'] += expenses['month_expenses']
            if 'month_rent' in expenses:
                l_m['expenses']['regular_expenses'] += expenses['month_rent']

        minimal_credit_payments = {}

        if self.credits is not None and len(self.credits) > 0:
            
            # TODO: sort only if necessary
            
            self.credits = {key: self.credits[key] for key
                            in sorted(self.credits, key=lambda item: self.credits[item].interest_rate, reverse=True)}
            for key, credit in self.credits.items():
                minimal_credit_payments[key] = credit.minimal_payment
                l_m["debts"][key] = {
                    'interest_rate': credit.interest_rate,
                    'before_debt': credit.debt,
                    'before_minimal_payment': credit.minimal_payment,
                    'before_closing_payment': credit.closing_payment,
                    'actual_payment': credit.minimal_payment,
                }
            total_payments = sum([x for x in minimal_credit_payments.values()])
            if round(total_payments, precision) > round(self.balance, precision):
                if 'Mortgage' in self.credits and len(self.credits) > 1:
                    raise BudgetError('MRG_MP + CRD_MP', {'need': total_payments, 'have': self.balance})
                else:
                    raise BudgetError('MRG_MP', {'need': total_payments, 'have': self.balance})
            self.balance -= total_payments

        if to_save is not None and to_save != 'None' and to_save != 0:
            assert round(to_save, precision) <= round(self.balance, precision),\
                'Not enough money for saving, need %f, have %f' % (to_save, self.balance)
            self.balance -= to_save
            self.savings += to_save
            l_m['to_save'] = to_save

        if len(minimal_credit_payments) > 0:
            for key in minimal_credit_payments.keys():
                pay = self.balance + minimal_credit_payments[key]
                l_m['debts'][key]['actual_payment'] = pay
                self.balance = self.credits[key].pay(self.balance + minimal_credit_payments[key])
                l_m['debts'][key]['actual_payment'] -= self.balance
                l_m['debts'][key].update({
                    'after_debt': self.credits[key].debt,
                    'after_minimal_payment': self.credits[key].minimal_payment,
                    'after_closing_payment': self.credits[key].closing_payment,
                })
                if self.credits[key].debt <= 0:
                    del self.credits[key]

        self.savings += self.balance

        l_m['last_save'] = self.balance
        self.balance = 0
        self.months += 1

        new_step = {'cmd': 'make_month'}
        if earned is not None and earned >= 0:
            new_step['payload'] = {'earned': earned}
        if month_rent is not None and round(month_rent, precision) > 0:
            if 'payload' not in new_step:
                new_step['payload'] = {}
            new_step['payload'].update({'month_rent': month_rent})
        if month_expenses is not None and round(month_expenses, precision) > 0:
            if 'payload' not in new_step:
                new_step['payload'] = {}
            new_step['payload'].update({'month_expenses': month_expenses})
        if to_save is not None and round(to_save, precision) > 0:
            if 'payload' not in new_step:
                new_step['payload'] = {}
            new_step['payload'].update({'to_save': to_save})

        last = self.scenario[len(self.scenario) - 1]

        if last['cmd'] == 'make_month':
            if 'times' in last:
                last_copy = deepcopy(last)
                del last_copy['times']
                if is_equal(new_step, last_copy, precision):
                    self.scenario[len(self.scenario) - 1]['times'] += 1
                else:
                    self.scenario.append(new_step)
            elif is_equal(new_step, last, precision):
                self.scenario[len(self.scenario) - 1]['times'] = 2
            else:
                self.scenario.append(new_step)
        else:
            self.scenario.append(new_step)

        l_m['after_savings'] += self.savings
        if len(l_m['debts']) == 0:
            del l_m['debts']
        self.history.append(l_m)

    def print_history(self, history=None):

        # There are two ways to print:
        # 1. Budget.print_history(hst) — prints hst history list
        # 2. bt.print_history() — prints history of bt budget object

        if history is None:
            history = self.history

        table = PrettyTable()
        table.field_names = ['Month', 'Savings_i', 'Regular_i', 'Irreg_i', 'Total_i', 'Reg_ex', 'Irreg_ex',
           'Mort.i.r.', 'Mort.d', 'Mort.m.p.', 'Mort.c.p', '-Mort.d', '-Mort.m.p.', '-Mort.c.p', 'Mort.a.p',
           'Rep.i.r.', 'Rep.d', 'Rep.m.p.', 'Rep.c.p.', '-Rep.d', '-Rep.m.p.', '-Rep.c.p.', 'Rep.a.p',
           'To_Save', 'Last_Save', 'Savings_o']

        for i, month in enumerate(history):
           a = month['incomes']['before_savings'] if month['incomes']['before_savings'] is not None else 0
           b = month['incomes']['regular_income'] if month['incomes']['regular_income'] is not None else 0
           c = month['incomes']['irregular_income'] if month['incomes']['irregular_income'] is not None else 0
           total_income = a + b + c
           row = [
              i,
              round(month['incomes']['before_savings'], 0) if month['incomes']['before_savings'] is not None else '—',
              round(month['incomes']['regular_income'], 0) if month['incomes']['regular_income'] is not None else '—',
              round(month['incomes']['irregular_income'], 0) if month['incomes']['irregular_income'] is not None else '—',
              round(total_income, 0),
              round(month['expenses']['expenses']['regular_expenses'], 0) if month['expenses']['expenses']['regular_expenses'] is not None else '—',
              round(month['expenses']['expenses']['irregular_expenses'], 0) if month['expenses']['expenses']['irregular_expenses'] is not None else '—',

              round(month['debts']['Mortgage']['interest_rate'], 4) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['interest_rate'] is not None else '—',
              round(month['debts']['Mortgage']['before_debt'], 0) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['before_debt'] is not None else '—',
              round(month['debts']['Mortgage']['before_minimal_payment'], 0) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['before_minimal_payment'] is not None else '—',
              round(month['debts']['Mortgage']['before_closing_payment'], 0) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['before_closing_payment'] is not None else '—',
              round(month['debts']['Mortgage']['after_debt'], 0) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['after_debt'] is not None else '—',
              round(month['debts']['Mortgage']['after_minimal_payment'], 0) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['after_minimal_payment'] is not None else '—',
              round(month['debts']['Mortgage']['after_closing_payment'], 0) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['after_closing_payment'] is not None else '—',
              round(month['debts']['Mortgage']['actual_payment'], 0) if len(month['debts']) != 0 and 'Mortgage' in month['debts'] and month['debts']['Mortgage']['actual_payment'] is not None else '—',

              round(month['debts']['Repairing']['interest_rate'], 4) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['interest_rate'] is not None else '—',
              round(month['debts']['Repairing']['before_debt'], 0) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['before_debt'] is not None else '—',
              round(month['debts']['Repairing']['before_minimal_payment'], 0) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['before_minimal_payment'] is not None else '—',
              round(month['debts']['Repairing']['before_closing_payment'], 0) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['before_closing_payment'] is not None else '—',
              round(month['debts']['Repairing']['after_debt'], 0) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['after_debt'] is not None else '—',
              round(month['debts']['Repairing']['after_minimal_payment'], 0) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['after_minimal_payment'] is not None else '—',
              round(month['debts']['Repairing']['after_closing_payment'], 0) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['after_closing_payment'] is not None else '—',
              round(month['debts']['Repairing']['actual_payment'], 0) if len(month['debts']) != 0 and 'Repairing' in month['debts'] and month['debts']['Repairing']['actual_payment'] is not None else '—',

              round(month['to_save'], 0) if month['to_save'] is not None else '—',
              round(month['last_save'], 0) if month['last_save'] is not None else '—',
              round(month['after_savings'], 0) if month['after_savings'] is not None else '—',
           ]
           table.add_row(row)

        print(table)

    @staticmethod
    def execute(scenario):

        # TODO: validate scenario

        commands = {
            'add_savings': lambda inst, **kargs: Budget.add_savings(inst, **kargs),
            'get_credit': lambda inst, **kargs: Budget.get_credit(inst, **kargs),
            'make_month': lambda inst, **kargs: Budget.make_month(inst, **kargs),
            'spend_savings': lambda inst, **kargs: Budget.spend_savings(inst, **kargs),
        }

        if scenario[0]['cmd'] != 'initiate':
            assert False, 'First command should be "initiate"'

        bt = None

        for command in scenario:

            if command['cmd'] == 'initiate':
                if 'payload' in command:
                    bt = Budget(**command['payload'])
                else:
                    bt = Budget()
                continue

            k = command['times'] if 'times' in command else 1
            for _ in range(k):
                if 'payload' not in command or len(command['payload']) == 0:
                    if command['cmd'] == 'get_credit':
                        continue
                    commands[command['cmd']](bt)
                else:
                    commands[command['cmd']](bt, **command['payload'])

        return bt
