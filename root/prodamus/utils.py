import hashlib
import json
import hmac
import os
import re
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
    return hmac.new(os.getenv('PRODAMUS_SECRET_KEY').encode('utf8'), data_json.encode('utf8'),
                    hashlib.sha256).hexdigest()


def deep_int_to_string(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, MutableMapping):
            deep_int_to_string(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                deep_int_to_string({str(k): v})
        else:
            dictionary[key] = str(value)


def transform_json(json_obj):
    # regular expression pattern to match "products[X][Y]"
    pattern = re.compile(r"products\[(\d+)]\[(\w+)]")
    
    # create an empty list to store the new "products" key
    new_products = []
    
    # iterate over the keys of the JSON object
    for key in list(json_obj.keys()):
        match = pattern.match(key)
        if match:
            # extract the X and Y values from the matched key
            X = int(match.group(1))
            Y = match.group(2)
            # create a dictionary with the corresponding key-value pair
            new_item = {Y: json_obj.pop(key)}
            # add the new item to the list of products
            if len(new_products) <= X:
                new_products.append({})
            new_products[X].update(new_item)
    
    # add the new "products" key to the JSON object
    json_obj["products"] = new_products
    return json_obj


@logger.catch
def verify_signature(check_signature, check_data, *args, transformation_needed):
    if transformation_needed:
        check_data = transform_json(check_data)
    
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
    pass
    # stupid_data = {'date': '2023-05-03T17:49:30+03:00', 'order_id': '12132945', 'order_num':
    #     'fba821e5-275f-480d-aae3-df448dd58014', 'domain': 'testpage3.payform.ru', 'sum': '2000.00', 'currency': 'rub',
    #                'customer_phone': '+375297861654', 'customer_extra': 'Полная оплата курса', 'payment_type':
    #                'Оплата картой, выпущенной в РФ', 'commission': '3.5', 'commission_sum': '70.00', 'attempt': '1',
    #                'products[0][name]':
    #                    'Обучающие материалы', 'products[0][price]': '2000.00', 'products[0][quantity]': '1',
    #                'products[0][sum]':
    #                    '2000.00', 'payment_status': 'success', 'payment_status_description': 'Успешная оплата',
    #                'payment_init': 'manual'}
    
