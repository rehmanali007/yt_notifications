from bottle import route, run, request, default_app, abort, app
import xml.etree.ElementTree as XML
import asyncio
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
import json

config = json.load(open('config.json', 'r'))

WEBHOOK_URL = config.get("WEBHOOK_URL")
notified = []

namespaces = {
    'yt': 'http://www.youtube.com/xml/schemas/2015',
    'xmlns': 'http://www.w3.org/2005/Atom'
}

'''
To subscribe to a channel's notifications go to https://pubsubhubbub.appspot.com/subscribe
And use this URL --> ( https://www.youtube.com/xml/feeds/videos.xml?channel_id=TARGET_CHANNEL_ID )

'''


async def send_to_target(message):
    print('Sending to target')
    username = config.get("BOT_NAME")
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(
            WEBHOOK_URL, adapter=AsyncWebhookAdapter(session))
        await webhook.send(message, username=username)


@route('/callback', method='get')
@route('/callback', method='post')
def index():
    global notified
    if request.method == 'POST':
        response = request.body.read().decode('utf-8')
        root = XML.fromstring(response)

        for entry in root.findall('xmlns:entry', namespaces=namespaces):
            deleted = entry.find('at:deleted-entry')
            if deleted:
                # return
                return
            video_id = entry.find('yt:videoId', namespaces=namespaces).text
            title = entry.find('xmlns:title', namespaces=namespaces).text
            link = entry.find('xmlns:link', namespaces=namespaces).get('href')
            for el in entry.find(
                    'xmlns:author', namespaces=namespaces):
                if el.tag.split('}')[-1] == 'name':
                    author = el.text

            message = config.get("DESCRIPTION")
            message = message.replace(
                'VIDEO_LINK_HERE', link).replace('AUTHOR_HERE', author)
            if link in notified:
                return
            asyncio.get_event_loop().run_until_complete(send_to_target(message))
            notified.append(link)
            notified = notified[-100:]
            print('Message sent!')

        # Do Something Here

        return 'Goodly'

    try:
        mode = request.query['hub.mode']
        challenge = request.query['hub.challenge']
        return challenge
        verify_token = request.query['hub.verify_token']
    except KeyError:
        print('KeyError, Aborting ..')
        abort(404)

    if mode == 'subscribe' and verify_token == secret:
        return challenge
    abort(404)


if __name__ == '__main__':
    """For Development"""
    run(host='0.0.0.0', port=80, debug=True)

# For Production
app = app()
