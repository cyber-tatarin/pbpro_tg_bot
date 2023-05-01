import db.setup as db
import db.models as models
from utils import verify_signature
from tg.main import payment_confirmed


def confirm_payment(signature, data):
    if verify_signature(signature, data):
        if int(data['sum']) >= 2000 and data['payment_status'] == 'success':
            session = db.Session()
            user = session.query(models.User).filter(models.User.order_id==data['order_num']).first()
            session.close()
            payment_confirmed(user.client_tg_id)
        