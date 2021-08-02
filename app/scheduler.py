from prettytable import PrettyTable
from copy import deepcopy
from credit import Credit
from budget import Budget
from savings import SavingsSolver
from errors import PlanError, SavingsError, BudgetError, CreditError

# Debug mode prints all tables I = Scheduler(data, debug=True)
# TODO: refactor all class, use exceptions instead of if/else statements, make exception where needed


class Scheduler:

    def __init__(self, input_data, debug=False):

        # TODO: validate input data

        self.input_data = input_data

        personal_data = self.input_data['personal_data']
        credit_scheme = self.input_data['credit_scheme'] if 'credit_scheme' in self.input_data else None
        realties = self.input_data['realties']
        use_no_mortgage = self.input_data['use_no_mortgage']
        mortgage_schemes = self.input_data['mortgage_schemes'] if 'mortgage_schemes' in self.input_data else None

        self.solution = {}

        for rlt_id, realty in realties.items():

            self.solution.update({
                rlt_id: {}
            })

            data = self.converter(personal_data, realty, credit_scheme)

            if use_no_mortgage:
                no_mrg_result = self.__plan_no_mrg(data)

                if debug:
                    print('Optimum:', no_mrg_result['opt'])
                    table = PrettyTable()
                    table.field_names = ['x_1,2', 'With Savings', 'With Credit']
                    for key, row in no_mrg_result['combs'].items():
                        table.add_row(
                            [key, row['savings'] if 'savings' in row else '—', row['credit'] if 'credit' in row else '—'])
                    print(table)

                self.solution[rlt_id]['without_mortgage'] = no_mrg_result
                self.solution[rlt_id]['with_credit'] = False if credit_scheme is None else True

            # TODO: if found SuperGood, than don't do next steps

            if mortgage_schemes is not None:
                self.solution[rlt_id]['with_mortgage'] = {}
                for mrg_id, mortgage_scheme in mortgage_schemes.items():

                    data = self.converter(personal_data, realty, credit_scheme, mortgage_scheme)

                    result = self.__plan(data)
                    if debug:
                        print('Optimum:', result['opt'])
                        table = PrettyTable()
                        table.field_names = ['x_1,2', 'With Savings', 'With Credit']
                        for key, row in result['combs'].items():
                            table.add_row([key,
                                           'BOTH:' + str(row['both']) if 'both' in row
                                           else row['savings'] if 'savings' in row else '—',
                                           row['credit'] if 'credit' in row else '—'])
                        print(table)

                    self.solution[rlt_id]['with_mortgage'][mrg_id] = result
                    self.solution[rlt_id]['with_credit'] = False if credit_scheme is None else True

    @staticmethod
    def converter(personal_data, realty, credit_scheme, mortgage_scheme=None):
        result = {
            'deal_month_start': personal_data['deal_month_start'],
            'deal_month_finish': personal_data['deal_month_finish'],
            'get_keys_after_months': realty['get_keys_month'] if 'get_keys_month' in realty else 0,
            'max_repairing_gap': personal_data['max_repairing_delay_months'],
            'current_savings': personal_data['current_savings'],
            'month_income': personal_data['month_income'] - personal_data['month_expenses'],
            'month_rent': personal_data['month_rent'],
            'realty_cost': realty['cost'],
            'inflation_percent': personal_data['inflation_percent'],
            'repairing_schedule': None if credit_scheme is None else [{'interest_rate': credit_scheme['interest_rate'],
                                                                       'months': credit_scheme['months']}],
            'repairing_cost': realty['repairing_expenses'],
            'repairing_months': realty['repairing_months'],
        }
        if mortgage_scheme is not None:
            result.update({
                'initial_payment_percent': mortgage_scheme['initial_payment_percent'],
                'mortgage_expencies': mortgage_scheme['initial_expenses'],
                'mortgage_schedule': [{'interest_rate': float(x['interest_rate']),
                                       'months': x['months']} for x in mortgage_scheme['schedule']]
            })

        return result

    # TODO: severe refactoring has to be done

    def __plan_no_mrg(self, data):
        mrg__d_s = data['deal_month_start']
        mrg__d_f = data['deal_month_finish']
        rep__delay = data['max_repairing_gap']
        S_i = data['current_savings']
        m_income = data['month_income']
        m_rent = data['month_rent']
        realty_cost = data['realty_cost']
        repairing_cost = data['repairing_cost']
        repairing_months = data['repairing_months']
        repairing_schedule = data['repairing_schedule']
        with_credit = False if data['repairing_schedule'] is None else True

        opt = None
        combs = {}

        # TODO: get rid of outside look, just set x_1 = mrg__d_s (if inflation doesn't matters)

        for x_1 in range(mrg__d_s, mrg__d_f):

            mth = 0

            # TODO: make as a secondary realty

            is_primary = True if 'is_primary' not in data or data['is_primary'] else False
            if is_primary and x_1 > data['get_keys_after_months']:
                # TODO: get rid of unnecessary x_2 param
                combs[(x_1,)] = {
                    'savings': {
                        'success': False,
                        'code': 'x_1 > g_k',
                        'message': 'Should be primary!',
                    }
                }
                if with_credit:
                    combs[(x_1,)].update({
                        'credit': {
                            'success': False,
                            'code': 'x_1 > g_k',
                            'message': 'Should be primary!',
                        }
                    })

                continue

            try:
                bt = Budget(savings=S_i)

                for _ in range(x_1):
                    bt.make_month(earned=m_income, month_rent=m_rent)
                    mth += 1

                for x_2 in range(rep__delay):

                    combs[(x_1, x_2)] = {'savings': {}}
                    if with_credit:
                        combs[(x_1, x_2)].update({'credit': {}})

                    if bt.savings >= realty_cost:
                        is_primary = True if 'is_primary' not in data or data['is_primary'] else False
                        if is_primary:
                            get_keys_after_months = data['get_keys_after_months']
                        else:
                            get_keys_after_months = x_1
                        bt_copy = deepcopy(bt)
                        mth_new = mth
                        gap = get_keys_after_months - x_1 + x_2
                        bt_copy.spend_savings(buy_realty=realty_cost)
                        for _ in range(gap):
                            mth_new += 1
                            bt_copy.make_month(earned=m_income, month_rent=m_rent)
                        if bt_copy.savings >= repairing_cost:
                            bt_copy.spend_savings(repairing=repairing_cost)
                            for _ in range(repairing_months):
                                mth_new += 1
                                bt_copy.make_month(earned=m_income, month_rent=m_rent)
                            criteria = bt_copy.months - bt_copy.savings / m_income
                            if opt is None or 'savings' not in opt or criteria < opt['savings']['result']['criteria']:
                                new_savings = {'savings': {
                                    'case': 'S_i > C, S > S_t',
                                    'x': (x_1, x_2),
                                    'scenario': bt_copy.scenario,
                                    'result': {
                                        'months': bt_copy.months,
                                        'savings': bt_copy.savings,
                                        'criteria': criteria,
                                    },
                                    'schedule': Budget.execute(bt_copy.scenario).history
                                }}
                                if opt is None:
                                    opt = new_savings
                                else:
                                    opt.update(new_savings)

                            combs[(x_1, x_2)]['savings'] = {
                                'success': True,
                                'months': bt_copy.months,
                                'savings': bt_copy.savings,
                                'criteria': criteria,
                            }

                            if with_credit:
                                combs[(x_1, x_2)]['credit'] = {
                                    'success': False,
                                    'code': 'S_i > C, S > S_t',
                                    'message': 'Not needed',
                                }

                        else:
                            combs[(x_1, x_2)]['savings'] = {
                                'success': False,
                                'code': 'S_i > C, S < S_t',
                                'payload': {
                                    'have': bt_copy.savings,
                                    'need': repairing_cost,
                                }
                            }
                            if with_credit:
                                try:
                                    store_months_c = self.__crd(data, deepcopy(bt_copy), x_1, x_2, mth_new)
                                    if store_months_c is not None:
                                        criteria = store_months_c[2].months - store_months_c[2].savings / m_income
                                        if opt is None or 'credit' not in opt or criteria < opt['credit']['result']['criteria']:
                                            new_credit = {'credit': {
                                                'case': 'S_i > C, S < S_t',
                                                'x': (x_1, x_2),
                                                'scenario': store_months_c[2].scenario,
                                                'result': {
                                                    'months': store_months_c[2].months,
                                                    'savings': store_months_c[2].savings,
                                                    'criteria': criteria,
                                                },
                                                'schedule': Budget.execute(store_months_c[2].scenario).history
                                            }}
                                            if opt is None:
                                                opt = new_credit
                                            else:
                                                opt.update(new_credit)

                                        combs[(x_1, x_2)]['credit'] = {
                                            'success': True,
                                            'months': store_months_c[2].months,  # store_months_c[0],
                                            'savings': store_months_c[2].savings,  # store_months_c[1],
                                            'criteria': criteria,  # store_months_c[0] - store_months_c[1] / m_income,
                                        }
                                    else:
                                        # TODO: make it as an exception (if this code is reachable)
                                        combs[(x_1, x_2)]['credit'] = {
                                            'success': False,
                                            'code': None,
                                            'message': 'NO MRG. No errollkjkldjaf askljf  iwruoiweqrkwlej r weerkjwqeoir ulkaj drkjqer, credit impossible!!!!',
                                        }
                                except (BudgetError, AssertionError) as e:
                                    if isinstance(e, BudgetError):
                                        combs[(x_1, x_2)]['credit'] = {
                                            'success': False,
                                            'code': e.code,
                                            'palyload': e.payload,
                                            'message': e.message,
                                        }
                                    if isinstance(e, AssertionError):
                                        combs[(x_1, x_2)]['credit'] = {
                                            'success': False,
                                            'code': 'Assertion',
                                            'message': e.message,
                                        }
                    else:
                        combs[(x_1, x_2)]['savings'] = {
                            'success': False,
                            'code': 'S_i < C',
                            'payload': {
                                'have': bt.savings,
                                'need': realty_cost,
                            }
                        }
                        if with_credit:
                            combs[(x_1, x_2)]['credit'] = {
                                'success': False,
                                'code': 'S_i < C',
                                'payload': {
                                    'have': bt.savings,
                                    'need': realty_cost,
                                }
                            }

            except (PlanError, AssertionError) as e:
                if isinstance(e, PlanError):
                    combs[x_1] = {
                        'savings': {
                            'success': False,
                            'code': e.code,
                            'payload': e.payload,
                            'message': e.message,
                        }
                    }
                    if with_credit:
                        combs[x_1].update({
                            'credit': {
                                'success': False,
                                'code': e.code,
                                'payload': e.payload,
                                'message': e.message,
                            }
                        })

                if isinstance(e, AssertionError):
                    combs[x_1] = {
                        'savings': {
                            'success': False,
                            'code': 'Assertion',
                            'message': e.message,
                        }
                    }
                    if with_credit:
                        combs[x_1].update({
                            'credit': {
                                'success': False,
                                'code': 'Assertion',
                                'message': e.message,
                            }
                        })
                continue

        return {
            'opt': opt if opt is not None else None,
            'combs': combs,
        }

    def __plan(self, data):
        mrg__d_s = data['deal_month_start']
        mrg__d_f = data['deal_month_finish']
        rep__delay = data['max_repairing_gap']
        S_i = data['current_savings']
        m_income = data['month_income']
        m_rent = data['month_rent']
        C = data['realty_cost']
        IP_min = C * data['initial_payment_percent'] / 100
        R = data['mortgage_expencies']
        realty_cost = data['realty_cost']
        repairing_schedule = data['repairing_schedule']
        with_credit = False if data['repairing_schedule'] is None else True

        opt = None
        combs = {}

        for x_1 in range(mrg__d_s, mrg__d_f):

            mth = 0

            # TODO: make a special message for such realty!

            is_primary = True if 'is_primary' not in data or data['is_primary'] else False
            if is_primary and x_1 > data['get_keys_after_months']:
                combs[(x_1,)] = {
                    'savings': {
                        'success': False,
                        'message': 'Should be primary!',
                    }
                }
                if with_credit:
                    combs[(x_1,)].update({
                        'credit': {
                            'success': False,
                            'message': 'Should be primary!',
                        }
                    })
                continue

            try:
                bt = Budget(savings=S_i)

                for _ in range(x_1):
                    bt.make_month(earned=m_income, month_rent=m_rent)
                    mth += 1

                if bt.savings < IP_min + R:
                    raise PlanError('S_i < IP_min + R', {'need': IP_min + R, 'have': bt.savings})

                for x_2 in range(rep__delay):
                    combs[(x_1, x_2)] = {'savings': {}}
                    if with_credit:
                        combs[(x_1, x_2)].update({'credit': {}})

                    if with_credit:
                        if bt.savings >= realty_cost:
                            combs[(x_1, x_2)]['credit'] = {
                                'success': False,
                                'code': 'S_i > C, Not needed',
                            }
                        else:
                            try:
                                store_months_c = self.__mrg_crd(data, deepcopy(bt), x_1, x_2, mth)
                                if store_months_c is not None:
                                    criteria = store_months_c[2].months - store_months_c[2].savings / m_income
                                    if opt is None or 'credit' not in opt or criteria < opt['credit']['result']['criteria']:
                                        new_credit = {'credit': {
                                            'case': 'S_i < C, S < S_t',
                                            'x': (x_1, x_2),
                                            'scenario': store_months_c[2].scenario,
                                            'result': {
                                                'months': store_months_c[2].months,
                                                'savings': store_months_c[2].savings,
                                                'criteria': criteria,
                                            },
                                            'schedule': Budget.execute(store_months_c[2].scenario).history
                                        }}
                                        if opt is None:
                                            opt = new_credit
                                        else:
                                            opt.update(new_credit)
                                    combs[(x_1, x_2)]['credit'] = {
                                        'success': True,
                                        'months': store_months_c[2].months,  # store_months_c[0],
                                        'savings': store_months_c[2].savings,  # store_months_c[1],
                                        'criteria': criteria,  # store_months_c[0] - store_months_c[1] / m_income
                                    }
                                else:
                                    combs[(x_1, x_2)]['credit'] = {
                                        'success': False,
                                        'code': None,
                                        'message': 'MRG. No error, creditkflas djfqwk jekrjkj werlkjqWQ@!@$@%#^@%#$%@$#%#@^#%$^#$ impossible',
                                    }
                            except (BudgetError, AssertionError) as e:
                                if isinstance(e, BudgetError):
                                    combs[(x_1, x_2)]['credit'] = {
                                        'success': False,
                                        'code': e.code,
                                        'payload': e.payload,
                                    }
                                if isinstance(e, AssertionError):
                                    combs[(x_1, x_2)]['credit'] = {
                                        'success': False,
                                        'code': 'Assertion',
                                        'message': e.message,
                                    }

                    try:
                        store_months_s = self.__mrg_svn(data, deepcopy(bt), x_1, x_2, mth)
                        if store_months_s is not None:
                            criteria = store_months_s[2].months - store_months_s[2].savings / m_income
                            if opt is None or 'savings' not in opt or criteria < opt['savings']['result']['criteria']:
                                new_savings = {'savings': {
                                    'case': 'S_i < C, S < S_t',
                                    'x': (x_1, x_2),
                                    'scenario': store_months_s[2].scenario,
                                    'result': {
                                        'months': store_months_s[2].months,
                                        'savings': store_months_s[2].savings,
                                        'criteria': criteria,
                                    },
                                    'schedule': Budget.execute(store_months_s[2].scenario).history
                                }}
                                if opt is None:
                                    opt = new_savings
                                else:
                                    opt.update(new_savings)
                            combs[(x_1, x_2)]['savings'] = {
                                'success': True,
                                'months': store_months_s[2].months,  # store_months_s[0],
                                'savings': store_months_s[2].savings,  # store_months_s[1],
                                'criteria': criteria,  # store_months_s[0] - store_months_s[1] / m_income
                            }
                        else:
                            combs[(x_1, x_2)]['savings'] = {
                                'success': False,
                                'code': 'INFEASIBLE',
                            }
                    except (BudgetError, SavingsError, AssertionError) as e:
                        if isinstance(e, BudgetError):
                            combs[(x_1, x_2)]['savings'] = {
                                'success': False,
                                'code': e.code,
                                'payload': e.payload,
                            }
                        if isinstance(e, CreditError):
                            combs[(x_1, x_2)]['savings'] = {
                                'success': False,
                                'code': e.code,
                                'payload': e.payload,
                            }
                        if isinstance(e, SavingsError):
                            combs[(x_1, x_2)]['savings'] = {
                                'success': False,
                                'code': 'S_i > C, S > S_t',
                                'message': 'Not needed',
                            }
                        if isinstance(e, AssertionError):
                            combs[(x_1, x_2)]['savings'] = {
                                'success': False,
                                'code': 'Assertion',
                                'message': e.message,
                            }
                        else:
                            pass

            except (PlanError, AssertionError) as e:
                if isinstance(e, PlanError):
                    combs[x_1] = {
                        'savings': {
                            'success': False,
                            'code': e.code,
                            'payload': e.payload,
                            'message': e.message,
                        }
                    }
                    if with_credit:
                        combs[x_1].update({
                            'credit': {
                                'success': False,
                                'code': e.code,
                                'payload': e.payload,
                                'message': e.message,
                            }
                        })
                if isinstance(e, AssertionError):
                    combs[x_1] = {
                        'savings': {
                            'success': False,
                            'code': 'Assertion',
                            'message': e.message,
                        }
                    }
                    if with_credit:
                        combs[x_1].update({
                            'credit': {
                                'success': False,
                                'code': 'Assertion',
                                'message': e.message,
                            }
                        })
                continue

        # function to detect optimal plan

        return {
            'opt': opt if opt is not None else None,
            'combs': combs,
        }

    @staticmethod
    def __crd(data, bt, x_1, x_2, mth):
        m_income = data['month_income']
        m_rent = data['month_rent']
        repairing_cost = data['repairing_cost']
        repairing_schedule = deepcopy(data['repairing_schedule'])
        repairing_months = data['repairing_months']

        credit_debt = repairing_cost - bt.savings
        credit_MP = Credit.get_minimal_payment(
            current_debt=credit_debt,
            interest_rate=data['repairing_schedule'][0]['interest_rate'],
            months_left=data['repairing_schedule'][0]['months']
        )

        if credit_MP > m_income - m_rent:
            raise BudgetError('CRD_MP', {'need': credit_MP, 'have': m_income - m_rent})
        else:
            bt.get_credit(name='Repairing', requested_sum=repairing_cost - bt.savings,
                          schedule=deepcopy(repairing_schedule))
            bt.spend_savings(repairing=repairing_cost)

            for _ in range(repairing_months):
                mth += 1
                bt.make_month(earned=m_income, month_rent=m_rent)

            max_months = 2000
            while len(bt.credits) > 0:
                mth += 1
                bt.make_month(earned=m_income)
                # TODO: put here an error, credit cant be payed in time, or make limit equal to credit duration
                if mth > max_months:
                    break

            return mth, bt.savings, bt

    @staticmethod
    def __mrg_crd(data, bt, x_1, x_2, mth):
        is_primary = True if 'is_primary' not in data or data['is_primary'] else False
        if is_primary:
            get_keys_after_months = data['get_keys_after_months']
        else:
            get_keys_after_months = x_1
        repairing_months = data['repairing_months']
        month_income = data['month_income']
        month_rent = data['month_rent']
        realty_cost = data['realty_cost']
        inflation_percent = data['inflation_percent']
        initial_payment_percent = data['initial_payment_percent']
        mortgage_expencies = data['mortgage_expencies']
        mortgage_schedule = data['mortgage_schedule']
        repairing_cost = data['repairing_cost']
        repairing_schedule = deepcopy(data['repairing_schedule'])

        actual_realty_cost = realty_cost * (1 + inflation_percent * mth / 1200)
        bt.get_credit(
            name='Mortgage',
            requested_sum=actual_realty_cost - bt.savings + mortgage_expencies,
            minimal_initial_sum=actual_realty_cost * initial_payment_percent / 100,
            expenses=mortgage_expencies,
            schedule=deepcopy(mortgage_schedule))

        bt.spend_savings(buy_realty=realty_cost)

        for _ in range(get_keys_after_months - x_1):
            mth += 1
            bt.make_month(earned=month_income, month_rent=month_rent)

        for _ in range(x_2):
            mth += 1
            bt.make_month(earned=month_income, month_rent=month_rent)

        bt.get_credit(name='Repairing', requested_sum=repairing_cost, schedule=deepcopy(repairing_schedule))

        bt.spend_savings(repairing=repairing_cost)

        for _ in range(repairing_months):
            mth += 1
            bt.make_month(earned=month_income, month_rent=month_rent)

        # TODO: should be changed for something concrete

        for _ in range(1, 100):
            mth += 1
            if len(bt.credits) > 0:
                bt.make_month(earned=month_income)
                continue

            return mth, bt.savings, bt

        return None

    @staticmethod
    def __mrg_svn(data, bt, x_1, x_2, mth):
        is_primary = True if 'is_primary' not in data or data['is_primary'] else False
        if is_primary:
            get_keys_after_months = data['get_keys_after_months']
        else:
            get_keys_after_months = x_1
        repairing_months = data['repairing_months']
        month_income = data['month_income']
        month_rent = data['month_rent']
        realty_cost = data['realty_cost']
        inflation_percent = data['inflation_percent']
        initial_payment_percent = data['initial_payment_percent']
        mortgage_expencies = data['mortgage_expencies']
        mortgage_schedule = data['mortgage_schedule']
        repairing_cost = data['repairing_cost']

        actual_realty_cost = realty_cost * (1 + inflation_percent * mth / 1200)
        params = {
            'C': actual_realty_cost,
            'S_i': bt.savings,
            'R': mortgage_expencies,
            'n': sum([x['months'] for x in mortgage_schedule]),
            'I': month_income - month_rent,
            'S_t': repairing_cost,
            'IP_min': actual_realty_cost * initial_payment_percent / 100,
        }
        if len(mortgage_schedule) > 1 and mortgage_schedule[0]['months'] < get_keys_after_months + x_2 - mth:
            params['k_1'] = mortgage_schedule[0]['interest_rate']
            params['k_2'] = mortgage_schedule[1]['interest_rate']
            params['l'] = mortgage_schedule[0]['months']
            params['m'] = get_keys_after_months + x_2 - mth - mortgage_schedule[0]['months']
        else:
            params['k_1'] = mortgage_schedule[0]['interest_rate']
            params['l'] = get_keys_after_months + x_2 - mth

        problem = SavingsSolver(params, launch=True)
        if problem.solution is None:
            return None

        req_sum = actual_realty_cost - bt.savings + mortgage_expencies + problem.solution['save_before']
        bt.get_credit(
            name='Mortgage',
            requested_sum=req_sum,
            minimal_initial_sum=actual_realty_cost * initial_payment_percent / 100,
            expenses=mortgage_expencies,
            schedule=deepcopy(mortgage_schedule))
        bt.spend_savings(buy_realty=realty_cost)

        g = params['l'] if 'm' not in params else params['l'] + params['m']
        save_state = {
            'save': False,
            'next_savings': None,
        }

        for i in range(g):
            if (i == problem.solution['scheme'][0]['month'] or
                    (len(problem.solution['scheme']) > 1 and i == problem.solution['scheme'][1]['month'] + params['l'])):

                period = problem.solution['scheme'][0] if i == problem.solution['scheme'][0]['month'] \
                    else problem.solution['scheme'][1]
                mth += 1
                if 'init_save' not in period:
                    period['init_save'] = params['I'] - bt.credits['Mortgage'].minimal_payment \
                        if 'Mortgage' in bt.credits else params['I']
                bt.make_month(earned=month_income, month_rent=month_rent, to_save=period['init_save'])
                if i != params['l'] and (('m' not in params) or ('m' in params and i != params['m'] + params['l'])):
                    save_state = {
                        'save': True,
                        'next_savings': period['next_savings'] if 'next_savings' in period else None
                    }
                continue

            if 'Mortgage' in bt.credits and round(bt.credits['Mortgage'].debt, 2) != 0:
                if i == params['l'] or ('m' in params and i == params['m'] + params['l']):
                    save_state = {
                        'save': False,
                        'next_savings': None,
                    }
                MP = bt.credits['Mortgage'].minimal_payment
                if save_state['save']:
                    save = params['I'] - MP if save_state['next_savings'] is None else save_state['next_savings']
                else:
                    save = 0
                bt.make_month(earned=month_income, month_rent=month_rent, to_save=save)
            else:
                bt.make_month(earned=month_income, month_rent=month_rent, to_save=params['I'])

            mth += 1

        bt.spend_savings(repairing=repairing_cost)
        for _ in range(repairing_months):
            mth += 1
            bt.make_month(earned=month_income, month_rent=month_rent)

        for _ in range(1, 100):
            mth += 1
            if len(bt.credits) > 0:
                bt.make_month(earned=month_income)
                continue
            return mth, bt.savings, bt
        return None
