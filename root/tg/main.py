import asyncio
import os
import sys

from sqlalchemy.exc import IntegrityError

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from dotenv import load_dotenv, find_dotenv
from aiogram.types import CallbackQuery
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import ChatNotFound
from sqlalchemy.orm import sessionmaker

from .keyboards import *
from . import callback_data_models, utils
from root.db import setup as db
from root.db import models
from root.gsheets import main as gsh

from root.logger.log import logger

logger = logger

load_dotenv(find_dotenv())

bot = Bot(os.getenv('TG_API'))
storage = MemoryStorage()

dp = Dispatcher(bot=bot, storage=storage)

# ADMIN_ID = 459471362
# ADMIN_ID = [899761612]
# ADMIN_ID = [1357642007, 459471362]
ADMIN_ID = [1287712867, 899761612]

database_error_message = 'У нас проблемы с базой данных. Если ты видишь это сообщение, ' \
                         'напиши, пожалуйста, мне @dimatatatarin'


class TaskStates(StatesGroup):
    input_phone_number = State()
    task_is_done = State()
    send_comment_after_accept = State()
    send_comment_after_decline = State()
    transfer_to_bel_card_is_done = State()


async def save_state_into_db(user_id, state):
    session = db.Session()
    try:
        state_db_object = models.State(client_tg_id=user_id, current_state=state)
        session.add(state_db_object)
        session.commit()
    except IntegrityError:
        session.rollback()
        existing_state = session.query(models.State).filter(models.State.client_tg_id == str(user_id)).first()
        existing_state.current_state = state
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()


async def delete_state_from_db(user_id):
    session = db.Session()
    try:
        existing_state = session.query(models.State).filter(models.State.client_tg_id == str(user_id)).first()
        session.delete(existing_state)
        session.commit()
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()


async def remove_keyboard_to_check_task(receiver_id, current_task, session):
    not_checked_task_objs = session.query(models.NotCheckedTask).filter(
        models.NotCheckedTask.receiver_id == str(receiver_id),
        models.NotCheckedTask.task_number == str(current_task)).all()
    
    for not_checked_task_obj in not_checked_task_objs:
        await bot.edit_message_reply_markup(not_checked_task_obj.admin_id, not_checked_task_obj.message_id,
                                            reply_markup=None)


def remove_not_checked_tasks_from_db(receiver_id, current_task, session):
    not_checked_task_objs = session.query(models.NotCheckedTask).filter(
        models.NotCheckedTask.receiver_id == str(receiver_id),
        models.NotCheckedTask.task_number == str(current_task)).all()
    
    for not_checked_task_obj in not_checked_task_objs:
        session.delete(not_checked_task_obj)
        

@logger.catch
@dp.message_handler(state='*', commands=['start', 'getpaymentlink'])
async def start(message: types.Message):
    session = db.Session()
    try:
        choose_card_message = session.query(models.Text).filter(models.Text.id == 91).first().text
        await message.answer(choose_card_message, reply_markup=get_ikb_to_choose_payment_card())
    except Exception as x:
        logger.exception(x)
        await message.answer(database_error_message)
        await message.delete()
    finally:
        if session.is_active:
            session.close()
    

@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'bel_card', state='*')
async def send_card_number(callback_query: CallbackQuery):
    await callback_query.message.answer('Вот номер карты:')
    await callback_query.message.answer('5442064534170965')
    await callback_query.message.answer('Переведи на эту карту $10 по курсу и отправь скриншот в этот чат. '
                                        'Ты получишь доступ, как только твоя оплата будет подтверждена администратором')
    
    await callback_query.answer()
    await TaskStates.transfer_to_bel_card_is_done.set()
    await save_state_into_db(callback_query.from_user.id, 'TaskStates:transfer_to_bel_card_is_done')
    
    loop = asyncio.get_event_loop()
    loop.create_task(gsh.async_got_link(callback_query.from_user.id,
                                        callback_query.from_user.full_name,
                                        callback_query.from_user.username))


@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'rus_card', state='*')
async def get_phone_number_for_payment_link(callback_query: CallbackQuery):
    session = db.Session()
    try:
        get_phone_number_message = session.query(models.Text).filter(models.Text.id == 92).first().text
        await callback_query.message.answer(get_phone_number_message)
    except Exception as x:
        logger.exception(x)
        await callback_query.message.answer(database_error_message)
        await callback_query.answer()
        return
    finally:
        if session.is_active:
            session.close()
            
    await TaskStates.input_phone_number.set()
    await save_state_into_db(callback_query.from_user.id, 'TaskStates:input_phone_number')


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

    session = db.Session()
    try:
        user = session.query(models.User).filter(models.User.client_tg_id == str(message.from_user.id)).first()
        if user.have_paid:
            await payment_confirmed(message.from_user.id)
        else:
            await message.answer(answer_message)
    except Exception as x:
        await message.answer(answer_message)
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()


# @logger.catch
# @dp.message_handler(state='*', commands=['getpaymentlink'])
# async def get_payment_link(message: types.Message):
#     session = db.Session()
#     try:
#         CHOOSE_CARD_MESSAGE = session.query(models.Text).filter(models.Text.id == 91).first().text
#         await message.answer(CHOOSE_CARD_MESSAGE, reply_markup=get_ikb_to_choose_payment_card())
#     except Exception as x:
#         logger.exception(x)
#         await message.answer('У нас проблемы с базой данных. Если ты видишь это сообщение, '
#                              'напиши, пожалуйста, мне @dimatatatarin')
#         return
#     finally:
#         if session.is_active:
#             session.close()
#
#     await message.delete()


@logger.catch
@dp.message_handler(state=TaskStates.input_phone_number)
async def send_payment_link(message: types.Message, state: FSMContext):
    session = db.Session()
    try:
        payment_link_message = session.query(models.Text).filter(models.Text.id == 93).first().text
    except Exception as x:
        logger.exception(x)
        await message.answer(database_error_message)
        return
    finally:
        if session.is_active:
            session.close()
    
    try:
        await message.answer(payment_link_message,
                             reply_markup=get_ikb_to_send_payment_link(message.text, message.from_user.id))
    except Exception as x:
        logger.exception(x)
        await message.answer(database_error_message)
        return
        
    await state.finish()
    await delete_state_from_db(message.from_user.id)
    loop = asyncio.get_event_loop()
    loop.create_task(gsh.async_got_link(message.from_user.id, message.from_user.full_name, message.from_user.username))
    
    # await gsh.async_got_link(message.from_user.id, message.from_user.full_name, message.from_user.username)


@logger.catch
@dp.message_handler(state=TaskStates.transfer_to_bel_card_is_done, content_types=['any'])
async def send_bel_card_receipt(message: types.Message, state: FSMContext):
    message_for_admin = f'Чек оплаты от пользователя {message.from_user.full_name} (@{message.from_user.username}):'
    
    for admin_id in ADMIN_ID:
        reply_markup = get_ikb_to_confirm_bel_card_payment(message.from_user.id)
        message_id_in_admin_chat = await utils.send_and_copy_message(bot, admin_id, message,
                                                                     message_for_admin, reply_markup)
        new_not_checked_task = models.NotCheckedTask(admin_id=admin_id, receiver_id=message.from_user.id,
                                                     message_id=message_id_in_admin_chat.message_id,
                                                     task_number=0)
        session = db.Session()
        try:
            session.add(new_not_checked_task)
            session.commit()
        except IntegrityError:
            session.rollback()
            not_checked_task_obj = session.query(models.NotCheckedTask).filter(models.NotCheckedTask.receiver_id == str(message.from_user.id),
                                                                               models.NotCheckedTask.task_number == str(0),
                                                                               models.NotCheckedTask.admin_id == str(admin_id)).first()
            if not_checked_task_obj:
                try:
                    await bot.delete_message(admin_id, not_checked_task_obj.message_id)
                except:
                    pass
            not_checked_task_obj.message_id = message_id_in_admin_chat.message_id
            session.commit()
            
        except Exception as x:
            logger.exception(x)
        finally:
            if session.is_active:
                session.close()
                
    await message.answer('Твой чек отправлен на проверку. Ты получишь доступ к марафону и подарок, '
                         'как только чек будет проверен')
    await state.finish()
    await delete_state_from_db(message.from_user.id)


@logger.catch
@dp.callback_query_handler(callback_data_models.confirm_bel_card_payment_cb_data.filter())
async def confirm_bel_card_payment(callback_query: CallbackQuery, callback_data: dict):
    user_id = callback_data['receiver_id']
    
    loop = asyncio.get_event_loop()
    loop.create_task(gsh.async_paid(user_id))
    
    session = db.Session()
    try:
        await remove_keyboard_to_check_task(user_id, 0, session)
        remove_not_checked_tasks_from_db(user_id, 0, session)
        session.commit()
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()
    
    await payment_confirmed(user_id)
    await callback_query.answer(cache_time=0)
    
    # try:
    #     task = models.Task(client_tg_id=user_id, current_task=1)
    #     session = db.Session()
    #     try:
    #         session.add(task)
    #         session.commit()
    #         # await bot.send_message(user_id, 'Оплата прошла успешно, Вы готовы получить первое задание?',
    #         #                        reply_markup=get_ikb_to_get_task('1'))
    #
    #         await bot.send_message(user_id,
    #                                'Оплата прошла успешно! Вот твоя персональная ссылка в закрытый чат марафона:
    #                                \nhttps://t.me/+z3KnjLUsgsw0YTYy\n\n'
    #                                'А вот и обещанный подарок — РУКОВОДСТВО: «Площадки, сервисы и товары»\n'
    #                                'https://drive.google.com/file/d/1bjTh_qqWYQSHAlnS10Mdgf7AJgdeFQau/view?usp=share_link\n\n'
    #                                'Уже 22 мая ты получишь свое первое задание. Будь на связи!')
    #
    #         loop = asyncio.get_event_loop()
    #         loop.create_task(gsh.async_paid(user_id))
    #
    #     except IntegrityError as x:
    #         await bot.send_message(user_id, 'Ты уже получал задание')
    #     except Exception as x:
    #         logger.exception(x)
    #         await bot.send_message(user_id, 'У нас проблемы с базой данных. Если ты видишь это сообщение, '
    #                                         'напиши, пожалуйста, мне @dimatatatarin')
    #     finally:
    #         if session.is_active:
    #             session.close()
    # except ChatNotFound:
    #     pass


@logger.catch
@dp.callback_query_handler(callback_data_models.send_task_cb_data.filter(), state='*')
async def send_task(callback_query: CallbackQuery, callback_data: dict):
    task_number = callback_data['task_number']
    
    session = db.Session()
    try:
        task_message = session.query(models.Text).filter(models.Text.id == task_number).first().text
    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               database_error_message)
        return
    finally:
        if session.is_active:
            session.close()
    
    await bot.send_message(callback_query.from_user.id, task_message)
    await bot.send_message(callback_query.from_user.id, 'Пришли ответ на задание одним следующим сообщением '
                                                        'в любом формате (текст/аудио/видео)')
    await TaskStates.task_is_done.set()
    
    await callback_query.message.edit_reply_markup(reply_markup=None)
    
    await save_state_into_db(callback_query.from_user.id, 'TaskStates:task_is_done')
    await callback_query.answer(cache_time=0)
    
    loop = asyncio.get_event_loop()
    loop.create_task(gsh.async_on_task(callback_query.from_user.id, task_number))
    

@logger.catch
@dp.message_handler(state=TaskStates.task_is_done, content_types=['any'])
async def check_task(message: types.Message, state: FSMContext):
    session = db.Session()
    try:
        task_number = session.query(models.Task).filter(
            models.Task.client_tg_id == str(message.from_user.id)).first().current_task
        message_for_admin = f'Задание #{task_number} от пользователя {message.from_user.full_name}:'
        
        for admin_id in ADMIN_ID:
            reply_markup = get_ikb_to_check_users_tasks(message.from_user.id)
            message_id_in_admin_chat = await utils.send_and_copy_message(bot, admin_id, message,
                                                                         message_for_admin, reply_markup)
            new_not_checked_task = models.NotCheckedTask(admin_id=admin_id, receiver_id=message.from_user.id,
                                                         message_id=message_id_in_admin_chat.message_id,
                                                         task_number=task_number)
            session.add(new_not_checked_task)
        
            try:
                session.commit()
            
            except IntegrityError:
                session.rollback()
                not_checked_task_obj = session.query(models.NotCheckedTask).filter(models.NotCheckedTask.receiver_id == str(message.from_user.id),
                                                                                   models.NotCheckedTask.task_number == str(task_number),
                                                                                   models.NotCheckedTask.admin_id == str(admin_id)).first()
                if not_checked_task_obj:
                    try:
                        await bot.edit_message_reply_markup(admin_id, not_checked_task_obj.message_id,
                                                            reply_markup=None)
                    except:
                        pass
                    not_checked_task_obj.message_id = message_id_in_admin_chat.message_id
                    session.commit()
        
            except Exception as x:
                logger.exception(x)
                await bot.send_message(message.from_user.id,
                                       database_error_message)
                return
            
        await message.answer(
            'Твое задание отправлено на проверку. Ты получишь ответ, как только задание будет проверено'
        )

    except Exception as x:
        logger.exception(x)
        await bot.send_message(message.from_user.id,
                               database_error_message)
    finally:
        if session.is_active:
            session.close()
            
    await delete_state_from_db(message.from_user.id)
    await state.finish()

    
@logger.catch
@dp.callback_query_handler(callback_data_models.accept_task_cb_data.filter())
async def accept_task(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']
    task_number = 0
    
    session = db.Session()
    
    try:
        task = session.query(models.Task).filter(models.Task.client_tg_id == str(receiver_id)).first()
        
        await remove_keyboard_to_check_task(receiver_id, task.current_task, session)
        remove_not_checked_tasks_from_db(receiver_id, task.current_task, session)
        
        task.current_task += 1
        task_number = task.current_task
        session.commit()
    
    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               database_error_message)
        return
    
    finally:
        if session.is_active:
            session.close()
    
    session = db.Session()
    try:
        number_of_tasks_query = session.query(models.Text).filter(models.Text.id < 50)
        number_of_tasks = number_of_tasks_query.count()
    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               database_error_message)
        return
    finally:
        if session.is_active:
            session.close()
    
    if task_number > number_of_tasks:
        await bot.send_message(receiver_id, 'Твое задание приняли!')
        await bot.send_message(receiver_id, 'Ура, все задания выполнены!')
    else:
        try:
            reply_markup = get_ikb_to_get_task(str(task_number))
            await bot.send_message(receiver_id, 'Твое задание приняли! Хочешь получить следующее?',
                                   reply_markup=reply_markup)
        except Exception as x:
            await bot.send_message(receiver_id, database_error_message)
            logger.exception(x)

    await callback_query.answer(cache_time=0)


@logger.catch
@dp.callback_query_handler(callback_data_models.decline_task_cb_data.filter())
async def decline_task(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']
    
    session = db.Session()

    try:
        task = session.query(models.Task).filter(models.Task.client_tg_id == str(receiver_id)).first()
        
        await remove_keyboard_to_check_task(receiver_id, task.current_task, session)
        remove_not_checked_tasks_from_db(receiver_id, task.current_task, session)
        
        session.commit()

    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               database_error_message)
        return
    
    finally:
        if session.is_active:
            session.close()
    
    await bot.send_message(receiver_id, 'Твое задание не приняли, комментарий не дали.',
                           reply_markup=get_ikb_to_resend_declined_answer())
    await callback_query.answer(cache_time=0)


@logger.catch
@dp.callback_query_handler(callback_data_models.accept_task_with_comment_cb_data.filter())
async def accept_task_with_comment(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']

    session = db.Session()

    try:
        task = session.query(models.Task).filter(models.Task.client_tg_id == str(receiver_id)).first()
    
        await remove_keyboard_to_check_task(receiver_id, task.current_task, session)
        
        user = await bot.get_chat(receiver_id)
        msg = await callback_query.message.answer(
            f'Вы приняли решение пользователя {user.full_name}, дайте комментарий',
            reply_markup=get_ikb_to_cancel_state(receiver_id, task.current_task))
        await TaskStates.send_comment_after_accept.set()

        state = dp.get_current().current_state()
        await state.update_data(receiver_id=receiver_id,
                                cancel_message=msg['message_id'],
                                chat_id=msg['chat']['id'],
                                answer_message=callback_query.message.message_id)

        await callback_query.answer(cache_time=0)

    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               database_error_message)

    finally:
        if session.is_active:
            session.close()
    

@logger.catch
@dp.callback_query_handler(callback_data_models.decline_task_with_comment_cb_data.filter())
async def decline_task_with_comment(callback_query: CallbackQuery, callback_data: dict):
    receiver_id = callback_data['receiver_id']
    user = await bot.get_chat(receiver_id)

    session = db.Session()

    try:
        task = session.query(models.Task).filter(models.Task.client_tg_id == str(receiver_id)).first()
    
        await remove_keyboard_to_check_task(receiver_id, task.current_task, session)

        msg = await callback_query.message.answer(
            f'Вы отклонили решение пользователя {user.full_name}, дайте комментарий',
            reply_markup=get_ikb_to_cancel_state(receiver_id, task.current_task))
        await TaskStates.send_comment_after_decline.set()

        state = dp.get_current().current_state()
        await state.update_data(receiver_id=receiver_id,
                                cancel_message=msg['message_id'],
                                chat_id=msg['chat']['id'],
                                answer_message=callback_query.message.message_id)

        await callback_query.answer(cache_time=0)
        
    except Exception as x:
        logger.exception(x)
        await bot.send_message(callback_query.from_user.id,
                               database_error_message)
        
    finally:
        if session.is_active:
            session.close()


@logger.catch
@dp.message_handler(state=TaskStates.send_comment_after_accept, content_types=['any'])
async def send_comment_after_accept(message: types.Message, state: FSMContext):
    data = await state.get_data()
    receiver_id = data['receiver_id']
    cancel_message_id = data['cancel_message']
    chat_id = data['chat_id']
    answer_message_id = data['answer_message']
    
    session = db.Session()
    try:
        task = session.query(models.Task).filter(models.Task.client_tg_id == str(receiver_id)).first()
        
        remove_not_checked_tasks_from_db(receiver_id, task.current_task, session)
        
        task.current_task += 1
        task_number = task.current_task
        session.commit()

        message_for_client = f'Вот ответ от твоего ментора:'
        session = db.Session()
        try:
            number_of_tasks_query = session.query(models.Text).filter(models.Text.id < 50)
            number_of_tasks = number_of_tasks_query.count()
        except Exception as x:
            logger.exception(x)
            await bot.send_message(message.from_user.id,
                                   database_error_message)
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

        await bot.delete_message(chat_id, cancel_message_id)
        await state.finish()
        
    except Exception as x:
        logger.exception(x)
    finally:
        if session.is_active:
            session.close()
    

@logger.catch
@dp.message_handler(state=TaskStates.send_comment_after_decline, content_types=['any'])
async def send_comment_after_decline(message: types.Message, state: FSMContext):
    data = await state.get_data()
    receiver_id = data['receiver_id']
    cancel_message_id = data['cancel_message']
    chat_id = data['chat_id']
    answer_message_id = data['answer_message']

    session = db.Session()
    try:
        task = session.query(models.Task).filter(models.Task.client_tg_id == str(receiver_id)).first()
    
        remove_not_checked_tasks_from_db(receiver_id, task.current_task, session)
        
        session.commit()
    except Exception as x:
        logger.exception(x)
        await bot.send_message(message.from_user.id,
                               database_error_message)
        return
    
    finally:
        if session.is_active:
            session.close()
    
    await bot.delete_message(chat_id, cancel_message_id)
    
    message_for_client = f'Твое решение не приняли. Вот ответ от ментора:'
    
    await utils.send_and_copy_message(bot, receiver_id, message, message_for_client,
                                      reply_markup=get_ikb_to_resend_declined_answer(), divider=False)
    
    await state.finish()


@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'resend_declined_answer')
async def resend_declined_answer(callback_query: CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await save_state_into_db(callback_query.from_user.id, 'TaskStates:task_is_done')
    await TaskStates.task_is_done.set()
    await bot.send_message(callback_query.from_user.id, 'Пришли ответ на задание одним следующим сообщением '
                                                        'в любом формате (текст/аудио/видео)')


@logger.catch
@dp.callback_query_handler(callback_data_models.cancel_checking_task_cb_data.filter(), state='*')
async def drop_state(callback_query: CallbackQuery, callback_data: dict):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.finish()
    await callback_query.message.delete()
    await callback_query.answer('Действие отменено')

    receiver_id = callback_data['receiver_id']
    task_number = callback_data['task_number']

    session = db.Session()
    try:
        not_checked_task_objs = session.query(models.NotCheckedTask).filter(
            models.NotCheckedTask.receiver_id == str(receiver_id),
            models.NotCheckedTask.task_number == str(task_number)).all()

        for not_checked_task_obj in not_checked_task_objs:
            await bot.edit_message_reply_markup(not_checked_task_obj.admin_id, not_checked_task_obj.message_id,
                                                reply_markup=get_ikb_to_check_users_tasks(receiver_id))
    except Exception as x:
        logger.exception(x)


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
                                   'Оплата прошла успешно! Вот твоя персональная ссылка в закрытый чат '
                                   'марафона:\nhttps://t.me/+z3KnjLUsgsw0YTYy\n\n'
                                   'Нажми на кнопку под сообщением, чтобы получить первое задание\n\n'
                                   'А вот и обещанный подарок — РУКОВОДСТВО: «Площадки, сервисы и товары»:',
                                   reply_markup=get_ikb_to_get_task('1'))
            with open('Площадки,_сервисы_и_товары_для_продаж_в_строительстве.pdf', 'rb') as checklist:
                await bot.send_document(user_id, checklist)
        
        except IntegrityError:
            await bot.send_message(user_id, 'Ты уже получал задание')
        except Exception as x:
            logger.exception(x)
            await bot.send_message(user_id, database_error_message)
        finally:
            if session.is_active:
                session.close()
    except ChatNotFound:
        pass


async def send_message_to_users_manually(user_ids_list: list, message):
    for user_id in user_ids_list:
        try:
            await bot.send_message(user_id, message)
            logger.info(f'message is sent to {user_id}')
        except ChatNotFound as x:
            logger.exception(x)
        except Exception as x:
            logger.exception(x)
        finally:
            await asyncio.sleep(0.036)


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
    except IntegrityError:
        session.rollback()
        task_obj = session.query(models.Task).filter(models.Task.client_tg_id == str(user_id)).first()
        task_obj.current_task = task_number
        session.commit()
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
