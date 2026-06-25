from django.shortcuts import render


def guide_list(request):
    return render(request, "guide/guide_list.html")

def guide_detail(request):
    return render(request, "guide/guide_detail.html")