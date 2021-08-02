import unittest
from savings import SavingsSolver, SavingsError, ComputationError, precision
from errors import CreditError, SavingsError, ComputationError

# TODO: add tests for execute function with EXCEPTIONS
# TODO: add tests for unfeasible instance creation
# TODO: add tests for 'Amp_1', 'Zmp_1', 'Amp_2_c', 'Zmp_2_c'
# TODO: add tests for "execute" function with no "init_save", should work well.

# timing: g < t < n | t < g < n | t < n < g
# dimensions: a_10 | a_10 and a_20
# result: success | fail | oversave

problem_set = {
    't_n_g__1_fail': {
        'params': {
            'I': 100000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'l': 85,
            'n': 80,
        },
        'solution': None,
    },
    't_n_g__2_fail': {
        'params': {
            'I': 100000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'k_2': 0.0095,
            'l': 40,
            'm': 45,
            'n': 80,
        },
        'solution': None,
    },
    't_n_g__1_oversave': {
        'params': {
            'I': 100000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 5000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'l': 100,
            'n': 50,
        },
        'solution': {
            'success': True,
            'method': 'save after mortgage',
            'save_before': 0,
            'scheme': [{'month': 47,
                        'init_save': 84596.5909830518,
                        'next_savings': 100000}],
            'saved': 5284596.590983052,
            'debt': 0,

            # 'success': True,
            # 'method': 'easy',
            # 'save_before': 0,
            # 'scheme': [{'month': 47,
            #             'init_save': 84638.74085776694,
            #             'next_savings': 100000}],
            # 'saved': 5284638.740857767,
            # 'debt': 0,
        }
    },
    't_n_g__2_oversave': {
        'params': {
            'I': 100000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'k_2': 0.0122,
            'l': 50,
            'm': 120,
            'n': 100,
        },
        'solution': {
            'success': True,
            'method': 'easy',
            'save_before': 0,
            'scheme': [{'month': 79,
                        'init_save': 30023.596690254286,  # 30151.18407430686,
                        'next_savings': 100000}],
            'saved': 9030023.596690254,  # 9030151.184074307,
            'debt': 0,
        }
    },
    'g_t_n__1_success': {
        'params': {
            'I': 100000,
            'S_i': 1000000,
            'S_t': 400000,
            'C': 5000000,
            'R': 60000,
            'IP_min': 700000,
            'k_1': 10/1200,
            'n': 240,
            'l': 24,
        },
        'solution': {
            'success': True,
            'method': 'simplex',
            'save_before': 0.0,
            'scheme': [{'month': 18,
                        'init_save': 35865.509}],
            'saved': 399999.9998342397,
            'debt': 2717734.971237984,
        }
    },
    'g_t_n__1_success__S_0': {
        'params': {
            'I': 100000,
            'S_i': 1000000,
            'S_t': 1600000,  # Try cases 1500000, 1550000, 1500000
            'C': 5000000,
            'R': 60000,
            'IP_min': 700000,
            'k_1': 10/1200,
            'n': 240,
            'l': 24,
        },
        'solution': {
            'success': True,
            'method': 'boundary',
            'save_before': 182610.67,
            'scheme': [{'month': 0,
                        'init_save': 59057.889}],
            'saved': 1599999.9994578417,
            'debt': 4094851.162640979,
        }
    },
    'g_t_n__2_success': {
        'params': {
            'I': 150000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 5000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'k_2': 0.0122,
            'l': 12,
            'm': 12,
            'n': 240,
        },
        'solution': {
            'success': True,
            'method': 'simplex',
            'save_before': 0.0,
            'scheme': [{'month': 11,
                        'init_save': 0.0},
                       {'month': 3,
                        'init_save': 13042.368}],
            'saved': 999999.9999144623,
            'debt': 2023777.7860597589,
        },
    },
    'g_t_n__2_success__P_1': {
        'params': {
            'I': 450175,
            'S_i': 42687639,
            'S_t': 492707,
            'C': 66835858,
            'R': 95295,
            'IP_min': 668358,
            'k_1': 0.0065,
            'k_2': 0.0122,
            'l': 8,
            'm': 4,
            'n': 143,
        },
        'solution': {
            'success': True,
            'method': 'simplex',
            'save_before': 0.0,
            'scheme': [{'month': 7,
                        'init_save': 16795.077},
                       {'month': 0,
                        'init_save': 118977.98}],
            'saved': 492706.99923764257,
            'debt': 21603121.159358896,
        }
    },
    'g_t_n__1_fail': {
        'params': {
            'I': 100000,
            'S_i': 1000000,
            'S_t': 1650000,
            'C': 5000000,
            'R': 60000,
            'IP_min': 700000,
            'k_1': 10/1200,
            'n': 240,
            'l': 24,
        },
        'solution': None,
    },
    'g_t_n__2_fail': {
        'params': {
            'I': 120000,
            'S_i': 1000000,
            'S_t': 1600000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'k_2': 0.0128,
            'l': 12,
            'm': 12,
            'n': 120,
        },
        'solution': None,
    },
    't_g_n__1_success': {
        'params': {
            'I': 120000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'l': 65,
            'n': 120,
        },
        'solution': {
            'success': True,
            'method': 'simplex',
            'save_before': 0.0,
            'scheme': [{'month': 55,
                        'init_save': 32747.304}],
            'saved': 999999.9997964955,
            'debt': 577743.582070857,
        }
    },
    't_g_n__2_success': {
        'params': {
            'I': 120000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'k_2': 0.0128,
            'l': 45,
            'm': 20,
            'n': 80,
        },
        'solution': {
            'success': True,
            'save_before': 0.0,
            'scheme': [{'month': 44,
                        'init_save': 0.0},
                       {'month': 4,
                        'init_save': 50231.745}],
            'saved': 999999.9998323427,
            'debt': 769136.2574491366,
        }
    },
    't_g_n__1_fail': {
        'params': {
            'I': 120000,
            'S_i': 1000000,
            'S_t': 5000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'l': 70,
            'n': 120,
        },
        'solution': None,
    },
    't_g_n__2_fail': {
        'params': {
            'I': 120000,
            'S_i': 1000000,
            'S_t': 4000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'k_2': 0.0128,
            'l': 40,
            'm': 40,
            'n': 120,
        },
        'solution': None,
    },
    't_g_n__1_oversave': {
        'params': {
            'I': 120000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'l': 70,
            'n': 120,
        },
        'solution': {
            'success': True,
            'method': 'easy',
            'save_before': 0,
            'scheme': [{'month': 61,
                        'init_save': 85728.76903555461,  # 85808.0096868577,
                        'next_savings': 120000}],
            'saved': 1045728.7690355546,  # 1045808.0096868577,
            'debt': 0,
        }
    },
    't_g_n__2_oversave': {
        'params': {
            'I': 120000,
            'S_i': 1000000,
            'S_t': 1000000,
            'C': 7000000,
            'R': 50000,
            'IP_min': 700000,
            'k_1': 0.0065,
            'k_2': 0.0128,
            'l': 50,
            'm': 50,
            'n': 120,
        },
        'solution': {
            'success': True,
            'method': 'easy',
            'save_before': 0,
            'scheme': [{'month': 61,
                        'init_save': 29557.013311778195,  # 29698.985059553757,
                        'next_savings': 120000}],
            'saved': 4589557.013311778,  # 4589698.985059554,
            'debt': 0,
        }
    },
    't_0__1_success': {
        'params': {
            'I': 122657,
            'S_i': 3836725,
            'S_t': 2881957,
            'C': 2237880,
            'R': 897524,
            'IP_min': 1000000,
            'k_1': 0.0078,
            'l': 10,
            'n': 1034,
        },
        'solution': {
            'success': True,
            'scheme': [{'month': 0,
                        'init_save': 114582.89}],
            'save_before': 1736128.1,
            'saved': 2881956.9669827316,
            'debt': 1034779.9826501682
        }
    },
    't_0__2_success': {
        'params': {
            'I': 93703,
            'S_i': 3576227,
            'S_t': 1653750,
            'C': 5210442,
            'R': 35836,
            'IP_min': 729461,
            'k_1': 0.0116,
            'k_2': 0.022,
            'l': 6,
            'm': 8,
            'n': 563,
        },
        'solution': {
            'success': True,
            'scheme': [{'month': 0},
                       {'month': 0}],
            'save_before': 997223.6469131332,
            'saved': 1653750.0,
            'debt': 2666982.168551267
        }
    },
    't_0__1_fail': {
        'params': {
            'I': 22657,
            'S_i': 3836725,
            'S_t': 2881957,
            'C': 2237880,
            'R': 897524,
            'IP_min': 1000000,
            'k_1': 0.0078,
            'l': 8,
            'n': 1034,
        },
        'solution': None,
    },
    't_0__2_fail': {
        'params': {
            'I': 26985,
            'S_i': 6034728,
            'S_t': 9448194,
            'C': 3312118,
            'R': 212380,
            'IP_min': 1887907,
            'k_1': 0.0421,
            'k_2': 0.0542,
            'l': 7,
            'm': 8,
            'n': 1020,
        },
        'solution': None
    }
}

problem_x_simplex = {
    'params': {
        'C': 5000000,
        'S_i': 1000000,
        'R': 60000,
        'k_1': 10/1200,
        'n': 240,
        'l': 24,
        'I': 100000,
        'S_t': 400000,
        'IP_min': 700000,
    },
    'classification': {
        'timing': 'g < t < n',  # g < t < n | t < g < n | t < n < g
        'dimensions': 1,  # a_10 | a_10 and a_20
        'result': 'success',  # success | fail | oversave
        'method': 'simplex-pulp',  # none | easy | boundary | simplex-pulp | simplex-scipy
    },
    'solution': {
        'success': True,
        'save_before': 0.0,
        'saved': 399999.9998342397,
        'debt': 2717734.971237984,
        'scheme': [
            {
                'month': 18,
                'init_save': 35865.509,
            }
        ],
    },
    # 'coefficients': {
    #     'None': {
    #         'Amp_1': 0.010760523598313223,
    #         'Zmp_1': 260872.904503037,
    #     },
    #     7: {
    #         'Amp_1s': 0.011612946719394817,
    #         'Zmp_1s': 245876.84212777286,
    #         'Amp_1s_c': 0.011612946719394817,
    #         'Zmp_1s_c': 245876.842127773,
    #         'Amp_1sp': 0.011742422911231712,
    #         'Bmp_1sp': 0.011149296984258171,
    #         'Zmp_1sp': 243599.06129231837,
    #         'Ad_2': 1.053198504606253,
    #         'Bd_2': 1.0,
    #         'Zd_2': 21848827.027951527,
    #         # 'As_2': 1.053198504606253,
    #         'As_2': 1.0,
    #         'Bs_2': 1.0,
    #         # 'Zs_2': 21848827.027951527,
    #         'Zs_2': 0.0,
    #         'Ad_2_c': 1.0415855578868582,
    #         'Zd_2_c': 22053125.18582376,
    #         'Amp_2': 0.01595272266876192,
    #         'Bmp_2': 0.01514692871191075,
    #         'Zmp_2': 330942.6254312506,
    #     },
    #     (7, 0): {
    #         'Amp_2s': 0.01595272266876192,
    #         'Bmp_2s': 0.01514692871191075,
    #         'Zmp_2s': 330942.62543125066,
    #         'Amp_2s_c': 0.015776822192668037,
    #         'Zmp_2s_c': 334037.115064516,
    #         'Amp_2sp': 0.01619507160683044,
    #         'Bmp_2sp': 0.015377036271889785,
    #         'Cmp_2sp': 0.015191697561637806,
    #         'Zmp_2sp': 329131.28325724637,
    #         'Ad_3': 1.0563624482332956,
    #         'Bd_3': 1.0030041284840463,
    #         'Cd_3': 0.9909149659000654,
    #         'Zd_3': 21468378.56679513,
    #         'As_3': 0.9514147851795087,
    #         'Bs_3': 0.9538688911843306,
    #         'Cs_3': 0.9544249073150866,
    #         'Zs_3': 363131.1502282609,
    #         'Ad_3_c': 1.0290811255048182,
    #         'Zd_3_c': 21788373.23087322,
    #     }
    # }
}
problem_xy_simplex = {
    'params': {
        'C': 66835858,
        'S_i': 42687639,
        'R': 95295,
        'k_1': 0.0065,
        'k_2': 0.0122,
        'l': 8,
        'm': 4,
        'n': 143,
        'I': 450175,
        'S_t': 492707,
        'IP_min': 668358,
    },
    'classification': {
        'timing': 'g < t < n',  # g < t < n | t < g < n | t < n < g
        'dimensions': 2,  # a_10 | a_10 and a_20
        'result': 'success',  # success | fail | oversave
        'method': 'simplex-pulp',  # none | easy | boundary | simplex-pulp | simplex-scipy
    },
    'solution': {
        'success': True,
        'save_before': 0.0,
        'saved': 492706.99923764257,
        'debt': 21603121.159358896,
        'scheme': [
            {
                'month': 7,
                'init_save': 16795.077,
            },
            {
                'month': 0,
                'init_save': 118977.98,
            },
        ],
    },
    'coefficients': {
        'None': {
            'Amp_1': 0.010760523598313223,
            'Zmp_1': 260872.904503037,
        },
        7: {
            'Amp_1s': 0.011612946719394817,
            'Zmp_1s': 245876.84212777286,
            'Amp_1s_c': 0.011612946719394817,
            'Zmp_1s_c': 245876.842127773,
            'Amp_1sp': 0.011742422911231712,
            'Bmp_1sp': 0.011149296984258171,
            'Zmp_1sp': 243599.06129231837,
            'Ad_2': 1.053198504606253,
            'Bd_2': 1.0,
            'Zd_2': 21848827.027951527,
            # 'As_2': 1.053198504606253,
            'As_2': 1.0,
            'Bs_2': 1.0,
            # 'Zs_2': 21848827.027951527,
            'Zs_2': 0.0,
            'Ad_2_c': 1.0415855578868582,
            'Zd_2_c': 22053125.18582376,
            'Amp_2': 0.01595272266876192,
            'Bmp_2': 0.01514692871191075,
            'Zmp_2': 330942.6254312506,
        },
        (7, 0): {
            'Amp_2s': 0.01595272266876192,
            'Bmp_2s': 0.01514692871191075,
            'Zmp_2s': 330942.62543125066,
            'Amp_2s_c': 0.015776822192668037,
            'Zmp_2s_c': 334037.115064516,
            'Amp_2sp': 0.01619507160683044,
            'Bmp_2sp': 0.015377036271889785,
            'Cmp_2sp': 0.015191697561637806,
            'Zmp_2sp': 329131.28325724637,
            'Ad_3': 1.0563624482332956,
            'Bd_3': 1.0030041284840463,
            'Cd_3': 0.9909149659000654,
            'Zd_3': 21468378.56679513,
            'As_3': 0.9514147851795087,
            'Bs_3': 0.9538688911843306,
            'Cs_3': 0.9544249073150866,
            'Zs_3': 363131.1502282609,
            'Ad_3_c': 1.0290811255048182,
            'Zd_3_c': 21788373.23087322,
        }
    }
}

problem_no_mortgage__1 = {
    'params': {
        'I': 811958,
        'S_i': 8715762,
        'S_t': 3320118,
        'C': 774365,
        'R': 464199,
        'IP_min': 542055,
        'k_1': 0.0323,
        'l': 390,
        'n': 127,
    },
    'error': {
        'code': 'NOMORTGAGE',
        'message': 'Realty can be bought and repairing can be payed without credits, need 3320118, but can save more: 324605017',
        'payload': {
            'have': 324605017,
            'need': 3320118,
        }
    }
}
problem_no_mortgage__2 = {
    'params': {
        'I': 95629,
        'S_i': 9975222,
        'S_t': 7468613,
        'C': 2903279,
        'R': 900761,
        'IP_min': 2525852,
        'k_1': 0.0278,
        'k_2': 0.0284,
        'l': 5,
        'm': 9,
        'n': 611,
    },
    'error': {
        'code': 'NOMORTGAGE',
        'message': 'Realty can be bought and repairing can be payed without credits, need 7468613, but can save more: 8410749',
        'payload': {
            'have': 8410749,
            'need': 7468613,
        }
    }
}


class TestExecuteFunction(unittest.TestCase):

    def test__problem_set(self):
        problems = [
            't_n_g__1_oversave',
            't_n_g__2_oversave',
            'g_t_n__1_success',
            'g_t_n__1_success__S_0',
            'g_t_n__2_success',
            'g_t_n__2_success__P_1',
            't_g_n__1_success',
            't_g_n__2_success',
            't_g_n__1_oversave',
            't_g_n__2_oversave',
            't_0__1_success',
            't_0__2_success',
        ]
        for key in problems:
            problem = problem_set[key]
            result = SavingsSolver.execute(problem['params'], problem['solution'])
            self.assertEqual(round(result['D'], precision),
                             round(problem['solution']['debt'], precision),
                             'Should be %f (rounded)' % problem['solution']['debt'])
            self.assertEqual(round(result['S'], precision),
                             round(problem['solution']['saved'], precision),
                             'Should be %f (rounded)' % problem['solution']['saved'])

    def test_problem_x_simplex(self):
        problem = problem_x_simplex
        result = SavingsSolver.execute(problem['params'], problem['solution'])
        self.assertEqual(round(result['D'], precision),
                         round(problem['solution']['debt'], precision),
                         'Should be %f (rounded)' % problem['solution']['debt'])
        self.assertEqual(round(result['S'], precision),
                         round(problem['solution']['saved'], precision),
                         'Should be %f (rounded)' % problem['solution']['saved'])

    def test_problem_xy_simplex(self):
        problem = problem_xy_simplex
        result = SavingsSolver.execute(problem['params'], problem['solution'])
        self.assertEqual(round(result['D'], precision),
                         round(problem['solution']['debt'], precision),
                         'Should be %f (rounded)' % problem['solution']['debt'])
        self.assertEqual(round(result['S'], precision),
                         round(problem['solution']['saved'], precision),
                         'Should be %f (rounded)' % problem['solution']['saved'])
    
    def test_xy_next_savings(self):
        params = {
            'C': 5000000,
            'S_i': 1000000,
            'R': 60000,
            'k_1': 10/1200,
            'k_2': 15/1200,
            'l': 20,
            'm': 30,
            'n': 240,
            'I': 150000,
            'S_t': 1000000,
            'IP_min': 700000
        }
        scheme = {
            'save_before': 4517,
            'debt': 677420.7701016981,
            'saved': 3267509.4334662086,
            'scheme': [
                {
                    'month': 10,
                    'init_save': 0,
                    'next_savings': 50000
                },
                {
                    'month': 9,
                    'init_save': 0
                }
            ]
        }
        result = SavingsSolver.execute(params, scheme)
        self.assertEqual(round(result['D'], precision),
                         round(scheme['debt'], precision),
                         'Should be %f (rounded)' % scheme['debt'])
        self.assertEqual(round(result['S'], precision),
                         round(scheme['saved'], precision),
                         'Should be %f (rounded)' % scheme['saved'])


class TestInstanceCreation(unittest.TestCase):

    def test_positive(self):
        
        """
        Try to catch an error of incorrect set of "k_2" and "m" parameters (1)
        """
        
        params = {
            'C': 27559190,
            'S_i': 11902044,
            'R': 197583,
            'k_1': 0.0177,
            'k_2': 0.0234,
            'l': 14,
            'n': 62,
            'I': 576279,
            'S_t': 2194,
            'IP_min': 5511838
        }

        e_code = None
        e_msg = None
        
        try:
            _ = SavingsSolver(params)
        except SavingsError as se:
            e_code = se.code
            e_msg = se.message
        
        self.assertEqual(e_code, 'PARAMS', 'Should be "PARAMS"')
        self.assertEqual(e_msg, 'The "k_2" and "m" should simultaneously be or not be presented in "params"')

    def test_negative(self):
        
        """
        Try to catch an error of incorrect set of "k_2" and "m" parameters (2)
        """
        
        params = {
            'C': 27559190,
            'S_i': 11902044,
            'R': 197583,
            'k_1': 0.0177,
            'l': 14,
            'm': 6,
            'n': 62,
            'I': 576279,
            'S_t': 2194,
            'IP_min': 5511838
        }

        e_code = None
        e_msg = None
        
        try:
            _ = SavingsSolver(params)
        except SavingsError as se:
            e_code = se.code
            e_msg = se.message
        
        self.assertEqual(e_code, 'PARAMS', 'Should be "PARAMS"')
        self.assertEqual(e_msg, 'The "k_2" and "m" should simultaneously be or not be presented in "params"')


class TestGetCoefficients(unittest.TestCase):

    def test_problem_xy_simplex__7_0(self):
        problem = SavingsSolver(problem_xy_simplex['params'])

        for key, val in problem_xy_simplex['coefficients']['None'].items():
            (cfn, ) = problem._SavingsSolver__get_cfs([key])
            self.assertEqual(round(cfn, precision),
                             round(val, precision),
                             'Should be %f (rounded)' % val)

        x = 7
        for key, val in problem_xy_simplex['coefficients'][7].items():
            (cfn, ) = problem._SavingsSolver__get_cfs([key], x)
            self.assertEqual(round(cfn, precision),
                             round(val, precision),
                             'Should be %f (rounded)' % val)

        y = 0
        for key, val in problem_xy_simplex['coefficients'][(7, 0)].items():
            (cfn,) = problem._SavingsSolver__get_cfs([key], x, y)
            self.assertEqual(round(cfn, precision),
                             round(val, precision),
                             'Should be %f (rounded)' % val)


class TestGetT(unittest.TestCase):

    def test_positive(self):
        params = {
            'C': 38282212,
            'S_i': 27689109,
            'R': 172086,
            'k_1': 0.0214,
            'k_2': 0.0103,
            'l': 35,
            'm': 53,
            'n': 182,
            'I': 239454,
            'S_t': 52937,
            'IP_min': 4593865
        }
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_t()
        expected = 92.10978371539112
        self.assertEqual(result, expected, 'Should be %f' % expected)

    def test_negative_1(self):
        params = {
            'C': 20000000,
            'S_i': 2000000,
            'R': 100000,
            'k_1': 0.0214,
            'k_2': 0.0103,
            'l': 35,
            'm': 53,
            'n': 182,
            'I': 30000,
            'S_t': 1000000,
            'IP_min': 1000000
        }
        expected = ('MP1', 'MP1: need 395729 but have %d' % params['I'])
        error = []
        try:
            problem = SavingsSolver(params)
            problem._SavingsSolver__get_t()
        except CreditError as e:
            error = [e.code, e.message]
        self.assertEqual(error[0], expected[0], 'Should be message: %s' % expected[0])
        self.assertEqual(error[1], expected[1], 'Should be message: %s' % expected[1])

    def test_negative_2(self):
        params = {
            'C': 20000000,
            'S_i': 2000000,
            'R': 100000,
            'k_1': 0.0214,
            'k_2': 0.1234,
            'l': 35,
            'm': 53,
            'n': 182,
            'I': 400000,
            'S_t': 1000000,
            'IP_min': 1000000
        }
        expected = ('MP2', 'MP2: need 2153366 but have %d' % params['I'])
        error = []
        try:
            problem = SavingsSolver(params)
            problem._SavingsSolver__get_t()
        except CreditError as e:
            error = [e.code, e.message]
        self.assertEqual(error[0], expected[0], 'Should be message: %s' % expected[0])
        self.assertEqual(error[1], expected[1], 'Should be message: %s' % expected[1])


class TestGetD(unittest.TestCase):
    
    def test_x(self):
        params = {
            'C': 5000000,
            'R': 60000,
            'I': 100000,
            'S_i': 1000000,
            'IP_min': 700000,
            'S_t': 1000000,
            'k_1': 10 / 1200,
            'l': 12,
            'n': 240,
        }
        S_0 = 0
        x = 3
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_d(S_0, x)
        expected = 3811153.3113912903
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)

    def test_xy(self):
        params = {
            'C': 5000000,
            'R': 60000,
            'I': 100000,
            'S_i': 1000000,
            'IP_min': 700000,
            'S_t': 1000000,
            'k_1': 10 / 1200,
            'k_2': 15 / 1200,
            'l': 12,
            'm': 12,
            'n': 240,
        }
        S_0 = 0
        x = 3
        y = 3
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_d(S_0, x, y)
        expected = 3623980.71031829
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)


class TestGetS(unittest.TestCase):
    
    def test_x(self):
        params = {
            'C': 5000000,
            'S_i': 1000000,
            'R': 60000,
            'k_1': 10 / 1200,
            'l': 12,
            'n': 240,
            'I': 100000,
            'IP_min': 700000,
            'S_t': 1000000
        }
        S_0 = 0
        x = 2
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_s(S_0, x)
        expected = 620019.926826541
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)

    def test_xy(self):
        params = {
            'C': 5000000,
            'S_i': 1000000,
            'R': 60000,
            'k_1': 10 / 1200,
            'k_2': 15 / 1200,
            'l': 12,
            'm': 12,
            'n': 240,
            'I': 100000,
            'IP_min': 700000,
            'S_t': 1000000
        }
        S_0 = 0
        x = 2
        y = 2
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_s(S_0, x, y)
        expected = 1118694.5701379157
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)


class TestGetS0(unittest.TestCase):
    
    def test_x(self):
        params = {
            'C': 5000000,
            'R': 60000,
            'I': 100000,
            'S_i': 1000000,
            'IP_min': 700000,
            'S_t': 1000000,
            'k_1': 10 / 1200,
            'l': 12,
            'n': 240
        }
        x = 10
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_s_0(x)
        expected = 884814.3254008256
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)

    def test_xy(self):
        params = {
            'C': 5000000,
            'R': 60000,
            'I': 100000,
            'S_i': 1000000,
            'IP_min': 700000,
            'S_t': 1000000,
            'k_1': 10 / 1200,
            'k_2': 15 / 1200,
            'l': 12,
            'm': 12,
            'n': 240
        }
        x = 10
        y = 3
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_s_0(x, y)
        expected = 412186.2039246257
        self.assertEqual(round(result, precision),
                         round(expected, precision),
                         'Should be %f (rounded)' % expected)


class TestGetBoundarySolution(unittest.TestCase):

    def test_x(self):
        params = {
            'C': 5000000,
            'S_i': 1000000,
            'R': 60000,
            'k_1': 10 / 1200,
            'l': 34,
            'n': 240,
            'I': 150000,
            'IP_min': 700000,
            'S_t': 1000000
        }
        x = 20
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_bnd_sltn(params['S_t'], 0, problem.params['S_0_top'], x)
        expected = {'success': True, 'S0': 0, 'S': 1885385.2014754326, 'D': 1506694.1381920152}
        self.assertEqual(result['success'], expected['success'], 'Should be %d' % expected['success'])
        self.assertEqual(round(result['S'], precision),
                         round(expected['S'], precision),
                         'Should be %f (rounded)' % expected['S'])
        self.assertEqual(round(result['D'], precision),
                         round(expected['D'], precision),
                         'Should be %f (rounded)' % expected['D'])

    def test_xy(self):
        params = {
            'C': 5000000,
            'S_i': 1000000,
            'R': 60000,
            'k_1': 10 / 1200,
            'k_2': 15 / 1200,
            'l': 34,
            'm': 10,
            'n': 240,
            'I': 150000,
            'IP_min': 700000,
            'S_t': 1000000
        }
        x = 20
        y = 5
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__get_bnd_sltn(params['S_t'], 0, problem.params['S_0_top'], x, y)
        expected = {'success': True, 'S0': 0, 'S': 2578565.5198449567, 'D': 829463.6683605933}
        self.assertEqual(result['success'], expected['success'], 'Should be %d' % expected['success'])
        self.assertEqual(round(result['S'], precision),
                         round(expected['S'], precision),
                         'Should be %f (rounded)' % expected['S'])
        self.assertEqual(round(result['D'], precision),
                         round(expected['D'], precision),
                         'Should be %f (rounded)' % expected['D'])


class TestComputeSimplex(unittest.TestCase):

    x_case_params = {
        'I': 150000,
        'S_i': 1000000,
        'S_t': 1000000,
        'C': 5000000,
        'IP_min': 700000,
        'R': 60000,
        'k_1': 10 / 1200,
        'l': 34,
        'n': 240,
    }

    def test_x_is_0(self):
        x = 0
        problem = SavingsSolver(self.x_case_params)
        result = problem._SavingsSolver__compute_simplex(x)
        expected = {
            'D': 3745599.76584564,
            'S': 3692401.995112634,
        }
        self.assertEqual(round(result['S'], precision),
                         round(expected['S'], precision),
                         'Should be %f' % expected['S'])
        self.assertEqual(round(result['D'], precision),
                         round(expected['D'], precision),
                         'Should be %f' % expected['D'])

    def test_x_is_14(self):
        x = 14
        problem = SavingsSolver(self.x_case_params)
        result = problem._SavingsSolver__compute_simplex(x)
        expected = {
            'D': 2143027.140916196,
            'S': 2435725.8805401325,
        }
        self.assertEqual(round(result['S'], precision),
                         round(expected['S'], precision),
                         'Should be %f' % expected['S'])
        self.assertEqual(round(result['D'], precision),
                         round(expected['D'], precision),
                         'Should be %f' % expected['D'])

    def test_x_is_27(self):
        x = 27
        problem = SavingsSolver(self.x_case_params)
        result = problem._SavingsSolver__compute_simplex(x)
        expected = {
            'D': 540755.2815145203,
            'S': 999999.9998599018,
            'a_10': 133010.99,
        }
        self.assertEqual(round(result['S'], precision),
                         round(expected['S'], precision),
                         'Should be %f' % expected['S'])
        self.assertEqual(round(result['D'], precision),
                         round(expected['D'], precision),
                         'Should be %f' % expected['D'])
        self.assertEqual(round(result['a_10'], precision),
                         round(expected['a_10'], precision),
                         'Should be %f' % expected['a_10'])

    def test_x_is_28(self):
        x = 28
        problem = SavingsSolver(self.x_case_params)
        result = problem._SavingsSolver__compute_simplex(x)
        expected = {
            'D': 578018.5010487183,
            'S': 999999.9969846805,
            'a_10': 144119.04,
            'S_0': 135285.76,
        }
        self.assertEqual(round(result['S'], precision),
                         round(expected['S'], precision),
                         'Should be %f' % expected['S'])
        self.assertEqual(round(result['D'], precision),
                         round(expected['D'], precision),
                         'Should be %f' % expected['D'])
        self.assertEqual(round(result['a_10'], precision),
                         round(expected['a_10'], precision),
                         'Should be %f' % expected['a_10'])
        self.assertEqual(round(result['S_0'], precision),
                         round(expected['S_0'], precision),
                         'Should be %f' % expected['S_0'])

    def test_x_is_29_infeasible(self):

        """
        Catch an infeasible case
        """

        x = 29

        problem = SavingsSolver(self.x_case_params)
        
        expected = (2, 'Problem infeasible, can\'t save %d' % self.x_case_params['S_t'])
        error = []

        try:
            problem._SavingsSolver__compute_simplex(x)
        except ComputationError as e:
            error = [e.code, e.message]
        
        self.assertEqual(error[0], expected[0], 'Should be message: %s' % expected[0])
        self.assertEqual(error[1], expected[1], 'Should be message: %s' % expected[1])

    def test_x_is_33_infeasible(self):

        """
        S_0_min is bigger than S_0_max
        """

        x = 33

        problem = SavingsSolver(self.x_case_params)
        
        expected = (1, 'S_0_min is 252113 and S_0_max is 240000')
        error = []

        try:
            problem._SavingsSolver__compute_simplex(x)
        except ComputationError as e:
            error = [e.code, e.message]
        
        self.assertEqual(error[0], expected[0], 'Should be message: %s' % expected[0])
        self.assertEqual(error[1], expected[1], 'Should be message: %s' % expected[1])

    def test_xy_1(self):

        params = {
            'I': 239454,
            'S_i': 27689109,
            'S_t': 52937,
            'C': 38282212,
            'IP_min': 4593865,
            'R': 172086,
            'k_1': 0.0214,
            'k_2': 0.0103,
            'l': 35,
            'm': 53,
            'n': 182,
        }

        x = 34
        y = 52

        problem = SavingsSolver(params)
        result = problem._SavingsSolver__compute_simplex(x,y)
        
        expected = {
            'D': 1011677.5282826927,
            'S': 52937.0,
        }

        self.assertEqual(round(result['S'], precision), round(expected['S'], precision), 'Should be %f' % expected['S'])
        self.assertEqual(round(result['D'], precision), round(expected['D'], precision), 'Should be %f' % expected['D'])

    def test_xy_2(self):

        params = {
            'I': 450175,
            'C': 66835858,
            'S_i': 42687639,
            'S_t': 492707,
            'R': 95295,
            'k_1': 0.0065,
            'k_2': 0.0122,
            'l': 8,
            'm': 4,
            'n': 143,
            'IP_min': 668358,
        }

        x = 5
        y = 3

        problem = SavingsSolver(params)
        result = problem._SavingsSolver__compute_simplex(x,y)
        
        expected = {
            'D': 21614969.308619913,
            'S': 492706.99961478676,
            'S_0_max': 17592275.48431168,
            'a_20': 88595.526,
        }

        self.assertEqual(round(result['S'], precision), round(expected['S'], precision), 'Should be %f' % expected['S'])
        self.assertEqual(round(result['D'], precision), round(expected['D'], precision), 'Should be %f' % expected['D'])
        self.assertEqual(round(result['S_0_max'], precision), round(expected['S_0_max'], precision), 'Should be %f' % expected['S_0_max'])
        self.assertEqual(round(result['a_20'], precision), round(expected['a_20'], precision), 'Should be %f' % expected['a_20'])

    def test__x_additional(self):
        params = {
            'I': 576279,
            'S_i': 11902044,
            'S_t': 2194,
            'C': 27559190,
            'IP_min': 5511838,
            'R': 197583,
            'k_1': 0.0177,
            'l': 14,
            'n': 62,
        }
        x = 13
        problem = SavingsSolver(params)
        result = problem._SavingsSolver__compute_simplex(x)
        expected = {
            'D': 11206198.91696578,
            'S': 2194.0
        }
        self.assertEqual(round(result['S'], precision),
                         round(expected['S'], precision),
                         'Should be %f' % expected['S'])
        self.assertEqual(round(result['D'], precision),
                         round(expected['D'], precision),
                         'Should be %f' % expected['D'])

    def test__problem_xy_simplex(self):
        x = problem_xy_simplex['solution']['scheme'][0]['month']
        y = problem_xy_simplex['solution']['scheme'][1]['month']
        problem = SavingsSolver(problem_xy_simplex['params'])
        result = problem._SavingsSolver__compute_simplex(x, y)
        self.assertEqual(round(result['S'], 0),
                         round(problem_xy_simplex['solution']['saved'], 0),
                         'Should be %f' % problem_xy_simplex['solution']['saved'])
        self.assertEqual(round(result['D'], precision),
                         round(problem_xy_simplex['solution']['debt'], precision),
                         'Should be %f' % problem_xy_simplex['solution']['debt'])
        self.assertEqual(round(result['S_0'], 0),
                         round(problem_xy_simplex['solution']['save_before'], 0),
                         'Should be %f' % problem_xy_simplex['solution']['save_before'])
        self.assertEqual(round(result['a_10'], 0),
                         round(problem_xy_simplex['solution']['scheme'][0]['init_save'], 0),
                         'Should be %f' % problem_xy_simplex['solution']['scheme'][0]['init_save'])
        self.assertEqual(round(result['a_20'], 0),
                         round(problem_xy_simplex['solution']['scheme'][1]['init_save'], 0),
                         'Should be %f' % problem_xy_simplex['solution']['scheme'][1]['init_save'])


class TestFindBestSolution(unittest.TestCase):

    def test__problem_set__success_oversave(self):
        problems = [
            't_n_g__1_oversave',
            't_n_g__2_oversave',
            'g_t_n__1_success',
            'g_t_n__1_success__S_0',
            'g_t_n__2_success',
            'g_t_n__2_success__P_1',
            't_g_n__1_success',
            't_g_n__2_success',
            't_g_n__1_oversave',
            't_g_n__2_oversave',
            't_0__1_success',
            't_0__2_success',
        ]
        for key in problems:
            desc = problem_set[key]
            problem = SavingsSolver(desc['params'])
            result = problem.find_best_solution()
            self.assertEqual(round(result['saved'], precision),
                             round(desc['solution']['saved'], precision),
                             'Should be %f' % desc['solution']['saved'])
            self.assertEqual(round(result['debt'], precision),
                             round(desc['solution']['debt'], precision),
                             'Should be %f' % desc['solution']['debt'])
            self.assertEqual(round(result['save_before'], precision),
                             round(desc['solution']['save_before'], precision),
                             'Should be %f' % desc['solution']['save_before'])
            # self.assertEqual(round(result['scheme'][0]['init_save'], precision),
            #                  round(desc['solution']['scheme'][0]['init_save'], precision),
            #                  'Should be %f' % desc['solution']['scheme'][0]['init_save'])
            # if len(desc['solution']['scheme']) > 1:
            #     self.assertEqual(round(result['scheme'][1]['init_save'], precision),
            #                      round(desc['solution']['scheme'][1]['init_save'], precision),
            #                      'Should be %f' % desc['solution']['scheme'][1]['init_save'])

    def test__problem_set__fail(self):
        problems = [
            't_n_g__1_fail',
            't_n_g__2_fail',
            'g_t_n__1_fail',
            'g_t_n__2_fail',
            't_g_n__1_fail',
            't_g_n__2_fail',
            't_0__1_fail',
            't_0__2_fail',
        ]
        for key in problems:
            desc = problem_set[key]
            problem = SavingsSolver(desc['params'])
            result = problem.find_best_solution()
            self.assertEqual(result,
                             desc['solution'],
                             'Should be %s' % str(desc['solution']))

    def test__problem_x_simplex(self):
        problem = SavingsSolver(problem_x_simplex['params'])
        result = problem.find_best_solution()
        self.assertEqual(round(result['saved'], precision),
                         round(problem_x_simplex['solution']['saved'], precision),
                         'Should be %f' % problem_x_simplex['solution']['saved'])
        self.assertEqual(round(result['debt'], precision),
                         round(problem_x_simplex['solution']['debt'], precision),
                         'Should be %f' % problem_x_simplex['solution']['debt'])
        self.assertEqual(round(result['save_before'], precision),
                         round(problem_x_simplex['solution']['save_before'], precision),
                         'Should be %f' % problem_x_simplex['solution']['save_before'])
        self.assertEqual(round(result['scheme'][0]['init_save'], precision),
                         round(problem_x_simplex['solution']['scheme'][0]['init_save'], precision),
                         'Should be %f' % problem_x_simplex['solution']['scheme'][0]['init_save'])

    def test__problem_xy_simplex(self):
        problem = SavingsSolver(problem_xy_simplex['params'])
        result = problem.find_best_solution(debug=True)
        self.assertEqual(round(result['saved'], precision),
                         round(problem_xy_simplex['solution']['saved'], precision),
                         'Should be %f' % problem_xy_simplex['solution']['saved'])
        self.assertEqual(round(result['debt'], precision),
                         round(problem_xy_simplex['solution']['debt'], precision),
                         'Should be %f' % problem_xy_simplex['solution']['debt'])
        self.assertEqual(round(result['save_before'], precision),
                         round(problem_xy_simplex['solution']['save_before'], precision),
                         'Should be %f' % problem_xy_simplex['solution']['save_before'])
        self.assertEqual(round(result['scheme'][0]['init_save'], precision),
                         round(problem_xy_simplex['solution']['scheme'][0]['init_save'], precision),
                         'Should be %f' % problem_xy_simplex['solution']['scheme'][0]['init_save'])
        self.assertEqual(round(result['scheme'][1]['init_save'], precision),
                         round(problem_xy_simplex['solution']['scheme'][1]['init_save'], precision),
                         'Should be %f' % problem_xy_simplex['solution']['scheme'][1]['init_save'])

    def test__problem_no_mortgage__1(self):
        try:
            _ = SavingsSolver(problem_no_mortgage__1['params'], launch=True)
        except SavingsError as e:
            self.assertEqual(e.code,
                             problem_no_mortgage__1['error']['code'],
                             'Should be %s' % problem_no_mortgage__1['error']['code'])
            self.assertEqual(e.message,
                             problem_no_mortgage__1['error']['message'],
                             'Should be %s' % problem_no_mortgage__1['error']['message'])
            self.assertEqual(e.payload,
                             problem_no_mortgage__1['error']['payload'],
                             'Should be %s' % problem_no_mortgage__1['error']['payload'])

    def test__problem_no_mortgage__2(self):
        try:
            _ = SavingsSolver(problem_no_mortgage__2['params'], launch=True)
        except SavingsError as e:
            self.assertEqual(e.code,
                             problem_no_mortgage__2['error']['code'],
                             'Should be %s' % problem_no_mortgage__2['error']['code'])
            self.assertEqual(e.message,
                             problem_no_mortgage__2['error']['message'],
                             'Should be %s' % problem_no_mortgage__2['error']['message'])
            self.assertEqual(e.payload,
                             problem_no_mortgage__2['error']['payload'],
                             'Should be %s' % problem_no_mortgage__2['error']['payload'])


if __name__ == '__main__':
    unittest.main()
