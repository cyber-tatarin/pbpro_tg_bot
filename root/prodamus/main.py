from root.db import setup as db
from root.db import models
from .utils import verify_signature
from root.tg.main import payment_confirmed

from root.logger.log import get_logger


logger = get_logger()


@logger.catch
async def confirm_payment(signature, data):
    # if verify_signature(signature, data):
    if float(data['sum']) >= 2000 and data['payment_status'] == 'success':
        logger.info('prodamus/confirm_payment')
        session = db.Session()
        user = session.query(models.User).filter(models.User.order_id == data['order_num']).first()
        if user:
            user.have_paid = True
            session.commit()
            session.refresh(user)
            if session.is_active:
                session.close()
            await payment_confirmed(user.client_tg_id)
            return
        return
    return


        