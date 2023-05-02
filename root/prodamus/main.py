import logging

from root.db import setup as db
from root.db import models
from .utils import verify_signature
from root.tg.main import payment_confirmed

import logging

# Set up logging
logging.basicConfig(
    filename='bot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def confirm_payment(signature, data):
    if verify_signature(signature, data):
        if int(data['sum']) >= 2000 and data['payment_status'] == 'success':
            logging.info('we are in verify')
            session = db.Session()
            user = session.query(models.User).filter(models.User.order_id == data['order_num']).first()
            user.have_paid = True
            session.commit()
            if session.is_active:
                session.close()
            await payment_confirmed(user.client_tg_id)
        