import os
import mimetypes
from django.conf import settings
from django.shortcuts import render,redirect
from django.http import FileResponse



#function to deal with download files, obsolete
#def download_file(request,query_id,filename):
#    return FileResponse(open(os.path.join('media','submission',query_id,filename),'rb'))

def home(request):
    return render(request,"s2d2/home.html")

def help(request):
    return render(request,"s2d2/help.html")


