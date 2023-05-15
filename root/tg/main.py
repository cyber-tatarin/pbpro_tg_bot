import asyncio
import os
import sys

from sqlalchemy.exc import IntegrityError

sys.path.append(os.path.abspath(os.path.pardir))

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from dotenv import load_dotenv, find_dotenv
from aiogram.types import CallbackQuery
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import ChatNotFound
from sqlalchemy.orm import sessionmaker

from keyboards import *
import callback_data_models
import utils
from root.db import setup as db
from root.db import models
from root.gsheets import main as gsh

from root.logger.log import logger

logger = logger

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


async def save_state_into_db(user_id, state):
    session = db.Session()
    try:
        state_db_object = models.State(client_tg_id=user_id, current_state=state)
        session.add(state_db_object)
        session.commit()
    except IntegrityError:
        session.rollback()
        existing_state = session.query(models.State).filter(models.State.client_tg_id == user_id).first()
        existing_state.current_state = state
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()


async def delete_state_from_db(user_id):
    session = db.Session()
    try:
        existing_state = session.query(models.State).filter(models.State.client_tg_id == user_id).first()
        session.delete(existing_state)
        session.commit()
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()


@logger.catch
@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message):
    session = db.Session()
    try:
        WELCOME_MESSAGE = session.query(models.Text).filter(models.Text.id == 91).first().text
        await message.answer(WELCOME_MESSAGE)
    except Exception as x:
        logger.exception(x)
        await message.answer('У нас проблемы с базой данных. Если ты видишь это сообщение, '
                             'напиши, пожалуйста, мне @dimatatatarin')
        return
    finally:
        if session.is_active:
            session.close()
    
    await message.delete()
    await TaskStates.input_phone_number.set()
    await save_state_into_db(message.from_user.id, 'TaskStates:input_phone_number')


@logger.catch
@dp.message_handler(state='*', commands=['help'])
async def help_command(message: types.Message):
    await message.delete()
    await message.answer('Если появилась какая-то проблема, напиши мне @dimatatatarin. Мы все решим :)')
    await message.answer(f'Вот Ваш ID:')
    await message.answer(message.from_user.id)
    await message.answer('Он может понадобиться для решения проблемы')


@logger.catch
@dp.message_handler(state='*', commands=['checkpayment'])
async def check_payment_command(message: types.Message):
    await message.delete()
    answer_message = 'Пока твоя оплата не пришла. Ожидание оплаты может доходить до 15 минут. ' \
                     'Но не переживай, мы обязательно разберемся, даже если что-то пошло не так\n' \
                     'Нажми на /help, если Вам нужна дополнительная помощь'
    
    try:
        session = db.Session()
        user = session.query(models.User).filter(models.User.client_tg_id == message.from_user.id).first()
        if user.have_paid:
            await payment_confirmed(message.from_user.id)
        else:
            await message.answer(answer_message)
    except Exception as x:
        await message.answer(answer_message)
        logger.exception(x)


@logger.catch
@dp.message_handler(state='*', commands=['getpaymentlink'])
async def send_payment_link_manually(message: types.Message):
    session = db.Session()
    try:
        GET_PAYMENT_LINK_MANUALLY = session.query(models.Text).filter(models.Text.id == 92).first().text
    
    except Exception as x:
        logger.exception(x)
        await message.answer('У нас проблемы с базой данных. Если ты видишь это сообщение, '
                             'напиши, пожалуйста, мне @dimatatatarin')
        return
    finally:
        if session.is_active:
            session.close()
    
    await message.answer(GET_PAYMENT_LINK_MANUALLY)
    await message.delete()
    await TaskStates.input_phone_number.set()
    await save_state_into_db(message.from_user.id, 'TaskStates:input_phone_number')


@logger.catch
@dp.message_handler(state=TaskStates.input_phone_number)
async def send_payment_link(message: types.Message, state: FSMContext):
    session = db.Session()
    try:
        PAYMENT_LINK_MESSAGE = session.query(models.Text).filter(models.Text.id == 93).first().text
    except Exception as x:
        logger.exception(x)
        await message.answer('У нас проблемы с базой данных. Если ты видишь это сообщение, '
                             'напиши, пожалуйста, мне @dimatatatarin')
        return
    finally:
        if session.is_active:
            session.close()
    
    try:
        await message.answer(PAYMENT_LINK_MESSAGE,
                             reply_markup=get_ikb_to_send_payment_link(message.text, message.from_user.id))
    except Exception as x:
        logger.exception(x)
    await state.finish()
    await delete_state_from_db(message.from_user.id)
    loop = asyncio.get_event_loop()
    loop.create_task(gsh.async_got_link(message.from_user.id, message.from_user.full_name, message.from_user.username))
    
    # await gsh.async_got_link(message.from_user.id, message.from_user.full_name, message.from_user.username)


@logger.catch
@dp.callback_query_handler(callback_data_models.send_task_cb_data.filter())
async def send_task(callback_query: CallbackQuery, callback_data: dict):
    task_number = callback_data['task_number']
    
    session = db.Session()
    try:
        TASK = session.query(models.Text).filter(models.Text.id == task_number).first().text
    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               'У нас проблемы с базой данных. Если ты видишь это сообщение, '
                               'напиши, пожалуйста, мне @dimatatatarin')
        return
    finally:
        if session.is_active:
            session.close()
    
    await bot.send_message(callback_query.from_user.id, TASK)
    await TaskStates.task_is_done.set()
    
    await callback_query.message.edit_reply_markup(reply_markup=None)
    
    await save_state_into_db(callback_query.from_user.id, 'TaskStates:task_is_done')
    await callback_query.answer(cache_time=0)
    loop = asyncio.get_event_loop()
    loop.create_task(gsh.async_on_task(callback_query.from_user.id, task_number))
    
    # await gsh.async_on_task(callback_query.from_user.id, task_number)


@logger.catch
@dp.message_handler(state=TaskStates.task_is_done, content_types=['any'])
async def check_task(message: types.Message, state: FSMContext):
    session = db.Session()
    task_number = session.query(models.Task).filter(
        models.Task.client_tg_id == message.from_user.id).first().current_task
    session.close()
    
    message_for_admin = f'Задание #{task_number} от пользователя {message.from_user.full_name}:'
    
    reply_markup = get_ikb_to_check_users_tasks(message.from_user.id)
    await utils.send_and_copy_message(bot, ADMIN_ID, message, message_for_admin, reply_markup)
    await message.answer('Твое задание отправлено на проверку. Ты получишь ответ, как только задание будет проверено')
    await state.finish()
    await delete_state_from_db(message.from_user.id)


@logger.catch
@dp.callback_query_handler(callback_data_models.accept_task_cb_data.filter())
async def accept_task(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']
    
    session = db.Session()
    task = session.query(models.Task).filter(models.Task.client_tg_id == receiver_id).first()
    task.current_task += 1
    task_number = task.current_task
    session.commit()
    if session.is_active:
        session.close()
    
    session = db.Session()
    try:
        number_of_tasks_query = session.query(models.Text).filter(models.Text.id < 50)
        number_of_tasks = number_of_tasks_query.count()
    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               'У нас проблемы с базой данных. Если ты видишь это сообщение, '
                               'напиши, пожалуйста, мне @dimatatatarin')
        return
    finally:
        if session.is_active:
            session.close()
    
    if task_number > number_of_tasks:
        await bot.send_message(receiver_id, 'Ваше задание приняли!')
        await bot.send_message(receiver_id, 'Ура, все задания выполнены!')
    else:
        reply_markup = get_ikb_to_get_task(str(task_number))
        await bot.send_message(receiver_id, 'Твое задание приняли! Хочешь получить следующее?',
                               reply_markup=reply_markup)
    
    await bot.edit_message_reply_markup(ADMIN_ID, callback_query.message.message_id, reply_markup=None)
    await callback_query.answer(cache_time=0)


@logger.catch
@dp.callback_query_handler(callback_data_models.decline_task_cb_data.filter())
async def decline_task(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']
    
    await bot.send_message(receiver_id, 'Твое задание не приняли, комментарий не дали.',
                           reply_markup=get_ikb_to_resend_declined_answer())
    await bot.edit_message_reply_markup(ADMIN_ID, callback_query.message.message_id, reply_markup=None)
    await callback_query.answer(cache_time=0)


@logger.catch
@dp.callback_query_handler(callback_data_models.accept_task_with_comment_cb_data.filter())
async def accept_task_with_comment(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']
    user = await bot.get_chat(receiver_id)
    
    msg = await callback_query.message.answer(f'Вы приняли решение пользователя {user.full_name}, дайте комментарий',
                                              reply_markup=get_ikb_to_cancel_state())
    await TaskStates.send_comment_after_accept.set()
    
    state = dp.get_current().current_state()
    await state.update_data(receiver_id=receiver_id,
                            cancel_message=msg['message_id'],
                            chat_id=msg['chat']['id'],
                            answer_message=callback_query.message.message_id)
    
    await callback_query.answer(cache_time=0)


@logger.catch
@dp.callback_query_handler(callback_data_models.decline_task_with_comment_cb_data.filter())
async def decline_task_with_comment(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']
    user = await bot.get_chat(receiver_id)
    
    msg = await callback_query.message.answer(f'Вы отклонили решение пользователя {user.full_name}, дайте комментарий',
                                              reply_markup=get_ikb_to_cancel_state())
    await TaskStates.send_comment_after_decline.set()
    
    state = dp.get_current().current_state()
    await state.update_data(receiver_id=receiver_id,
                            cancel_message=msg['message_id'],
                            chat_id=msg['chat']['id'],
                            answer_message=callback_query.message.message_id)
    
    await callback_query.answer(cache_time=0)


@logger.catch
@dp.message_handler(state=TaskStates.send_comment_after_accept, content_types=['any'])
async def send_comment_after_accept(message: types.Message, state: FSMContext):
    data = await state.get_data()
    receiver_id = data['receiver_id']
    cancel_message_id = data['cancel_message']
    chat_id = data['chat_id']
    answer_message_id = data['answer_message']
    
    await bot.delete_message(chat_id, cancel_message_id)
    
    session = db.Session()
    task = session.query(models.Task).filter(models.Task.client_tg_id == receiver_id).first()
    task.current_task += 1
    task_number = task.current_task
    session.commit()
    if session.is_active:
        session.close()
    
    message_for_client = f'Вот ответ от твоего ментора:'
    session = db.Session()
    try:
        number_of_tasks_query = session.query(models.Text).filter(models.Text.id < 50)
        number_of_tasks = number_of_tasks_query.count()
    except Exception as x:
        logger.exception(x)
        await bot.send_message(message.from_user.id,
                               'У нас проблемы с базой данных. Если ты видишь это сообщение, '
                               'напиши, пожалуйста, мне @dimatatatarin')
        return
    finally:
        if session.is_active:
            session.close()
    
    if task_number > number_of_tasks:
        await utils.send_and_copy_message(bot, receiver_id, message, message_for_client,
                                          divider=False)
        await bot.send_message(receiver_id, 'Ура! Все задания выполнены!')
    else:
        reply_markup = get_ikb_to_get_task(str(task_number))
        await utils.send_and_copy_message(bot, receiver_id, message, message_for_client,
                                          reply_markup=reply_markup, divider=False)
    
    await bot.edit_message_reply_markup(ADMIN_ID, answer_message_id, reply_markup=None)
    await state.finish()


@logger.catch
@dp.message_handler(state=TaskStates.send_comment_after_decline, content_types=['any'])
async def send_comment_after_decline(message: types.Message, state: FSMContext):
    data = await state.get_data()
    receiver_id = data['receiver_id']
    cancel_message_id = data['cancel_message']
    chat_id = data['chat_id']
    answer_message_id = data['answer_message']
    
    await bot.delete_message(chat_id, cancel_message_id)
    
    message_for_client = f'Твое решение не приняли. Вот ответ от ментора:'
    
    await utils.send_and_copy_message(bot, receiver_id, message, message_for_client,
                                      reply_markup=get_ikb_to_resend_declined_answer(), divider=False)
    
    await bot.edit_message_reply_markup(ADMIN_ID, answer_message_id, reply_markup=None)
    await state.finish()


@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'resend_declined_answer')
async def resend_declined_answer(callback_query: CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await TaskStates.task_is_done.set()
    await save_state_into_db(callback_query.from_user.id, 'TaskStates:task_is_done')


@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'drop_state', state='*')
async def drop_state(callback_query: CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.finish()
    await callback_query.message.delete()
    await callback_query.answer('Действие отменено')
    
    await delete_state_from_db(callback_query.from_user.id)


@logger.catch
async def payment_confirmed(user_id):
    try:
        task = models.Task(client_tg_id=user_id, current_task=1)
        # task = models.Task(current_tg_id=user_id, current_task=1)
        session = db.Session()
        try:
            session.add(task)
            session.commit()
            # await bot.send_message(user_id, 'Оплата прошла успешно, Вы готовы получить первое задание?',
            #                        reply_markup=get_ikb_to_get_task('1'))
            
            await bot.send_message(user_id,
                                   'Оплата прошла успешно! Вот твоя персональная ссылка в закрытый чат марафона: https://t.me/+z3KnjLUsgsw0YTYy\n '
                                   'Уже 22 мая ты получишь свое первое задание. Будь на связи!')
        
        except IntegrityError as x:
            await bot.send_message(user_id, 'Ты уже получал задание задание')
        except Exception as x:
            logger.exception(x)
            await bot.send_message(user_id, 'У нас проблемы с базой данных. Если ты видишь это сообщение, '
                                            'напиши, пожалуйста, мне @dimatatatarin')
        finally:
            if session.is_active:
                session.close()
    except ChatNotFound:
        pass


async def send_message_to_users_manually(user_ids_list: list, message):
    for user_id in user_ids_list:
        try:
            await bot.send_message(user_id, message)
        except ChatNotFound as x:
            logger.exception(x)


async def send_task_to_user_manually(user_id, task_number):
    # await bot.send_message(user_id, TASKS[task_number])
    # await dp.current_state(user=user_id).set_state('TaskStates:task_is_done')
    # # await storage.set_state(user=user_id, state='TaskStates:task_is_done', chat=user_id)
    #
    # await save_state_into_db(user_id, 'TaskStates:task_is_done')
    # loop = asyncio.get_event_loop()
    # loop.create_task(gsh.async_on_task(user_id, task_number))
    
    reply_markup = get_ikb_to_get_task(str(task_number))
    await bot.send_message(user_id, 'Нажми кнопку ниже, чтобы получить задание',
                           reply_markup=reply_markup)
    
    task = models.Task(client_tg_id=user_id, current_task=task_number)
    session = db.Session()
    try:
        session.add(task)
        session.commit()
    except IntegrityError as x:
        pass
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()


# Define a function to restore the user states from the database
async def restore_user_states():
    session = db.Session()
    try:
        for row in session.query(models.State).all():
            await storage.set_state(user=row.client_tg_id, state=row.current_state, chat=row.client_tg_id)
        session.query(models.State).delete()
        session.commit()
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()


async def on_startup(_):
    await restore_user_states()


if __name__ == '__main__':
    with logger.catch():
        executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=on_startup)
