from django.shortcuts import render, redirect, get_object_or_404
from .forms import ChatForm
from .models import ChatSession, Message
from .utils import generate_response

def chat(request):
    return render(request, 'chat.html', context={'text': 'Chat Bot'})

def home(request):
    return render(request, 'chats/home.html')

def new_chat(request):
    session = ChatSession.objects.create()
    return redirect('chats:chat', id=str(session.id))


def chat_view(request, id):
    session = get_object_or_404(ChatSession, id=id)

    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['user_input']

            recent_messages = session.messages.order_by('-created')[:3][::-1]
            ai_response = generate_response(user_input, recent_messages)

            Message.objects.create(session=session, sender='human', text=user_input)
            Message.objects.create(session=session, sender='ai', text=ai_response)

            return redirect('chats:chat', id=session.id)

    else:
        form = ChatForm()

    chat_history = session.messages.order_by('created')

    return render(request, 'chats/chats.html', {
        'form': form,
        'chat_history': chat_history,
        'session': session,
    })