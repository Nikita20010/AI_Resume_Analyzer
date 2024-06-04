
#from django.shortcuts import render, redirect
# from .forms import ResumeForm
#import PyPDF2
# from .models import Resume

# def upload_resume(request):
#     if request.method == 'POST':
#         form = ResumeForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('student/analyze_resume')
#     else:
#         form = ResumeForm()
#     return render(request, 'student/upload_resume.html', {'form': form})

# def analyze_resume(request):
#     if request.method == 'POST':
#         resume_id = request.POST.get('resume_id')
#         resume = Resume.objects.get(id=resume_id)
#         extracted_content = extract_resume_content(resume.resume_file.path)
#         return render(request, 'student/analyze_resume.html', {'resume': resume, 'resume_data': extracted_content})
#     else:
#         resumes = Resume.objects.all()
#         return render(request, 'student/analyze_resume.html', {'resumes': resumes})




from pyresparser import ResumeParser

import json
import re
import io
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text

def extract_resume_content(file_path):
    # Extract text from PDF file
    text = pdf_reader(file_path)
    print(text)
    resume_data = ResumeParser("C:/Users/Admin/Downloads/Resume-Parser-master/Resume-Parser-master/PdfToForm/app/static/upload/Adhiksha Thorat.pdf").get_extracted_data()
    print("resume_data",resume_data)

    # Save the extracted text into a JSON file
    with open('D:/100% AI-Resume-Analyzer/100% AI-Resume-Analyzer/AI-Resume-Analyzer-main/App/Uploaded_Resumes//resume_text.json', 'w') as json_file:
        json.dump({'text': resume_data}, json_file, indent=4)

    return text

def analyze_resume():
    # if request.method == 'POST':
    #     resume_id = request.POST.get('resume_id')
    #     resume = Resume.objects.get(id=resume_id)
        extracted_content = extract_resume_content("C:/Users/Admin/Downloads/Resume-Parser-master/Resume-Parser-master/PdfToForm/app/static/upload/Adhiksha Thorat.pdf")
       
        # Read the JSON file containing the extracted text
        with open('D:/100% AI-Resume-Analyzer/100% AI-Resume-Analyzer/AI-Resume-Analyzer-main/App/Uploaded_Resumes/resume_text.json', 'r') as json_file:
            data = json.load(json_file)
            text = data['text']
            print(text['name'])

        
        print('candidate_name', text['name'],'Email', text['email'],'Mobile Number', text['mobile_number'],'Skills', text['skills'])

        # # Pass the extracted data to the template for rendering
        # return render(request, 'analyze_resume.html', {
        #     'candidate_name': candidate_name,
        #     'basic_details': basic_details,
        #     'education': education,
        #     'experience': experience,
        #     'skills': skills,
        #     'projects': projects
        # })

analyze_resume()