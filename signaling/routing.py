from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/signal/(?P<room_name>\w+)/(?P<pin>\w+)/$', consumers.SignalingConsumer.as_asgi()),
]