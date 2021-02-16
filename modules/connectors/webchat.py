from aiohttp import web
import socketio
import uuid
import re
import os.path
import ssl
import time
from modules import extractor, caller

sio = socketio.AsyncServer(cors_allowed_origins=[]) #Only for SSL workaround so that socketio works with requests from other origins.
#sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

async def index(request):
    """Serve the client-side application."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(dir_path + '/index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

#START SOCKET CONNECTION
@sio.event
def connect(sid, environ):
    print("connect ", sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

@sio.on('session_request')
async def session_request(sid, data):
    if data is None:
        data = {}
    if 'session_id' not in data or data['session_id'] is None:
        data['session_id'] = uuid.uuid4().hex
    print('session_confirm: ', data['session_id'])
    await sio.emit("session_confirm", data['session_id'], room=sid)
#END SOCKET CONNECTION



@sio.on('user_uttered') #ON USER MESSAGE
async def handle_message(sid, message_dict):
    quick_replies = {}
    all_quick_replies = []
    message = message_dict['message']
    parsed_message = extractor.parse(message)
    response = caller.run_action_from_parsed_message(parsed_message, "WEBCHAT_"+str(sid))
    print(response.get_printable_string())
    for x in response.get_telegram_or_webchat_format():
        text = x['message']
        if text == 'Pie chart':
            timestamp = time.time()
            image_src = "/static/pie.png?" +str(timestamp)
            send_message = {"attachment":{"type":"image","payload":{"title":"Category table","src":image_src}}}
            await sio.emit('bot_uttered', send_message, room=sid)
        else:
            if x['buttons']:
                for b in x ['buttons']:
                    quick_replies['title'] = b['title']
                    quick_replies['payload'] = b['payload']
                    all_quick_replies.append(quick_replies.copy())
            send_message = {"text": text, "quick_replies":all_quick_replies}
            await sio.emit('bot_uttered', send_message, room=sid)


app.router.add_static('/static', './static')
app.router.add_get('/', index)

def start():
    cert_path = os.path.dirname(os.path.realpath(__file__))
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=cert_path+ "/certificate.crt", keyfile= cert_path+"/private.key")
    web.run_app(app, port=5080,ssl_context=context)
    #web.run_app(app, port=8080)
