import os

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from dotenv import load_dotenv, find_dotenv
from aiogram.types import CallbackQuery
from aiogram import Bot, Dispatcher, executor, types

import keyboards
import callback_data_models
from texts import TASKS, WELCOME_MESSAGE, PAYMENT_LINK_MESSAGE
from ..db import setup as db
from ..db import models
import utils

load_dotenv(find_dotenv())

bot = Bot(os.getenv('TG_API'))
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

ADMIN_ID = 459471362


class TaskStates(StatesGroup):
    input_phone_number = State()
    task_is_done = State()
    send_comment_after_accept = State()
    send_comment_after_decline = State()


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message):
    print('start')
    await message.answer(WELCOME_MESSAGE)
    # reply_markup=keyboards.get_ikb_to_send_payment_link())
    await message.delete()
    await TaskStates.input_phone_number.set()


@dp.message_handler(state=TaskStates.input_phone_number)
async def send_payment_link(message: types.Message, state: FSMContext):
    # link = generate_payment_link(message.text, message.from_user.id)
    await message.answer(PAYMENT_LINK_MESSAGE,
                         reply_markup=keyboards.get_ikb_to_send_payment_link(message.text, message.from_user.id))
    await state.finish()


@dp.callback_query_handler(callback_data_models.send_task_cb_data.filter())
async def send_task(callback_query: CallbackQuery, callback_data: dict):
    print('send_task')
    task_number = callback_data['task_number']
    
    await bot.send_message(callback_query.from_user.id, TASKS[task_number])
    await TaskStates.task_is_done.set()
    await callback_query.message.edit_reply_markup(reply_markup=None)
    
    await callback_query.answer(cache_time=0)


@dp.message_handler(state=TaskStates.task_is_done, content_types=['any'])
async def check_task(message: types.Message, state: FSMContext):
    print('check')
    
    # data = await state.get_data()
    # task_number = data['current_task_number']
    session = db.Session()
    task_number = session.query(models.Task).filter(
        models.Task.client_tg_id == message.from_user.id).first().current_task
    session.close()
    
    message_for_admin = f'Задание #{task_number} от пользователя {message.from_user.full_name}:'
    
    # await bot.send_message(ADMIN_ID, message_for_admin)
    # await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id,
    #                        message_id=message.message_id,
    #                        reply_markup=keyboards.get_ikb_to_check_users_tasks(message.from_user.id,
    #                                                                            message.message_id))
    # await bot.send_message(ADMIN_ID, '---------------------')
    
    reply_markup = keyboards.get_ikb_to_check_users_tasks(message.from_user.id)
    await utils.send_and_copy_message(bot, ADMIN_ID, message, message_for_admin, reply_markup)
    await state.finish()


@dp.callback_query_handler(callback_data_models.accept_task_with_comment_cb_data.filter())
async def accept_task_with_comment(callback_query: CallbackQuery, callback_data: dict):
    print('inside')
    
    receiver_id = callback_data['receiver_id']
    user = await bot.get_chat(receiver_id)
    msg = await callback_query.message.answer(f'Вы приняли решение пользователя {user.full_name}, дайте комментарий',
                                              reply_markup=keyboards.get_ikb_to_cancel_state())
    await TaskStates.send_comment_after_accept.set()
    
    state = dp.get_current().current_state()
    await state.update_data(receiver_id=receiver_id,
                            cancel_message=msg['message_id'],
                            chat_id=msg['chat']['id'])
    await callback_query.answer(cache_time=0)


@dp.callback_query_handler(callback_data_models.decline_task_with_comment_cb_data.filter())
async def decline_task_with_comment(callback_query: CallbackQuery, callback_data: dict):
    print('inside')
    
    receiver_id = callback_data['receiver_id']
    user = await bot.get_chat(receiver_id)
    msg = await callback_query.message.answer(f'Вы отклонили решение пользователя {user.full_name}, дайте комментарий',
                                              reply_markup=keyboards.get_ikb_to_cancel_state())
    await TaskStates.send_comment_after_decline.set()
    
    state = dp.get_current().current_state()
    await state.update_data(receiver_id=receiver_id,
                            cancel_message=msg['message_id'],
                            chat_id=msg['chat']['id'])
    await callback_query.answer(cache_time=0)


@dp.message_handler(state=TaskStates.send_comment_after_accept, content_types=['any'])
async def send_comment_after_accept(message: types.Message, state: FSMContext):
    print('send com')
    
    data = await state.get_data()
    receiver_id = data['receiver_id']
    cancel_message_id = data['cancel_message']
    chat_id = data['chat_id']
    await bot.delete_message(chat_id, cancel_message_id)
    
    session = db.Session()
    task = session.query(models.Task).filter(models.Task.client_tg_id == receiver_id).first()
    task.current_task += 1
    task_number = task.current_task
    session.commit()
    if session.is_active:
        session.close()
    
    message_for_client = f'Вот ответ от Вашего ментора:'
    
    if task_number > len(TASKS):
        await utils.send_and_copy_message(bot, receiver_id, message, message_for_client)
        # await bot.send_message(receiver_id, message_for_client, reply_to_message_id=message_id)
        await bot.send_message(receiver_id, 'Ура, Вы выполнили все задания!')
    else:
        reply_markup = keyboards.get_ikb_to_get_task(str(task_number))
        await utils.send_and_copy_message(bot, receiver_id, message, message_for_client, reply_markup=reply_markup)
        # await bot.copy_message(chat_id=receiver_id, from_chat_id=message.chat.id, message_id=message.message_id,
        #                        reply_to_message_id=message_id,
        #                        reply_markup=keyboards.get_ikb_to_get_task(str(task_number)))
    
    await state.finish()


@dp.message_handler(state=TaskStates.send_comment_after_decline, content_types=['any'])
async def send_comment_after_decline(message: types.Message, state: FSMContext):
    print('send com')
    
    data = await state.get_data()
    receiver_id = data['receiver_id']
    cancel_message_id = data['cancel_message']
    chat_id = data['chat_id']
    await bot.delete_message(chat_id, cancel_message_id)
    
    message_for_client = f'Ваше решение не приняли. Вот ответ от Вашего ментора:'
    
    await utils.send_and_copy_message(bot, receiver_id, message, message_for_client)
    # await bot.send_message(receiver_id, message_for_client, reply_to_message_id=message_id)
    await bot.send_message(receiver_id, 'Следующим сообщением отправьте, пожалуйста, новое решение')
    
    receiver_state = dp.current_state(user=receiver_id)
    await receiver_state.set_state(TaskStates.task_is_done.state)
    
    # await utils.send_and_copy_message(bot, receiver_id, message, message_for_client, reply_markup=reply_markup)
    # await bot.copy_message(chat_id=receiver_id, from_chat_id=message.chat.id, message_id=message.message_id,
    #                        reply_to_message_id=message_id,
    #                        reply_markup=keyboards.get_ikb_to_get_task(str(task_number)))
    
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'send_payment_link')
async def send_payment_link(callback_query: CallbackQuery):
    print('send')
    
    await bot.send_message(callback_query.from_user.id, 'link')
    
    # task = models.Task(client_tg_id=callback_query.from_user.id, current_task=1)
    # session = db.Session()
    # try:
    #     session.add(task)
    #     session.commit()
    # except Exception as x:
    #     print(x)
    # finally:
    #     if session.is_active:
    #         session.close()
    
    # state = dp.current_state(user=callback_query.from_user.id)
    # await state.update_data(current_task_number='1')
    # print(state.get_data())
    
    await callback_query.message.edit_reply_markup(reply_markup=None)
    
    await callback_query.answer(cache_time=0)


@dp.callback_query_handler(lambda c: c.data == 'drop_state', state='*')
async def drop_state(callback_query: CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.finish()
    await callback_query.message.delete()
    await callback_query.answer('Действие отменено')
    

@dp.message_handler(commands=['gettask'])
async def payment_confirmed_test(message: types.Message):
    task = models.Task(client_tg_id=message.from_user.id, current_task=1)
    session = db.Session()
    print('gogo')
    try:
        session.add(task)
        session.commit()
    except Exception as x:
        print(x)
    finally:
        if session.is_active:
            session.close()
    
    await message.answer('Оплата прошла успешно, Вы готовы получить первое задание?',
                         reply_markup=keyboards.get_ikb_to_get_task('1'))


async def payment_confirmed(user_id):
    task = models.Task(client_tg_id=user_id, current_task=1)
    session = db.Session()
    try:
        session.add(task)
        session.commit()
    except Exception as x:
        print(x)
    finally:
        if session.is_active:
            session.close()
    
    await bot.send_message(user_id, 'Оплата прошла успешно, Вы готовы получить первое задание?',
                           reply_markup=keyboards.get_ikb_to_get_task('1'))


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True)
