import json
import time

from channels.generic.websocket import WebsocketConsumer,AsyncWebsocketConsumer


class YourConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        for i in range(5):
            time.sleep(i + 2)
            await self.send(text_data=json.dumps(
                {
                    'type': 'connection_establish',
                    'message': f'{i}Hello,This is New File'
                }
            ))

    async def disconnect(self, close_code):
        pass
