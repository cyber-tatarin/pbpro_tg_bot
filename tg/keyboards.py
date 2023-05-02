import os.path

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import callback_data_models
import sys
import os

from prodamus import utils


def get_ikb_to_get_task(task_number):
    ikb_to_get_task = InlineKeyboardMarkup(row_width=1)
    b1 = InlineKeyboardButton(text=f'Получить задание #{task_number}',
                              callback_data=callback_data_models.send_task_cb_data.new(task_number))
    ikb_to_get_task.add(b1)
    return ikb_to_get_task


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


def get_ikb_to_send_payment_link(phone_number, user_id):
    ikb_to_send_payment_link = InlineKeyboardMarkup()
    link = utils.generate_payment_link(phone_number, user_id)
    b1 = InlineKeyboardButton(text='Оплатить', url=link)
    ikb_to_send_payment_link.add(b1)
    return ikb_to_send_payment_link


def get_ikb_to_cancel_state():
    ikb_to_drop_state = InlineKeyboardMarkup(row_width=1)
    b1 = InlineKeyboardButton(text='Отменить',
                              callback_data='drop_state')
    ikb_to_drop_state.add(b1)
    return ikb_to_drop_state
