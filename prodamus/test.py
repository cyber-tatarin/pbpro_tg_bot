import hashlib
import json
import hmac
from collections.abc import MutableMapping
from utils import generate_signature

data = {
    'date': '2023-04-29T16:01:10+03:00',
    'order_id': '12016712',
    'order_num': 'loka',
    'domain': 'testpage3.payform.ru',
    'sum': '300.00',
    'currency': 'rub',
    'customer_phone': '+375297861654',
    'customer_email': 'dmitriyseur@gmail.com',
    'customer_extra': 'Полная оплата курса',
    'payment_type': 'Оплата картой, выпущенной в РФ',
    'commission': '3.5',
    'commission_sum': '10.50',
    'attempt': '1',
    'products': [
        {
            'name': 'Обучающие материалы',
            'price': '300.00',
            'quantity': '1',
            'sum': '300.00'
        }
    ],
    'payment_status': 'success',
    'payment_status_description': 'Успешная оплата',
    'payment_init': 'manual'
}


secret_key = '0b6bef0be70db6ee8271736229b97b5804ef3af792d27622125abfefa66b2d2e'

# data = {k: str(v) for k, v in data.items()}
# sorted_data = json.dumps(data, ensure_ascii=False, sort_keys=True)
# if isinstance(sorted_data, str):
#     sorted_data = sorted_data.encode('utf-8')
# if isinstance(secret_key, str):
#     secret_key = secret_key.encode('utf-8')
# sorted_data = sorted_data.replace(b', ', b',').replace(b': ', b':').replace(b'"[', b'[').replace(b']"', b']').replace(b'\'', b'"')
# signature = hmac.new(secret_key, msg=sorted_data , digestmod='sha256').hexdigest()
# print(sorted_data.replace(b', ', b',').replace(b': ', b':'))



print(generate_signature(data))

# print('Сигнатура по моим вычислениям:', sign(data, secret_key))

print('Сигнатура Продамуса в заголовке запроса:', 'f43fb7eefe518cef0ae4770df89cec0cf8a6b8185e14067450bd76ffb20532ae')

print('https://testpage3.payform.ru/?order_id=loka&customer_phone=+375297861654&products[0][price]=300&products[0][quantity]=1&products[0][name]=Обучающие материалы&customer_extra=Полная оплата курса&do=pay')
