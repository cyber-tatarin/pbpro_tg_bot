from aiohttp import web

from root.prodamus.main import confirm_payment

import logging

# Set up logging
logging.basicConfig(
    filename='bot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def handle_post_request(request):
    data = await request.post()  # get request body as a multidict
    data_dict = dict(data)  # convert multidict to dict
    signature = str(request.headers.get('Sign'))
    
    logging.info(data_dict)
    logging.info(signature)
    
    await confirm_payment(signature, data_dict)
    return web.json_response({}, status=200)


async def handle_get_request(request):
    return web.json_response({}, status=200)

app = web.Application()
app.add_routes([web.post('/payment', handle_post_request)])
app.add_routes([web.get('/', handle_get_request)])

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0')

    