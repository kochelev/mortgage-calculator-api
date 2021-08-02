import math as mt
from copy import deepcopy
from scipy.optimize import linprog
from pulp import LpMinimize, LpProblem, LpVariable
from prettytable import PrettyTable
from credit import Credit
from errors import CreditError, SavingsError, ComputationError

# TODO Create a storage for coefficients
# TODO There should be a boolean attribute for the class "solved"
# TODO There should be an attribute of solution type: fail, success and precise, success and oversaved
# TODO Check input data, types and limits
# TODO Place matrix of rules inside __if_simplex_needed function
# TODO Place precision inside class as a tunable attribute

precision = 2


class SavingsSolver:

    def __init__(self, params, launch=False):

        self.params = deepcopy(params)

        if 'k_2' in params and 'm' in params:
            case_3d = True
        elif 'k_2' not in params and 'm' not in params:
            case_3d = False
        else:
            raise SavingsError('PARAMS', 'The "k_2" and "m" should simultaneously be or not be presented in "params"')

        self.params['case_3d'] = case_3d

        (C, S_i, S_t, R, IP_min, k_1, l) = self.__get_prms(['C', 'S_i', 'S_t', 'R', 'IP_min', 'k_1', 'l'])
        if case_3d:
            (k_2, m) = self.__get_prms(['k_2', 'm'])
            self.params['m_origin'] = m

        self.params['D_min'] = 0
        self.params['g'] = l if not case_3d else l + m
        self.params['Y'] = C - S_i + R
        self.params['t'] = self.__get_t()
        self.params['S_0_top'] = S_i - R - IP_min
        if S_i < IP_min + R:
            raise CreditError('IP', {'need': IP_min + R, 'have': S_i})

        self.coefficients = {'alpha': 1 + k_1}
        if case_3d:
            self.coefficients = {'beta': 1 + k_2}

        (t, n, g) = self.__get_prms(['t', 'n', 'g'])
        # TODO: put that check to the top
        if self.params['C'] <= self.params['S_i']:
            S_super = self.params['S_i'] - self.params['C'] + self.params['I'] * self.params['g']
            if S_super >= self.params['S_t']:
                raise SavingsError('NOMORTGAGE', {'need': self.params['S_t'], 'have': S_super})
    
        self.params['case'] = '0 <= g < t <= n' if g < t else \
                              '0 <= t <= g <= n' if g <= n and t >= 0 else \
                              '0 <= t <= n < g' if n < g and t >= 0 else \
                              't < 0 <= g <= n' if g <= n and t < 0 else \
                              't < 0 <= n < g' if n < g and t < 0 else \
                              'UNKNOWN CASE !!!!'

        self.logs = list()
        self.executors = dict(scipy=self.__with_scipy,
                              pulp=self.__with_pulp)
        self.results = None

        if launch:
            self.solution = self.find_best_solution()

    def __get_prms(self, p_list):

        return [self.params[x] for x in p_list]

    def __get_t(self):

        (I, C, S_i, R, k_1, l, n, case_3d) = \
            self.__get_prms(['I', 'C', 'S_i', 'R', 'k_1', 'l', 'n', 'case_3d'])

        D1 = C - S_i + R
        MP1 = k_1 * D1 / (1 - (1 / ((1 + k_1) ** n)))

        if MP1 > I:
            raise CreditError('MP1', {'need': MP1, 'have': I})

        t_1 = mt.log((I / (I - k_1 * D1)), (1 + k_1))

        if not case_3d or t_1 < l:
            return t_1

        (k_2,) = self.__get_prms(['k_2'])

        D2 = D1 * (1 + k_1) ** l - I * ((1 + k_1) ** l - 1) / k_1
        MP2 = k_2 * D2 / (1 - (1 / ((1 + k_2) ** (n - l))))

        if MP2 > I:
            raise CreditError('MP2', {'need': MP2, 'have': I})

        t_2 = mt.log((I / (I - k_2 * D2)), (1 + k_2))

        return l + t_2

    def find_best_solution(self, debug=False):

        self.logs = list()

        (t, g, l, n, I, Y, S_t, k_1, case_3d) = self.__get_prms(['t', 'g', 'l', 'n', 'I', 'Y', 'S_t', 'k_1', 'case_3d'])

        if case_3d:
            (m,) = self.__get_prms(['m'])

        if 0 <= t < g:
            t_cl = mt.floor(t)
            if not case_3d or t <= l:
                D_last = Credit.get_debt_after_period(
                    current_debt=Y,
                    interest_rate=k_1,
                    months_left=n,
                    month_payment=I,
                    months_passed=t_cl)
            else:
                (k_2,) = self.__get_prms(['k_2'])
                D_last = Credit.get_debt_after_period(
                    current_debt=Credit.get_debt_after_period(
                        current_debt=Y,
                        interest_rate=k_1,
                        months_left=n,
                        month_payment=I,
                        months_passed=l),
                    interest_rate=k_2,
                    months_left=n - l,
                    month_payment=I,
                    months_passed=t_cl - l)
            k = k_1 if t <= l else k_2
            S__t_g = (I - (D_last + D_last * k)) + I * (g - t_cl - 1)
            if S__t_g >= S_t:
                a_10 = S__t_g % I
                period = {'month': t_cl,
                          'init_save': a_10}
                if t_cl < g - 1:
                    period['next_savings'] = I
                result = {'success': True,
                          'method': 'save after mortgage',
                          'save_before': 0,
                          'saved': S__t_g,
                          'debt': 0,
                          'scheme': [period]}
                self.solution = result
                return result
            elif n <= g:
                self.solution = None
                return self.solution

        results = {'smp': None, 'bnd': None}

        for x in range(l):
            if case_3d:
                for y in range(m):
                    self.__iteration(results, (x, y), debug)
            else:
                self.__iteration(results, (x,), debug)

        result = results['smp'] if ((results['smp'] is not None and
                                     results['bnd'] is None) or
                                    (results['smp'] is not None and
                                     results['bnd'] is not None and
                                     results['smp']['debt'] < results['bnd']['debt'])) else results['bnd']

        self.solution = result
        if debug:
            self.results = results
        return self.solution

    def __iteration(self, results, V, debug=False):

        (C, S_i, S_t, S_0_top, t, I, R) = self.__get_prms(['C', 'S_i', 'S_t', 'S_0_top', 't', 'I', 'R'])

        if len(V) == 1:
            (Amp_1, Zmp_1) = self.__get_cfs(['Amp_1', 'Zmp_1'], x=V[0])
            S_0_min = max([0, S_i - C - R])
            S_0_max = min([S_0_top, (I - Zmp_1) / Amp_1])
            args = S_t, S_0_min, S_0_max
            steps = ['x', 'xp']
            fns = {'x': lambda: self.__get_bnd_sltn(*args, V[0]),
                   'xp': lambda: self.__get_bnd_sltn(*args, V[0] + 1)}
            mtx = {'x': [(1, 0), (1, 1), (1, 1), (1, 1)],
                   'xp': [(1, 1), (1, 1), (0, 1), (0, 0)]}
        else:
            (Amp_1, Zmp_1, Amp_2_c, Zmp_2_c) = self.__get_cfs(['Amp_1', 'Zmp_1', 'Amp_2_c', 'Zmp_2_c'], x=V[0], y=V[1])
            S_0_min = max([0, S_i - C - R])
            S_0_max = min([S_0_top, (I - Zmp_1) / Amp_1, (I - Zmp_2_c) / Amp_2_c])
            args = S_t, S_0_min, S_0_max
            steps = ['xy', 'xpyp', 'xyp', 'xpy']
            fns = {'xy': lambda: self.__get_bnd_sltn(*args, V[0], V[1]),
                   'xyp': lambda: self.__get_bnd_sltn(*args, V[0], V[1] + 1),
                   'xpy': lambda: self.__get_bnd_sltn(*args, V[0] + 1, V[1]),
                   'xpyp': lambda: self.__get_bnd_sltn(*args, V[0] + 1, V[1] + 1)}
            mtx = {'xy': [(1, 0), (1, 0), (1, 0), (1, 0), (1, 0)],
                   'xyp': [(1, 0), (1, 0), (1, 1), (1, 1), (1, 1)],
                   'xpy': [(1, 0), (1, 1), (1, 0), (1, 1), (1, 1)],
                   'xpyp': [(1, 1), (1, 1), (1, 1), (1, 1), (0, 1)]}

        res, fns_res = self.__if_simplex_needed(fns, steps, mtx, S_0_min)

        # Enable simplex for the first iteration
        if len(V) == 1 and V[0] == 0 or len(V) == 2 and V[0] == 0 and V[1] == 0:
            res = True

        if debug:
            if len(fns_res) < len(fns):
                fns_res.update({key: fns[key]() for key in fns.keys() if key not in fns_res.keys()})

        temp = {val['D']: key for key, val in fns_res.items() if val['success']}
        bnd_best = None
        if len(temp.keys()) > 0:
            bnd_best = fns_res[temp[min(temp.keys())]]
        if bnd_best is not None and (results['bnd'] is None or results['bnd']['debt'] >= bnd_best['D']):
            results['bnd'] = self.__format_sltn(V, bnd_best)

        log = [V, fns_res, res]

        if res or debug:
            try:
                smp = self.__compute_simplex(*V)
                if results['smp'] is None or results['smp']['debt'] >= smp['D']:
                    results['smp'] = self.__format_sltn(V, smp)
                log.append(smp)
            except ComputationError:
                log.append(None)
        else:
            log.append(None)

        log += [results['bnd'], results['smp']]
        self.logs.append(log)

    def __get_bnd_sltn(self, S_t, S_0_min, S_0_max, *xy):

        result = {
            'S_0_min': S_0_min,
            'S_0_max': S_0_max,
            'method': 'boundary',
        }

        S__S_0_min = self.__get_s(S_0_min, *xy)

        if S__S_0_min < S_t:
            S__S_0_max = self.__get_s(S_0_max, *xy)
            D = self.__get_d(S_0_max, *xy)
            if S__S_0_max < S_t:
                result.update({'success': False, 'S_0': S_0_max, 'S': S__S_0_max, 'D': D})
                return result
            else:
                S_0_opt = self.__get_s_0(*xy)
                D = self.__get_d(S_0_opt, *xy)
                S = self.__get_s(S_0_opt, *xy)
                result.update({'success': True, 'S_0': S_0_opt, 'S': S, 'D': D})
                return result
        else:
            D = self.__get_d(S_0_min, *xy)
            result.update({'success': True, 'S_0': S_0_min, 'S': S__S_0_min, 'D': D})
            return result

    def __get_cfs(self, c_list, x=None, y=None):

        (k_1, l, n, Y, I, case_3d) = self.__get_prms(['k_1', 'l', 'n', 'Y', 'I', 'case_3d'])

        alpha = 1 + k_1
        alpha__n = alpha ** n
        alphas__n__l = alpha__n - alpha ** l

        if case_3d:

            (k_2, m) = self.__get_prms(['k_2', 'm'])

            beta = 1 + k_2
            beta__n_l = beta ** (n - l)
            beta__m = beta ** m
            betas__n_l__m = beta__n_l - beta ** m

        fns = dict()
        fns['Amp_1'] = lambda: k_1 * alpha__n / (alpha__n - 1)
        fns['Zmp_1'] = lambda: Y * fns['Amp_1']()

        if x is not None:

            alpha__x = alpha ** x
            alpha__n_x = alpha ** (n - x)
            alpha__nx = alpha__n * alpha__x
            alphas__n__x = alpha__n - alpha__x
            alpha__n_x_1 = alpha ** (n - x - 1)
            alphas__n__x = alpha__n - alpha__x
            alpha__dx = (1 - 1 / alpha__x) / k_1
            alpha_xs = alpha__x * (1 + alpha__dx)

            fns['Amp_1s'] = lambda: k_1 * alpha__n / (alpha__n_x - 1)
            fns['Zmp_1s'] = lambda: (Y - I * alpha__dx) * fns['Amp_1s']()

            fns['Amp_1s_c'] = lambda: k_1 * alpha__nx / alphas__n__x
            fns['Zmp_1s_c'] = lambda: ((Y * k_1 - I) * alpha__nx + I * alpha__n) / alphas__n__x

            fns['Amp_1sp'] = lambda: k_1 * alpha__n / (alpha__n_x_1 - 1)
            fns['Bmp_1sp'] = lambda: fns['Amp_1sp']() / (alpha__x * alpha)
            fns['Zmp_1sp'] = lambda: Y * fns['Amp_1sp']() - I * alpha_xs * fns['Bmp_1sp']()

            fns['Ad_2'] = lambda: alphas__n__l / (alpha__n_x_1 - 1)
            fns['Bd_2'] = lambda: fns['Ad_2']() / (alpha__x * alpha)
            fns['Zd_2'] = lambda: Y * fns['Ad_2']() - I * alpha_xs * fns['Bd_2']()

            fns['Ad_2_c'] = lambda: alpha__x * alphas__n__l / alphas__n__x
            fns['Zd_2_c'] = lambda: Y * alpha__x * alphas__n__l / alphas__n__x + (I / k_1) * (1 - alpha__x) * alphas__n__l / alphas__n__x

            fns['As_2'] = lambda: 1 - (l - x - 1) * fns['Amp_1sp']()
            fns['Bs_2'] = lambda: 1 - (l - x - 1) * fns['Bmp_1sp']()
            fns['Zs_2'] = lambda: (I - fns['Zmp_1sp']()) * (l - x - 1)

            fns['Amp_2'] = lambda: k_2 * alphas__n__l * beta__n_l / ((alpha__n_x_1 - 1) * (beta__n_l - 1))
            fns['Bmp_2'] = lambda: fns['Amp_2']() / (alpha__x * alpha)
            fns['Zmp_2'] = lambda: Y * fns['Amp_2']() - I * alpha_xs * fns['Bmp_2']()

        if x is not None and y is not None:

            beta__y = beta ** y
            beta__n_l = beta ** (n - l)
            beta__n_l_y = beta ** (n - l - y)
            beta__n_l_y_1 = beta ** (n - l - y - 1)
            beta__dy = (1 - 1 / beta__y) / k_2
            beta_ys = beta__y * (1 + beta__dy)

            Kef = k_2 * beta__n_l / (beta__n_l - 1)
            fns['Amp_2_c'] = lambda: fns['Ad_2_c']() * Kef
            fns['Zmp_2_c'] = lambda: fns['Zd_2_c']() * Kef

            fns['Amp_2s'] = lambda: k_2 * alphas__n__l * beta__n_l / ((alpha__n_x_1 - 1) * (beta__n_l_y - 1))
            fns['Bmp_2s'] = lambda: fns['Amp_2s']() / (alpha__x * alpha)
            fns['Zmp_2s'] = lambda: Y * fns['Amp_2s']() - I * alpha_xs * fns['Bmp_2s']() \
                - I * beta__dy * k_2 * beta__n_l / (beta__n_l_y - 1)

            # TODO: refactor "Amp_2s_c" and "Zmp_2s_c" coefficients

            fns['Amp_2s_c'] = lambda: alpha__x * k_2 * beta__n_l * alphas__n__l / ((beta__n_l_y - 1) * alphas__n__x)
            fns['Zmp_2s_c'] = lambda: (Y * alpha__x + I * (1 - alpha__x) / k_1) * k_2 * beta__n_l * alphas__n__l / (
                        (beta__n_l_y - 1) * alphas__n__x) + I * (beta__n_l_y - beta__n_l) / (beta__n_l_y - 1)

            fns['Amp_2sp'] = lambda: k_2 * alphas__n__l * beta__n_l / ((alpha__n_x_1 - 1) * (beta__n_l_y_1 - 1))
            fns['Bmp_2sp'] = lambda: fns['Amp_2sp']() / (alpha__x * alpha)
            fns['Cmp_2sp'] = lambda: k_2 * beta__n_l_y_1 / (beta__n_l_y_1 - 1)

            # TODO: refactor "Zmp_2sp" coefficient

            # fns['Zmp_2sp'] = lambda: Y * fns['Amp_2sp']() \
            #     - I * fns['Bmp_2sp']() * (alpha__x * alpha__dx + 1) - I * beta_ys * fns['Cmp_2sp']()

            AlphasL = alpha ** n - alpha ** l
            AlphasY = alpha ** n - alpha ** (x + 1)
            BetasZ = beta ** (n - l) - beta ** (y + 1)
            BetasM = beta ** (n - l) - beta ** m

            BetaZ = beta ** (n - l - y) - 1
            BetaZ1 = beta ** (n - l - y - 1) - 1
            BetaZ1_AlphasY = BetaZ1 * AlphasY

            fns['Zmp_2sp'] = lambda: Y * k_2 * beta**(n-l) * alpha**(x+1) * AlphasL / BetaZ1_AlphasY \
                + I * (beta**(n-l-y) - k_2 * beta**(n-l-y-1) - beta**(n-l)) / BetaZ1 \
                - I * (k_2 / k_1) * beta**(n-l) * alpha * (alpha**x - 1) * AlphasL / BetaZ1_AlphasY \
                - I * k_2 * beta**(n-l) * AlphasL / BetaZ1_AlphasY
            fns['Ad_3'] = lambda: alphas__n__l * betas__n_l__m / ((alpha__n_x_1 - 1) * (beta__n_l_y_1 - 1))
            fns['Bd_3'] = lambda: fns['Ad_3']() / (alpha__x * alpha)
            fns['Cd_3'] = lambda: betas__n_l__m / ((beta__n_l_y_1 - 1) * (beta__y * beta))
            fns['Zd_3'] = lambda: Y * fns['Ad_3']() - I * alpha_xs * fns['Bd_3']() - I * beta_ys * fns['Cd_3']()

            fns['Ad_3_c'] = lambda: k_2*beta__y*k_1*alpha__x*alphas__n__l* (beta__n_l - beta__m) / (k_1 * k_2 * alphas__n__x * (beta__n_l - beta__y))

            # TODO: refactor "Zd_3_c" coefficient

            fns['Zd_3_c'] = lambda: k_2 * beta__y * k_1 * alpha__x * Y * alphas__n__l * (beta__n_l - beta__m) / (k_1 * k_2 * alphas__n__x * (beta__n_l - beta__y)) \
                - k_2 * beta__y * I * (alpha__x - 1) * alphas__n__l * (beta__n_l - beta__m) / (k_1 * k_2 * alphas__n__x * (beta__n_l - beta__y)) \
                - I * k_1 * alphas__n__x * (beta__y - 1) * (beta__n_l - beta__m) / (k_1 * k_2 * alphas__n__x * (beta__n_l - beta__y))

            fns['As_3'] = lambda: 1 - (l - x - 1) * fns['Amp_1sp']() - (m - y - 1) * fns['Amp_2sp']()
            fns['Bs_3'] = lambda: 1 - (l - x - 1) * fns['Bmp_1sp']() - (m - y - 1) * fns['Bmp_2sp']()
            fns['Cs_3'] = lambda: 1 - (m - y - 1) * fns['Cmp_2sp']()
            fns['Zs_3'] = lambda: (I - fns['Zmp_1sp']()) * (l - x - 1) + (I - fns['Zmp_2sp']()) * (m - y - 1)

        return [fns[el]() for el in c_list]

    def __get_d(self, S_0, x, y=None):

        if y is not None:
            (Ad_3_c, Zd_3_c) = self.__get_cfs(['Ad_3_c', 'Zd_3_c'], x=x, y=y)
            return Ad_3_c * S_0 + Zd_3_c

        (Ad_2_c, Zd_2_c) = self.__get_cfs(['Ad_2_c', 'Zd_2_c'], x=x)
        return Ad_2_c * S_0 + Zd_2_c

    def __get_s(self, S_0, x, y=None):

        (l, n, I) = self.__get_prms(['l', 'n', 'I'])
        (Amp_1s_c, Zmp_1s_c) = self.__get_cfs(['Amp_1s_c', 'Zmp_1s_c'], x=x)

        if y is not None:
            (k_2, m) = self.__get_prms(['k_2', 'm'])
            (Amp_2s_c, Zmp_2s_c) = self.__get_cfs(['Amp_2s_c', 'Zmp_2s_c'], x=x, y=y)
            return (1 - Amp_1s_c * (l - x) - Amp_2s_c * (m - y)) * S_0 \
                + I * (m + l - x - y) - Zmp_1s_c * (l - x) - Zmp_2s_c * (m - y)

        return (1 - Amp_1s_c * (l - x)) * S_0 + (I - Zmp_1s_c) * (l - x)

    def __get_s_0(self, x, y=None):

        (l, I, S_t) = self.__get_prms(['l', 'I', 'S_t'])
        (Amp_1s_c, Zmp_1s_c) = self.__get_cfs(['Amp_1s_c', 'Zmp_1s_c'], x=x)

        if y is not None:

            (m,) = self.__get_prms(['m'])
            (Amp_2s_c, Zmp_2s_c) = self.__get_cfs(['Amp_2s_c', 'Zmp_2s_c'], x=x, y=y)
            return (S_t - I * (m + l - x - y) + Zmp_1s_c * (l - x) + Zmp_2s_c * (m - y)) /\
                (1 - Amp_1s_c * (l - x) - Amp_2s_c * (m - y))

        return (S_t - (I - Zmp_1s_c) * (l - x)) / (1 - Amp_1s_c * (l - x))

    def __with_scipy(self, obj, lhs_ineq, rhs_ineq, bnd, d_cfs, s_cfs):
        try:
            opt = linprog(c=obj, A_ub=lhs_ineq, b_ub=rhs_ineq, bounds=bnd, method='revised simplex')
        except ValueError:
            raise ComputationError(2, self.params['S_t'])

        result = {
            'success': True,
            'D': sum([d_cfs[i] * opt.x[i] for i in range(len(obj))]) + d_cfs[len(d_cfs) - 1],
            'S': sum([s_cfs[i] * opt.x[i] for i in range(len(s_cfs) - 1)]) + s_cfs[len(s_cfs) - 1],
            'S_0': opt.x[0],
            'S_0_min': bnd[0][0],
            'S_0_max': bnd[0][1],
            'V': opt.x[1:],
            'method': 'simplex-scipy',
        }

        # TODO: delete a_10 and a_20 names, use V instead
        result.update({'a_%d0' % i: val for i, val in enumerate(opt.x) if i != 0})
        return result

    def __with_pulp(self, obj, lhs_ineq, rhs_ineq, bnd, d_cfs, s_cfs):

        model = LpProblem(name='simplex-x-y', sense=LpMinimize)
        X = [LpVariable(name='x_%d' % i, lowBound=x[0], upBound=x[1]) for i, x in enumerate(bnd)]

        model += sum([obj[i] * x for i, x in enumerate(X)]) + d_cfs[len(d_cfs) - 1]

        for i, eq in enumerate(lhs_ineq):
            model += (sum([eq[e] * x for e, x in enumerate(X)]) <= rhs_ineq[i])

        status = model.solve()

        if status != 1:
            raise ComputationError(2, self.params['S_t'])

        result = {
            'success': True if status == 1 else False,
            'D': sum([d_cfs[i] * model.variables()[i].value()
                      for i in range(len(obj))]) + d_cfs[len(d_cfs) - 1],
            'S': sum([s_cfs[i] * model.variables()[i].value()
                      for i in range(len(s_cfs) - 1)]) + s_cfs[len(s_cfs) - 1],
            'S_0': model.variables()[0].value(),
            'S_0_min': bnd[0][0],
            'S_0_max': bnd[0][1],
            'V': [v.value() for v in model.variables()[1:]],
            'method': 'simplex-pulp',
        }

        # TODO: delete a_10 and a_20 names, use V instead

        result.update({'a_%d0' % i: val.value() for i, val in enumerate(model.variables()) if i != 0})
        return result

    def __compute_simplex(self, x, y=None, module='pulp'):

        (I, S_t, S_0_top) = self.__get_prms(['I', 'S_t', 'S_0_top'])

        if y is None:
            (Amp_1, Zmp_1, Amp_1s, Zmp_1s, Amp_1sp, Bmp_1sp, Zmp_1sp,
             Ad_2, Bd_2, Zd_2, As_2, Bs_2, Zs_2) = self.__get_cfs((
                'Amp_1', 'Zmp_1', 'Amp_1s', 'Zmp_1s', 'Amp_1sp', 'Bmp_1sp', 'Zmp_1sp',
                'Ad_2', 'Bd_2', 'Zd_2', 'As_2', 'Bs_2', 'Zs_2'), x=x)
            d_cfs = [Ad_2, Bd_2, Zd_2]
            s_cfs = [As_2, Bs_2, Zs_2]
        else:
            (Amp_1, Zmp_1, Amp_1s, Zmp_1s, Amp_1sp, Bmp_1sp, Zmp_1sp,
             Amp_2, Bmp_2, Zmp_2, Amp_2s, Bmp_2s, Zmp_2s, Amp_2sp, Bmp_2sp, Cmp_2sp, Zmp_2sp,
             Ad_3, Bd_3, Cd_3, Zd_3, As_3, Bs_3, Cs_3, Zs_3) = self.__get_cfs((
                'Amp_1', 'Zmp_1', 'Amp_1s', 'Zmp_1s', 'Amp_1sp', 'Bmp_1sp', 'Zmp_1sp',
                'Amp_2', 'Bmp_2', 'Zmp_2', 'Amp_2s', 'Bmp_2s', 'Zmp_2s', 'Amp_2sp', 'Bmp_2sp', 'Cmp_2sp', 'Zmp_2sp',
                'Ad_3', 'Bd_3', 'Cd_3', 'Zd_3', 'As_3', 'Bs_3', 'Cs_3', 'Zs_3'), x=x, y=y)
            d_cfs = [Ad_3, Bd_3, Cd_3, Zd_3]
            s_cfs = [As_3, Bs_3, Cs_3, Zs_3]

        S_0_max = min([(I - Zmp_1) / Amp_1, S_0_top])
        S_0_min = max([0, -Zmp_1s / Amp_1s])

        if S_0_max < S_0_min:
            raise ComputationError(1, S_0_min, S_0_max)

        obj = d_cfs[:-1]

        if y is None:
            bnd = [(S_0_min, S_0_max), (0, I)]

            lhs_ineq = [[    -As_2,    -Bs_2],
                        [   Amp_1s,        1],
                        [  Amp_1sp,  Bmp_1sp],
                        [ -Amp_1sp, -Bmp_1sp]]

            rhs_ineq = [Zs_2 - S_t,
                        I - Zmp_1s,
                        I - Zmp_1sp,
                        Zmp_1sp]
        else:
            bnd = [(S_0_min, S_0_max), (0, I), (0, I)]

            lhs_ineq = [[    -As_3,    -Bs_3,    -Cs_3],
                        [   Amp_1s,        1,        0],
                        [  Amp_1sp,  Bmp_1sp,        0],
                        [ -Amp_1sp, -Bmp_1sp,        0],
                        [    Amp_2,    Bmp_2,        0],
                        [   -Amp_2,   -Bmp_2,        0],
                        [   Amp_2s,   Bmp_2s,        0],
                        [  -Amp_2s,  -Bmp_2s,        0],
                        [  Amp_2sp,  Bmp_2sp,  Cmp_2sp],
                        [ -Amp_2sp, -Bmp_2sp, -Cmp_2sp],
                        [   Amp_2s,   Bmp_2s,        1]]

            rhs_ineq = [Zs_3 - S_t,
                        I - Zmp_1s,
                        I - Zmp_1sp,
                        Zmp_1sp,
                        I - Zmp_2,
                        Zmp_2,
                        I - Zmp_2s,
                        Zmp_2s,
                        I - Zmp_2sp,
                        Zmp_2sp,
                        I - Zmp_2s]

        return self.executors[module](obj, lhs_ineq, rhs_ineq, bnd, d_cfs, s_cfs)

    @staticmethod
    def __format_sltn(V, sltn):
        result = {
            'success': sltn['success'],
            'scheme': [],
            'save_before': sltn['S_0'],
            'saved': sltn['S'],
            'debt': sltn['D']
        }
        for i, v in enumerate(V):
            period = {'month': v}
            key = 'a_%d0' % (i + 1)
            if key in sltn:
                period['init_save'] = sltn[key]
            result['scheme'].append(period)
        return result

    @staticmethod
    def __if_simplex_needed(fns, steps, m, S_0_min):
        f = {}
        for k in steps:
            f[k] = fns[k]()
            nx = [i for i, val in enumerate(m[k]) if (f[k]['success'],
                                                      0 if round(f[k]['S_0'], precision) == round(S_0_min, precision)
                                                      else 1) == val]
            if len(nx) == 0:
                return False, f
            if len(nx) == len(m[k]):
                continue
            m = {k: [m[k][i] for i, val in enumerate(nx)] for k in m}
        return True, f

    @staticmethod
    def execute(params, solution):

        g = params['l'] if not 'm' in params else params['l'] + params['m']
        save_state = {
            'save': False,
            'next_savigns': None,
        }
        S = solution['save_before']
        D = S + params['C'] - params['S_i'] + params['R']
        for i in range(g):
            k = params['k_1'] if i < params['l'] else params['k_2']
            if i == solution['scheme'][0]['month'] or (
                    len(solution['scheme']) > 1 and i == solution['scheme'][1]['month'] + params['l']):
                period = solution['scheme'][0] if i == solution['scheme'][0]['month'] else solution['scheme'][1]
                if 'init_save' not in period:
                    MP = Credit.get_minimal_payment(
                        current_debt=D,
                        interest_rate=k,
                        months_left=params['n'] - i)
                    period['init_save'] = params['I'] - MP
                S += period['init_save']
                if round(D, 2) != 0:
                    D = Credit.get_debt_after_period(
                        current_debt=D,
                        interest_rate=k,
                        months_left=params['n'] - i,
                        month_payment=params['I'] - period['init_save'],
                        months_passed=1)
                else:
                    S += params['I'] - period['init_save']

                if i != params['l'] and (('m' not in params) or ('m' in params and i != params['m'] + params['l'])):
                    save_state = {
                        'save': True,
                        'next_savings': period['next_savings'] if 'next_savings' in period else None
                    }

                continue

            if round(D, 2) != 0:
                if i == params['l'] or ('m' in params and i == params['m'] + params['l']):
                    save_state = {
                        'save': False,
                        'next_savings': None,
                    }

                MP = Credit.get_minimal_payment(
                    current_debt=D,
                    interest_rate=k,
                    months_left=params['n'] - i)

                if save_state['save']:
                    save = params['I'] - MP if save_state['next_savings'] is None else save_state['next_savings']
                    S += save

                pay = params['I'] if not save_state['save'] else params['I'] - save_state['next_savings'] if save_state[
                                                                                                                 'next_savings'] is not None else MP

                D = Credit.get_debt_after_period(
                    current_debt=D,
                    interest_rate=k,
                    months_left=params['n'] - i,
                    month_payment=pay,
                    months_passed=1)

            else:
                S += params['I']

        return {'D': D if round(D, 3) != 0 else 0, 'S': S}

    def __str__(self):

        (case_3d, case, S_i, C, IP_min, R,
         k_1, l, g, n, t, I, S_t, Y) = self.__get_prms(['case_3d', 'case', 'S_i', 'C', 'IP_min', 'R',
                                                        'k_1', 'l', 'g', 'n', 't', 'I', 'S_t', 'Y'])

        params_data = \
            [['I',          str(I),         'Month income'],
             ['S_i',        str(S_i),       'Initial savings'],
             ['C',          str(C),         'Realty cost'],
             ['IP_min',     str(IP_min),    'Mortgage initial payment'],
             ['R',          str(R),         'Mortgage expenses (insurance)'],
             ['Y',          str(Y),         'Y = C - S_i + R'],
             ['S_t',        str(S_t),       'Target savings'],
             ['k_1',        str(k_1),       '1st interest rate'],
             ['l',          str(l),         '1st saving period']]

        if case_3d:
            (k_2, m) = self.__get_prms(['k_2', 'm'])
            params_data +=\
                [['k_2',    str(k_2),       '2nd interest rate'],
                 ['m',      str(m),         '2nd saving period']]

        params_data += \
            [['g',          str(g),         'Months to get keys'],
             ['n',          str(n),         'Mortgage duration (months)'],
             ['t',          str(t),         'Expected mortgage duration'],
             ['case',       str(case),      'Problem type']]

        params_table = PrettyTable()
        params_table.field_names = ['Attribute', 'Value', 'Description']
        for row in params_data:
            params_table.add_row(row)

        print('Params:')
        print(params_table)

        if not hasattr(self, 'solution'):
            return 'Problem is not solved'

        if self.solution is None or not self.solution['success']:
            return 'Problem solved unsuccessfully:('

        print('Problem solved successfully:)')
        print(self.solution)

        if self.logs is None or len(self.logs) == 0:
            return 'No logs because problem solved easily'

        logs_table = PrettyTable()
        if case_3d:
            logs_table.field_names = ['x,y', 'xy boundary', 'xyp boundary', 'xpy boundary', 'xpyp boundary', 'Use?', 'Simplex (control)', 'Best B', 'Best S']
        else:
            logs_table.field_names = ['x', 'x boundary', 'x+1 boundary', 'Use?', 'Simplex (control)', 'Best B', 'Best S']
        for row in self.logs:
            if case_3d:
                logs_table.add_row([row[0],
                                    (row[1]['xy']['success'],
                                     round(row[1]['xy']['S_0']),
                                     round(row[1]['xy']['S']),
                                     round(row[1]['xy']['D'])) if 'xy' in row[1] else '—',
                                    (row[1]['xyp']['success'],
                                     round(row[1]['xyp']['S_0']),
                                     round(row[1]['xyp']['S']),
                                     round(row[1]['xyp']['D'])) if 'xyp' in row[1] else '—',
                                    (row[1]['xpy']['success'],
                                     round(row[1]['xpy']['S_0']),
                                     round(row[1]['xpy']['S']),
                                     round(row[1]['xpy']['D'])) if 'xpy' in row[1] else '—',
                                    (row[1]['xpyp']['success'],
                                     round(row[1]['xpyp']['S_0']),
                                     round(row[1]['xpyp']['S']),
                                     round(row[1]['xpyp']['D'])) if 'xpyp' in row[1] else '—',
                                    row[2],
                                    (row[3]['success'],
                                     round(row[3]['S_0']),
                                     round(row[3]['a_10']),
                                     round(row[3]['a_20']),
                                     round(row[3]['S']),
                                     round(row[3]['D'])) if row[3] is not None else '—',
                                    (round(row[4]['save_before']),
                                     round(row[4]['saved']),
                                     round(row[4]['debt'])) if row[4] is not None else '—',
                                    (round(row[5]['save_before']),
                                     round(row[5]['scheme'][0]['init_save']),
                                     round(row[5]['scheme'][1]['init_save']),
                                     round(row[5]['saved']),
                                     round(row[5]['debt'])) if row[5] is not None else '—'])
            else:
                logs_table.add_row([row[0][0],
                                    (row[1]['x']['success'],
                                     round(row[1]['x']['S_0']),
                                     round(row[1]['x']['S']),
                                     round(row[1]['x']['D'])) if 'x' in row[1] else '—',
                                    (row[1]['xp']['success'],
                                     round(row[1]['xp']['S_0']),
                                     round(row[1]['xp']['S']),
                                     round(row[1]['xp']['D'])) if 'xp' in row[1] else '—',
                                    row[2],
                                    (row[3]['success'],
                                     round(row[3]['S_0']),
                                     round(row[3]['a_10']),
                                     round(row[3]['S']),
                                     round(row[3]['D'])) if row[3] is not None else '—',
                                    (round(row[4]['save_before']),
                                     round(row[4]['saved']),
                                     round(row[4]['debt'])) if row[4] is not None else '—',
                                    (round(row[5]['save_before']),
                                     round(row[5]['scheme'][0]['init_save']),
                                     round(row[5]['saved']),
                                     round(row[5]['debt'])) if row[5] is not None else '—'])

        print('Logs:')
        print(logs_table)

        return 'Report: %d iterations and %d with simplex method' % (len(self.logs),
                                                                     len([x for x in self.logs if x[2]]))
