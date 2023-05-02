import hashlib
import json
import hmac
import os
import uuid
from collections.abc import MutableMapping
from dotenv import load_dotenv, find_dotenv
from ..db import setup as db
from ..db import models
from sqlalchemy.exc import IntegrityError


load_dotenv(find_dotenv())


def generate_payment_link(phone_number, client_tg_id):
    order_id = str(uuid.uuid4())
    user = models.User(client_tg_id=client_tg_id, order_id=order_id)
    session = db.Session()
    session.add(user)
    
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        user = session.query(models.User).filter(models.User.client_tg_id==client_tg_id).first()
        user.order_id = order_id
        session.commit()
        
    if session.is_active:
        session.close()
    
    link = f'https://testpage3.payform.ru/' \
    f'?order_id={order_id}' \
    f'&customer_phone={phone_number}' \
    f'&products[0][price]=2000' \
    f'&products[0][quantity]=1' \
    f'&products[0][name]=Обучающие материалы' \
    f'&customer_extra=Полная оплата курса' \
    f'&do=pay'
    
    return link.replace(' ', '%20')


def generate_signature(data):

    # переводим все значения data в string c помощью кастомной функции deep_int_to_string (см ниже)
    deep_int_to_string(data)

    # переводим data в JSON, с сортировкой ключей в алфавитном порядке, без пробелов и экранируем бэкслеши
    data_json = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).replace("/", "\\/")

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
            

def verify_signature(check_signature, data):
    benchmark_signature = generate_signature(data)
    if benchmark_signature == check_signature:
        return True
    else:
        return False
            