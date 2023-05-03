import hashlib
import json
import hmac
import os
from collections.abc import MutableMapping
from dotenv import load_dotenv, find_dotenv

from root.logger.log import logger


load_dotenv(find_dotenv())


@logger.catch
def generate_signature(gen_data):
    # переводим все значения data в string c помощью кастомной функции deep_int_to_string (см ниже)
    deep_int_to_string(gen_data)

    # переводим data в JSON, с сортировкой ключей в алфавитном порядке, без пробелов и экранируем бэкслеши
    data_json = json.dumps(gen_data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).replace("/", "\\/")
    print(data_json)
    # создаем подпись с помощью библиотеки hmac и возвращаем ее
    # секретный ключ продамуса достаем из окружения
    return hmac.new(os.getenv('PRODAMUS_SECRET_KEY').encode('utf8'), data_json.encode('utf8'), hashlib.sha256).hexdigest()


def deep_int_to_string(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, MutableMapping):
            deep_int_to_string(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                deep_int_to_string({str(k): v})
        else:
            dictionary[key] = str(value)
            

@logger.catch
def verify_signature(check_signature, check_data):
    benchmark_signature = generate_signature(check_data)
    logger.info('benchmark_sign:')
    logger.info(benchmark_signature)
    logger.info('check_sign:')
    logger.info(check_signature)
    if benchmark_signature == check_signature:
        logger.info('Signatures are equal')
        return True
    else:
        logger.info('Signatures are not equal')
        return False
        
        
if __name__ == '__main__':
    data = {"date" : "2023-05-02T23:57:13+03:00","order_id" : "12110326","order_num":"1cc7bb02-b277-45ac-9989-e588190d4cc6","domain":"testpage3.payform.ru","sum":"2000.00","currency":"rub","customer_phone":"+375297861654","customer_email":"dmitriyseur@gmail.com","customer_extra":"\u041f\u043e\u043b\u043d\u0430\u044f \u043e\u043f\u043b\u0430\u0442\u0430 \u043a\u0443\u0440\u0441\u0430","payment_type":"\u041e\u043f\u043b\u0430\u0442\u0430 \u043a\u0430\u0440\u0442\u043e\u0439, \u0432\u044b\u043f\u0443\u0449\u0435\u043d\u043d\u043e\u0439 \u0432 \u0420\u0424","commission" : "3.5","commission_sum" : "70.00","attempt" : "13","products":[{"name":"\u041e\u0431\u0443\u0447\u0430\u044e\u0449\u0438\u0435 \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b","price":"2000.00","quantity":"1","sum":"2000.00"}],"payment_status":"success","payment_status_description":"\u0423\u0441\u043f\u0435\u0448\u043d\u0430\u044f \u043e\u043f\u043b\u0430\u0442\u0430","payment_init":"manual"}
    print(generate_signature(data))
    