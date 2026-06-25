from django.shortcuts import render
from .models import BlogPost


def post_list(request):
    posts = BlogPost.objects.all()
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request):
    return render(request, "blog/post_detail.html")