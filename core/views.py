from django.shortcuts import render

def chat(request):
    return render(request, 'chat.html', context={'text': 'Chat Bot'})
