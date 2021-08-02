import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils import convert_input, convert_output, clarify_output
from scheduler import Scheduler
from budget import Budget

# TODO: get rid of settling expenses
# TODO: add max_repairing_delay_months
# TODO: add inflation_percent
# TODO: add min debt for mortgage

app = Flask(__name__)


env = os.environ.copy()
cors = CORS(app, resources={r"/*": {"origins": env.get('SPA_URL')}})


@app.route('/', methods=['GET'])
def ping():
    return '''Hello, I\'m Mortgage Calculator, version 0.1.02
              You can use one POST method: count'''


@app.route('/count', methods=['POST'])
def count():
    data = request.json
    try:
        # TODO: validate input data
        data = convert_input(data)
        sch = Scheduler(data)
        result = clarify_output(convert_output(sch.solution))
        return jsonify(result), 200
    except Exception as Ex:
        # TODO: here it's better to make logging with notification and more detailed error messaging
        return jsonify({'status': 'Bad input',
                        'Exception.class': Ex.__class__,
                        'Exception.msg': Ex.__repr__()}), 400


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int("5000"), debug=False)


# @app.route('/compare', methods=['POST'])
# def compare():
#     data = request.json
#     try:
#         # TODO: validate input data
#         data = convert_input(data)
#         sch = Scheduler(data)
#         result = clarify_output(convert_output(sch.solution))
#         return jsonify(result), 200
#     except Exception as Ex:
#         # TODO: here it's better to make logging with notification and more detailed error messaging
#         return jsonify({'status': 'Bad input', 'Exception.class': Ex.__class__, 'Exception.msg': Ex.__repr__()}), 400


# @app.route('/expand', methods=['POST'])
# def expand():
#     scenario = request.json
#     try:
#         # TODO: validate input data
#         result = Budget.execute(scenario)
#         return jsonify(clarify_output(result.history)), 200
#     except Exception as Ex:
#         # TODO: here it's better to make logging with notification and more detailed error messaging
#         return jsonify({'status': 'Bad input', 'Exception.class': Ex.__class__, 'Exception.msg': Ex.__repr__()}), 400
