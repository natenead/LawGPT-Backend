import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import LawApp.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LawGPT.settings')

application = ProtocolTypeRouter({
    'http':get_asgi_application(),
    'websocket':
        URLRouter(
            LawApp.routing.websocket_urlpatterns

    )
})

# """
# ASGI config for djangochannels project.
#
# It exposes the ASGI callable as a module-level variable named ``application``.
#
# For more information on this file, see
# https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
# """
#
# # import os
# #
# # from django.core.asgi import get_asgi_application
# #
# # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LawGPT.settings')
# #
# # application = get_asgi_application()


# import os
#
# from django.core.asgi import get_asgi_application
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LawGPT.settings')
#
# application = get_asgi_application()
