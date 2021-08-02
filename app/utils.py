from copy import deepcopy

# TODO: get rid of inflation attribute (for the future)
# TODO: find libs for checking equality of dictionaries


def convert_input(data):
    result = {
        "personal_data": {
            "current_savings": data["personal_data"]["current_savings"],
            "month_income": data["personal_data"]["income_per_month"],
            "month_expenses": data["personal_data"]["expenses_per_month"],
            "month_rent": data["personal_data"]["rent_expenses_per_month"],
            "deal_month_start": data["personal_data"]["deal_period_start_month"],
            "deal_month_finish": data["personal_data"]["deal_period_end_month"],
            "max_repairing_delay_months": data["personal_data"]["max_repairing_delay_months"],
            "inflation_percent": 0.0
        }
    }

    if "credit_scheme" in data:
        result["credit_scheme"] = {
            "interest_rate": data["credit_scheme"]["interest_rate"],
            "months": data["credit_scheme"]["months"],
        }

    realties = {key: convert_realty(rlt) for key, rlt in data["realties"].items()}
    result['realties'] = realties

    result["use_no_mortgage"] = data["use_no_mortgage"]

    if 'mortgages' in data:
        result['mortgage_schemes'] = {key: convert_mortgage_scheme(mrg) for key, mrg in data["mortgages"].items()}

    return result


def convert_realty(rlt):
    return {
        "id": rlt["id"],
        "is_primary": rlt["is_primary"],
        "get_keys_month": 0 if not rlt["is_primary"] else rlt["get_keys_month"],
        "cost": rlt["cost"],
        "repairing_expenses": rlt["repairing_expenses"],
        "repairing_months": rlt["repairing_months"]
    }


def convert_mortgage_scheme(mrg):
    schedule = [{
        "interest_rate": period["interest_rate"],
        "months": period["months"]}
        for period in mrg["schedule"]]
    return {
        "id": mrg["id"],
        "initial_payment_percent": mrg["initial_payment_percent"],
        "initial_expenses": mrg["initial_expenses"],
        "schedule": schedule
    }


def convert_output(output_data):
    ui_precision = 2

    def handle_case(case):
        case['success'] = True
        case['deal_month'] = case['x'][0]
        case['repairing_gap'] = case['x'][1]
        del case['x']
        case.update(case['result'])
        del case['result']
        case['savings'] = round(case['savings'], ui_precision)
        return case

    def solve(obj, with_credit):
        del obj['combs']

        if obj['opt'] is None:
            obj['savings'] = {'success': False}
            if with_credit:
                obj['credit'] = {'success': False}
        else:
            if 'savings' in obj['opt']:
                obj['savings'] = obj['opt']['savings']
                obj['savings'] = handle_case(obj['savings'])
            else:
                obj['savings'] = {'success': False}
            if with_credit:
                if 'credit' in obj['opt']:
                    obj['credit'] = obj['opt']['credit']
                    obj['credit'] = handle_case(obj['credit'])
                else:
                    obj['credit'] = {'success': False}

        del obj['opt']
        return obj
    
    for realty in output_data.values():
        if 'without_mortgage' in realty:
            realty['without_mortgage'] = solve(realty['without_mortgage'], realty['with_credit'])

        if 'with_mortgage' in realty:
            realty['with_mortgage'] = {key: solve(mrg, realty['with_credit']) for key, mrg in realty['with_mortgage'].items()}

    return output_data


def clarify_input(data):

    matches = {
        'None': None,
        'none': None,
        'null': None,
        'True': True,
        'true': True,
        'False': False,
        'false': False
    }

    if isinstance(data, list):
        temp_list = []
        for element in data:
            temp_list.append(clarify_input(element))
        return temp_list
    elif isinstance(data, dict):
        temp_dict = {}
        for key, value in data.items():
            temp_dict[key] = clarify_input(value)
        return temp_dict
    else:
        if data in matches:
            return matches[data]
        return data


def clarify_output(data):

    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_value = clarify_output(value)
            if isinstance(key, int) or isinstance(key, tuple):
                new_data[str(key)] = new_value
            else:
                new_data[key] = new_value
        return new_data
    elif isinstance(data, list):
        return [clarify_output(e) for e in data]
    else:
        return data


def is_equal(x_1, x_2, float_prc):

    def func(x, y):
        
        if type(x) != type(y):
            return False
        
        if x is None:
            return True
        
        if isinstance(x, int) or isinstance(x, bool) or isinstance(x, str):
            if x != y:
                return False
            else:
                return True
        
        if isinstance(x, float):
            if round(x, float_prc) != round(y, float_prc):
                return False
            else:
                return True

        if isinstance(x, list):
            if len(x) != len(y):
                return False
            for e in range(len(x)):
                if not func(x[e], y[e]):
                    return False
            return True
        
        if isinstance(x, dict):
            if len(x) != len(y):
                return False
            for x_key, x_value in x.items():
                if x_key not in y:
                    return False
                if not func(x_value, y[x_key]):
                    return False
            return True

    return func(x_1, x_2)


def validate_data(data):
    err = []
    if "personal_data" not in data:
        err.append("There should be personal_data in request.")

    if "realties" in data:
        ln = len(data['realties'].keys())
        if ln == 0 or ln > 5:
            err.append("Should be at least 1 but max 5 realties.")
    else:
        err.append("Realties should be presented in the request data.")

    if "use_no_mortgage" not in data:
        err.append("Param use_no_mortgage is required.")

    if not data["use_no_mortgage"] and ("mortgages" not in data or len(data["mortgages"]) == 0):
        err.append("If there is no mortgages, should be allowed to use 'no mortgage' mode.")

    if "mortgages" in data and len(data["mortgages"]) > 3:
        err.append("Should be max 3 mortgages.")

    return err if len(err) > 0 else None
