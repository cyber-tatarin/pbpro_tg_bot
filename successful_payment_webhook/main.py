from flask import Flask, request
import sys
import json
import os

from prodamus.main import confirm_payment

app = Flask(__name__)


@app.route('/payment', methods=['POST'])
def payment():
    # Handle the payment data here
    print("it's post request baby")
    print(request.form.to_dict())
    print(request.headers.get('Sign'))
    data = request.form.to_dict()
    signature = request.headers.get('Sign')
    
    confirm_payment(signature, data)
    
    return "Payment received"


@app.route('/', methods=['GET'])
def go():
    # Handle the payment data here
    # Do something with the data
    print("we've got data in get request", file=sys.stderr)
    return "Payment received"


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
    