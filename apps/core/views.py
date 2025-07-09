from django.shortcuts import render


def chat(request):
    return render(request, "chat.html")


def interview(request):
    return render(request, "interview.html")
