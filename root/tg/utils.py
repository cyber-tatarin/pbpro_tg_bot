from root.db import setup as db
from root.db import models
from sqlalchemy.exc import IntegrityError
import uuid

from root.logger.log import logger

logger = logger


async def send_and_copy_message(bot, receiver_id, message, extra_message, reply_markup=None, divider=True):
    await bot.send_message(receiver_id, extra_message)
    await bot.copy_message(chat_id=receiver_id, from_chat_id=message.chat.id,
                           message_id=message.message_id,
                           reply_markup=reply_markup)
    if divider:
        await bot.send_message(receiver_id, '------------------------------------')


@logger.catch
def generate_payment_link(phone_number, client_tg_id):
    order_id = str(uuid.uuid4())
    user = models.User(client_tg_id=client_tg_id, order_id=order_id)
    session = db.Session()
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        user = session.query(models.User).filter(models.User.client_tg_id == client_tg_id).first()
        user.order_id = order_id
        session.commit()

    if session.is_active:
        session.close()
    
    link = f'https://pbacademy.payform.ru/' \
           f'?order_id={order_id}' \
           f'&customer_phone={phone_number}' \
           f'&products[0][price]=800' \
           f'&products[0][quantity]=1' \
           f'&products[0][name]=Марафон %22Деньги в строительстве%22' \
           f'&customer_extra=Полная оплата марафона' \
           f'&do=pay'
    
    # link = f'https://testpage3.payform.ru/' \
    #        f'?order_id={order_id}' \
    #        f'&customer_phone={phone_number}' \
    #        f'&products[0][price]=800' \
    #        f'&products[0][quantity]=1' \
    #        f'&products[0][name]=Марафон %22Деньги в строительстве%22' \
    #        f'&customer_extra=Полная оплата марафона' \
    #        f'&do=pay'

    return link.replace(' ', '%20')
