from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/socket/',consumers.YourConsumer.as_asgi())
]
# application = ProtocolTypeRouter({
#     'websocket': OriginValidator(
#         TokenAuthMiddleware(
#             URLRouter([
#                 path('ws/notification/',consumers.YourConsumer.as_asgi())
#                 # url(r"^.*$", NoRouteFoundConsumer.as_asgi()),
#             ])
#         ),
#         ['*'],
#     ),
# })