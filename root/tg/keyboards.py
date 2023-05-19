from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import utils
import callback_data_models
from root.logger.log import logger

logger = logger


@logger.catch
def get_ikb_to_get_task(task_number):
    ikb_to_get_task = InlineKeyboardMarkup(row_width=1)
    b1 = InlineKeyboardButton(text=f'Получить задание #{task_number}',
                              callback_data=callback_data_models.send_task_cb_data.new(task_number))
    ikb_to_get_task.add(b1)
    return ikb_to_get_task


@logger.catch
def get_ikb_to_check_users_tasks(user_id):
    ikb_to_check_users_tasks = InlineKeyboardMarkup(row_width=1)
    b1 = InlineKeyboardButton(text='Принять решение и дать комментарий',
                              callback_data=callback_data_models.accept_task_with_comment_cb_data.new(user_id))
    b2 = InlineKeyboardButton(text='Принять решение без комментария',
                              callback_data=callback_data_models.accept_task_cb_data.new(user_id))
    b3 = InlineKeyboardButton(text='Отклонить решение и дать комментарий',
                              callback_data=callback_data_models.decline_task_with_comment_cb_data.new(user_id))
    b4 = InlineKeyboardButton(text='Отклонить решение без комментария',
                              callback_data=callback_data_models.decline_task_cb_data.new(user_id))
    ikb_to_check_users_tasks.add(b1, b2, b3, b4)
    return ikb_to_check_users_tasks


@logger.catch
def get_ikb_to_send_payment_link(phone_number, user_id):
    logger.info('inside send pm link')
    ikb_to_send_payment_link = InlineKeyboardMarkup()
    link = utils.generate_payment_link(phone_number, user_id)
    logger.info('after creating link')
    b1 = InlineKeyboardButton(text='Оплатить', url=link)
    ikb_to_send_payment_link.add(b1)
    return ikb_to_send_payment_link


@logger.catch
def get_ikb_to_cancel_state():
    ikb_to_drop_state = InlineKeyboardMarkup(row_width=1)
    b1 = InlineKeyboardButton(text='Отменить',
                              callback_data='drop_state')
    ikb_to_drop_state.add(b1)
    return ikb_to_drop_state


@logger.catch
def get_ikb_to_resend_declined_answer():
    ikb_to_resend_declined_answer = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton(text='Попробовать еще раз',
                              callback_data='resend_declined_answer')
    ikb_to_resend_declined_answer.add(b1)
    return ikb_to_resend_declined_answer


@logger.catch
def get_ikb_to_choose_payment_card():
    ikb_to_choose_payment_card = InlineKeyboardMarkup(row_width=1)
    b1 = InlineKeyboardButton(text='Российская карта', callback_data='rus_card')
    b2 = InlineKeyboardButton(text='Белорусская карта', callback_data='bel_card')
    ikb_to_choose_payment_card.add(b1, b2)
    return ikb_to_choose_payment_card


@logger.catch
def get_ikb_to_confirm_bel_card_payment(user_id):
    ikb_to_check_users_tasks = InlineKeyboardMarkup(row_width=1)
    b1 = InlineKeyboardButton(text='Принять оплату и дать доступ',
                              callback_data=callback_data_models.confirm_bel_card_payment_cb_data.new(user_id))
    ikb_to_check_users_tasks.add(b1)
    return ikb_to_check_users_tasks
    
