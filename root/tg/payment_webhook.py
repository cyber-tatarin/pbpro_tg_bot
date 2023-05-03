import json
import os

from aiohttp import web

from root.prodamus.main import confirm_payment
from main import payment_confirmed
from dotenv import load_dotenv, find_dotenv

from root.logger.log import get_logger


logger = get_logger()
load_dotenv(find_dotenv())


@logger.catch
async def handle_post_request(request):
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
              <label for="fname">ID пользователя:</label><br>
              <input type="text" id="id" name="id" required><br>
              <label for="lname">Пароль:</label><br>
              <input type="text" id="pass" name="pass" required><br><br>
              <input type="submit" value="Отправить">
            </form>
    
        
            </body>
            </html>
        """,
        content_type='text/html'
    )


@logger.catch
async def confirm_user_payment_manually(request):
    data = await request.post()
    user_id = data['id']
    password = data['pass']
    
    logger.info(user_id, password)

    if password == os.getenv('WEB_PASSWORD'):
        await payment_confirmed(user_id)
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
async def handle_get_request(request):
    raise Exception('goooo')
    return web.json_response({}, status=200)

app = web.Application()
app.add_routes([web.post('/payment', handle_post_request)])
app.add_routes([web.get('/', handle_get_request)])
app.add_routes([web.get('/confirm_payment_manually_form', confirm_user_payment_manually_form)])
app.add_routes([web.post('/confirm_payment_manually', confirm_user_payment_manually)])
app.add_routes([web.get('/success', success)])
app.add_routes([web.get('/fail', fail)])

if __name__ == '__main__':
    # web.run_app(app, host='0.0.0.0')
    web.run_app(app, host='127.0.0.1')


    