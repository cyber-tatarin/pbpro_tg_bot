import json

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
    try:
        data = await request.post()
        data = dict(data)
        logging.info(data)  # get request body as a raw json

        # raw_data = {key: value for key, value in data.multi_items()}
        # raw_data = json.loads(json.dumps(raw_data))  # remove unnecessary escaping
        
        signature = str(request.headers.get('Sign'))
    
        logging.info(data)
        logging.info(signature)
    
        await confirm_payment(signature, data)
        return web.json_response({}, status=200)
    except Exception as x:
        logging.error(x)
        return web.json_response({}, status=403)


async def handle_get_request(request):
    return web.json_response({}, status=200)

app = web.Application()
app.add_routes([web.post('/payment', handle_post_request)])
app.add_routes([web.get('/', handle_get_request)])

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0')

    