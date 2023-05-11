import json
import os

from aiohttp import web
import csv
import io

from root.prodamus.main import confirm_payment
from main import payment_confirmed, send_message_to_users_manually, send_task_to_user_manually
from dotenv import load_dotenv, find_dotenv

from root.logger.log import logger

logger = logger
load_dotenv(find_dotenv())


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
        except Exception as x:
            logger.exception(x)
        
        # Do something with the numeric values, for example, return them as a JSON response
        return web.json_response({'message': message_text, 'numeric_values': numeric_values,
                                  'length': len(numeric_values)})
    
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
              
              <label for="lname">Пароль:</label><br>
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
        task_number = str(data['task_number'])
        password = data['pass']
    except Exception as x:
        logger.exception(x)
        raise web.HTTPFound('/fail')
    
    if password == os.getenv('WEB_PASSWORD'):
        await send_task_to_user_manually(user_id, task_number)
        raise web.HTTPFound('/success')
    else:
        logger.info('Someone tried to access admin panel without paassword')
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

if __name__ == '__main__':
    # web.run_app(app, host='0.0.0.0')
    web.run_app(app, host='127.0.0.1')
