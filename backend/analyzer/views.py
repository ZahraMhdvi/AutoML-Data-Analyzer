from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from ml_engine.analyzer_service import DatasetAnalyzer
def home(request):
    return HttpResponse("ML Dataset Advisor is running!")


from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

from ml_engine.analyzer_service import DatasetAnalyzer



def upload_dataset(request):

    if request.method == "POST":

        uploaded_file = request.FILES["dataset"]
        fs = FileSystemStorage()
        file_name = fs.save(uploaded_file.name,uploaded_file)
        file_path = fs.path(file_name)
        analyzer = DatasetAnalyzer()
        result = analyzer.analyze(file_path)


        return render(request,"analyzer/result.html",{"result": result })


    return render(request,"analyzer/upload.html")