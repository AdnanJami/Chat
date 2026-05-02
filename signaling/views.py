from django.shortcuts import render, redirect
from chat.models import ChatRoom


def call(request, room_name):
    token = request.session.get('access_token')
    pin = request.session.get('pin')
    username = request.session.get('username')

    if not token or not pin:
        return redirect('/chat/')

    try:
        ChatRoom.objects.get(name=room_name, pin=pin)
    except ChatRoom.DoesNotExist:
        return redirect('/chat/')

    return render(request, 'signaling/call.html', {
        'room_name': room_name,
        'pin': pin,
        'token': token,
        'username': username,
    })