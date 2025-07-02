from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import uuid

from .models import ChatSession, Message


def chat_view(request, session_id=None):
    """
    Main chat interface view
    """
    session = None
    messages = []
    
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id)
            messages = session.messages.all().order_by('created')
        except ChatSession.DoesNotExist:
            # Create new session with provided ID
            session = ChatSession.objects.create(id=session_id)
    
    context = {
        'session': session,
        'session_id': str(session.id) if session else None,
        'messages': messages,
    }
    
    return render(request, 'core/chat.html', context)


def new_chat_view(request):
    """
    Create new chat session and redirect
    """
    new_session_id = str(uuid.uuid4())
    return chat_view(request, new_session_id)


def chat_sessions_view(request):
    """
    List all chat sessions
    """
    sessions = ChatSession.objects.all().order_by('-created')
    
    context = {
        'sessions': sessions,
    }
    
    return render(request, 'core/chat_sessions.html', context)


@csrf_exempt
def api_chat_sessions(request):
    """
    API endpoint for chat sessions
    """
    if request.method == 'GET':
        sessions = ChatSession.objects.all().order_by('-created')
        data = []
        
        for session in sessions:
            data.append({
                'id': str(session.id),
                'created': session.created.isoformat(),
                'message_count': session.messages.count(),
                'last_message': session.messages.last().text[:50] if session.messages.last() else None,
            })
        
        return JsonResponse({'sessions': data})
    
    elif request.method == 'POST':
        # Create new session
        session = ChatSession.objects.create()
        return JsonResponse({
            'id': str(session.id),
            'created': session.created.isoformat(),
        })


def home_view(request):
    """
    Home page with links to chat
    """
    recent_sessions = ChatSession.objects.all().order_by('-created')[:5]
    
    context = {
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'core/home.html', context)
