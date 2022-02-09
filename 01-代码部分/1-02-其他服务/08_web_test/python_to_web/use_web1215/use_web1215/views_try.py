from django.http import HttpResponse
from django.shortcuts import render

def hello(request):
    return HttpResponse("Hello World!")

def fun1(request):
    return HttpResponse("Open the book")

def runoob(request):
    # context = {}
    # context["hello"] = "Hello World ! "
    # return render(request, 'runoob.html', context)

    name1 = "菜鸟教程 Ohhh~~"
    return render(request, 'runoob.html', {"name1": name1})

    # list_name1 = ["数字1", "数字2", "数字3", "数字4",]
    # return render(request, 'runoob.html', {"list_name1": list_name1})

    # views_str = "<a href='https://www.runoob.com/'>点击跳转</a>"
    # return render(request, 'runoob.html', {"views_str": views_str})

def runoob2(request):
    name2 = "123.43"
    return render(request, 'runoob.html', {"name2": name2})


def cainiao1(request):
    return render(request, 'cainiao1.html')