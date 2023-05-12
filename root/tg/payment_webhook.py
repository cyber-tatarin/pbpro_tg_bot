import json
import os

from aiohttp import web
import csv
import io
import aiohttp_jinja2
import jinja2
from sqlalchemy.exc import IntegrityError

from root.prodamus.main import confirm_payment
from main import payment_confirmed, send_message_to_users_manually, send_task_to_user_manually
from dotenv import load_dotenv, find_dotenv

from root.logger.log import logger
from root.db import setup as db, models

logger = logger
load_dotenv(find_dotenv())


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True
)


@logger.catch
async def handle_payment_post_request(request):
    try:
        data = await request.post()
        data = dict(data)
        logger.info(data)  # get request body as a raw json
        
        signature = str(request.headers.get('Sign'))
        
        logger.info(signature)
        
        await confirm_payment(signature, data)
        return web.json_response({}, status=200)
    except Exception as x:
        return web.json_response({}, status=403)


@logger.catch
async def confirm_user_payment_manually_form(request):
    return web.Response(
        text="""
        <!DOCTYPE html>
            <html>
            <body>
            
            <h2>Подтвердить оплату вручную</h2>
    
            <form action="/confirm_payment_manually" method="POST">
              <label for="id">ID пользователя:</label><br>
              <input type="text" id="id" name="id" required><br>
              
              <label for="pass">Пароль:</label><br>
              <input type="password" id="pass" name="pass" required><br><br>
              
              <input type="submit" value="Отправить">
            </form>
    
        
            </body>
            </html>
        """,
        content_type='text/html'
    )


async def confirm_user_payment_manually(request):
    try:
        data = await request.post()
        user_id = data['id']
        password = data['pass']
    except Exception as x:
        logger.exception(x)
        raise web.HTTPFound('/fail')
    
    if password == os.getenv('WEB_PASSWORD'):
        await payment_confirmed(user_id)
        raise web.HTTPFound('/success')
    else:
        logger.info('Someone tried to access admin panel without paassword')
        raise web.HTTPFound('/fail')


async def send_message_manually_form(request):
    return web.Response(text="""
    <!DOCTYPE html>
        <html>
        <body>
        
        <h2>Подтвердить оплату вручную</h2>
        
            <form action="/send_message_manually" method="POST" enctype="multipart/form-data">
                <label for="file">Файл с ID пользователей в первом столбце:</label><br>
                <input type="file" id="file" name="csv_file" required> <br><br>
                
                <label for="message">Текст сообщения:</label><br>
                <textarea id="message" rows = "30" cols = "60" name = "message_text" required></textarea> <br><br>
                
                <label for="pass">Пароль:</label><br>
                <input type="password" id="pass" name="pass" required><br><br>
              
                <input type="submit" value="Отправить">
            </form>
        </body>
        </html>
    """, content_type="text/html")


async def send_message_manually(request):
    password = None
    csv_file = None
    message_text = None
    numeric_values = []
    try:
        data = await request.post()
        message_text = data['message_text']
        csv_file = data['csv_file'].file
        password = data['pass']
    except Exception as x:
        logger.exception(x)
    
    if password == os.getenv('WEB_PASSWORD'):
        
        with csv_file:
            csv_file_content = csv_file.read()
        
        try:
            # Read the file as CSV and extract numeric values from the first column
            reader_list_of_lists = csv.reader(csv_file_content.decode('utf-8').splitlines())
            list_of_values = [row[0] for row in reader_list_of_lists]
            numeric_values = [int(value) for value in list_of_values if value and value.isnumeric()]
            
            await send_message_to_users_manually(numeric_values, message_text)
            raise web.HTTPFound('/success')
        except Exception as x:
            logger.exception(x)
            raise web.HTTPFound('/fail')
    
    else:
        logger.info('Someone tried to access admin panel without paassword')
        raise web.HTTPFound('/fail')


async def send_task_manually_form(request):
    return web.Response(
        text="""
        <!DOCTYPE html>
            <html>
            <body>

            <h2>Отправить задание вручную</h2>

            <form action="/send_task_manually" method="POST">
              <label for="id">ID пользователя:</label><br>
              <input type="text" id="id" name="id" required><br>
              
              <label for="task">Номер задания:</label><br>
              <input type="number" id="task" name="task_number" required><br>
              
              <label for="pass">Пароль:</label><br>
              <input type="password" id="pass" name="pass" required><br><br>
              
              <input type="submit" value="Отправить">
            </form>


            </body>
            </html>
        """,
        content_type='text/html'
    )


async def send_task_manually(request):
    try:
        data = await request.post()
        user_id = data['id']
        # if data['task_number'] > 7
        task_number = data['task_number']
        password = data['pass']
    except Exception as x:
        logger.exception(x)
        raise web.HTTPFound('/fail')

    session = db.Session()
    try:
        number_of_tasks_query = session.query(models.Text).filter(models.Text.id < 50)
        number_of_tasks = number_of_tasks_query.count()
    except Exception as x:
        logger.exception(x)
        return
    
    finally:
        if session.is_active:
            session.close()
    
    if password == os.getenv('WEB_PASSWORD') and int(task_number) <= number_of_tasks:
        await send_task_to_user_manually(user_id, task_number)
        raise web.HTTPFound('/success')
    else:
        logger.info('Someone tried to access admin panel without password or input wrong task number')
        raise web.HTTPFound('/fail')
    
    
@aiohttp_jinja2.template('update_text_form.html')
async def update_text_form(request):
    session = db.Session()
    all_text_objects = session.query(models.Text).order_by(models.Text.id).all()
    return {'text_objects': all_text_objects}


async def update_text(request):
    try:
        data = await request.post()
        text_id = data['id']
        # if data['task_number'] > 7
        new_text = data['new_text']
        password = data['pass']
    except Exception as x:
        logger.exception(x)
        raise web.HTTPFound('/fail')
    
    if password == os.getenv('WEB_PASSWORD'):
        session = db.Session()
        if new_text != '':
            text_object = models.Text(id=text_id, text=new_text)
            try:
                session.add(text_object)
                session.commit()
            except IntegrityError:
                session.rollback()
                text_object = session.query(models.Text).filter(models.Text.id == text_id).first()
                text_object.text = new_text
                session.commit()
            finally:
                if session.is_active:
                    session.close()
            raise web.HTTPFound('/update_text_form')
        else:
            text_object = session.query(models.Text).filter(models.Text.id == text_id).first()
            if text_object:
                session.delete(text_object)
                try:
                    session.commit()
                except Exception as x:
                    logger.exception(x)
                    raise web.HTTPFound('/fail')
            if session.is_active:
                session.close()
            raise web.HTTPFound('/update_text_form')
    else:
        logger.info('Someone tried to access admin panel without password')
        raise web.HTTPFound('/fail')


@logger.catch
async def success(request):
    return web.Response(text="<h2>Все получилось</h2>",
                        content_type='text/html')


@logger.catch
async def fail(request):
    return web.Response(text="<h2>Что-то пошло не так. Попробуйте еще раз</h2>",
                        content_type='text/html')


@logger.catch
async def start_menu(request):
    return web.Response(
        text="""
            <!DOCTYPE html>
                <html>
                <body>

                <h2>Панель управления ботом @StroyTinder_bot</h2>

                <a href="/confirm_payment_manually_form">Подтвердить оплату вручную</a><br><br>
                <a href="/send_message_manually_form">Отправить сообщения вручную</a><br><br>
                <a href="/send_task_manually_form">Отправить задание вручную</a><br><br>
                <a href="/update_text_form">Редактировать тексты</a><br><br>


                </body>
                </html>
            """,
        content_type='text/html'
    )


app = web.Application()
app.add_routes([web.post('/payment', handle_payment_post_request)])

app.add_routes([web.get('/', start_menu)])

app.add_routes([web.get('/confirm_payment_manually_form', confirm_user_payment_manually_form)])
app.add_routes([web.post('/confirm_payment_manually', confirm_user_payment_manually)])

app.add_routes([web.get('/success', success)])
app.add_routes([web.get('/fail', fail)])

app.router.add_get('/send_message_manually_form', send_message_manually_form)
app.router.add_post('/send_message_manually', send_message_manually)

app.router.add_get('/send_task_manually_form', send_task_manually_form)
app.router.add_post('/send_task_manually', send_task_manually)

app.router.add_get('/update_text_form', update_text_form)
app.router.add_post('/update_text', update_text)
aiohttp_jinja2.setup(app, loader=env.loader, context_processors=[aiohttp_jinja2.request_processor])

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0')
    # web.run_app(app, host='127.0.0.1')
