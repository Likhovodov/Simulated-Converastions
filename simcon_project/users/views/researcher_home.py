from django.shortcuts import render

def ResearcherView(request):
    responseTable = template_response.objects.all()
    return render(request, 'researcher_view.html', locals())