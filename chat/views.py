from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ChatRoom
from django.contrib.auth.models import User
def index(request):
    # Redirect to login if no token in session
    if not request.session.get('access_token'):
        return redirect('/chat/login/')

    history = request.session.get('room_history', [])
    return render(request, 'chat/index.html', {'history': history})


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            request.session['access_token'] = str(refresh.access_token)
            request.session['username'] = username
            return redirect('/chat/')
        else:
            error = 'Invalid username or password'

    return render(request, 'chat/login.html', {'error': error})


def room(request, room_name):
    token = request.session.get('access_token')
    pin = request.session.get('pin')

    if not token or not pin:
        return redirect('/chat/')

    try:
        ChatRoom.objects.get(name=room_name, pin=pin)
    except ChatRoom.DoesNotExist:
        return redirect('/chat/')

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'pin': pin,
        'token': token,
        'username': request.session.get('username'),
    })


def create_or_join(request):
    if not request.session.get('access_token'):
        return redirect('/chat/login/')

    history = request.session.get('room_history', [])

    if request.method == 'POST':
        action = request.POST.get('action')
        token = request.session.get('access_token')
        username = request.session.get('username')

        if action == 'create':
            room_name = request.POST.get('room_name')
            room = ChatRoom.objects.create(name=room_name)
            request.session['pin'] = room.pin
            _add_to_history(request, room.name, room.pin)
            return redirect(f'/chat/{room.name}/')

        elif action == 'join':
            pin = request.POST.get('pin')
            room_name = request.POST.get('room_name')
            try:
                room = ChatRoom.objects.get(pin=pin, name=room_name)
                request.session['pin'] = pin
                _add_to_history(request, room.name, room.pin)
                return redirect(f'/chat/{room.name}/')
            except ChatRoom.DoesNotExist:
                return render(request, 'chat/index.html', {
                    'error': 'Invalid PIN',
                    'history': history,
                })

    return render(request, 'chat/index.html', {'history': history})


def _add_to_history(request, room_name, pin, username):
    history = request.session.get('room_history', [])
    history = [r for r in history if r['pin'] != pin]
    history.insert(0, {'room_name': room_name, 'pin': pin, 'username': username})
    request.session['room_history'] = history[:10]
    request.session.modified = True


def rejoin_room(request, pin):
    history = request.session.get('room_history', [])
    entry = next((r for r in history if r['pin'] == pin), None)
    if not entry:
        return redirect('/chat/')
    try:
        room = ChatRoom.objects.get(pin=pin)
    except ChatRoom.DoesNotExist:
        request.session['room_history'] = [r for r in history if r['pin'] != pin]
        request.session.modified = True
        return redirect('/chat/')
    request.session['pin'] = pin
    return redirect(f'/chat/{room.name}/')


def leave_room(request):
    request.session.pop('pin', None)
    return redirect('/chat/')


def logout_view(request):
    history = request.session.get('room_history', [])  # save history
    request.session.flush()                             # clear session
    request.session['room_history'] = history           # restore history
    return redirect('/chat/login/')



def register_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            error = 'Passwords do not match'
        elif User.objects.filter(username=username).exists():
            error = 'Username already taken'
        else:
            user = User.objects.create_user(username=username, password=password)
            refresh = RefreshToken.for_user(user)
            request.session['access_token'] = str(refresh.access_token)
            request.session['username'] = username
            return redirect('/chat/')

    return render(request, 'chat/register.html', {'error': error})

def _add_to_history(request, room_name, pin):
    history = request.session.get('room_history', [])
    history = [r for r in history if r['pin'] != pin]
    history.insert(0, {'room_name': room_name, 'pin': pin})
    request.session['room_history'] = history[:10]
    request.session.modified = True