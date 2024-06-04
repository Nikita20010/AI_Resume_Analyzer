from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
#from teacher import models as TMODEL
import json
import re
import io
from pyresparser import ResumeParser

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from django.shortcuts import render

#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')

def student_signup_view(request):
    userForm=forms.StudentUserForm()
    studentForm=forms.StudentForm()
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=forms.StudentUserForm(request.POST)
        studentForm=forms.StudentForm(request.POST,request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            student=studentForm.save(commit=False)
            student.user=user
            student.save()
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
        return HttpResponseRedirect('studentlogin')
    return render(request,'student/studentsignup.html',context=mydict)

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    }
    return render(request,'student/student_dashboard.html',context=dict)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_exam.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    total_questions=QMODEL.Question.objects.all().filter(course=course).count()
    questions=QMODEL.Question.objects.all().filter(course=course)
    total_marks=0
    for q in questions:
        total_marks=total_marks + q.marks
    
    return render(request,'student/take_exam.html',{'course':course,'total_questions':total_questions,'total_marks':total_marks})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    questions=QMODEL.Question.objects.all().filter(course=course)
    if request.method=='POST':
        pass
    response= render(request,'student/start_exam.html',{'course':course,'questions':questions})
    response.set_cookie('course_id',course.id)
    return response


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get('course_id') is not None:
        course_id = request.COOKIES.get('course_id')
        course=QMODEL.Course.objects.get(id=course_id)
        
        total_marks=0
        questions=QMODEL.Question.objects.all().filter(course=course)
        for i in range(len(questions)):
            
            selected_ans = request.COOKIES.get(str(i+1))
            actual_answer = questions[i].answer
            if selected_ans == actual_answer:
                total_marks = total_marks + questions[i].marks
        student = models.Student.objects.get(user_id=request.user.id)
        result = QMODEL.Result()
        result.marks=total_marks
        result.exam=course
        result.student=student
        result.save()

        return HttpResponseRedirect('view-result')



@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':courses})
    

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results= QMODEL.Result.objects.all().filter(exam=course).filter(student=student)

    # Retrieve all results for the given course
    all_results = QMODEL.Result.objects.filter(exam=course)

    # Sort results by marks
    sorted_results = sorted(all_results, key=lambda x: x.marks, reverse=True)

    # Calculate rank positions
    highest_marks = sorted_results[0].marks if sorted_results else 0
    medium_marks = sorted_results[len(sorted_results) // 2].marks if sorted_results else 0
    lowest_marks = sorted_results[-1].marks if sorted_results else 0

    return render(request, 'student/check_marks.html', {
        'results': results,
        'all_results': all_results,
        'highest_marks': highest_marks,
        'medium_marks': medium_marks,
        'lowest_marks': lowest_marks,
        'course': course  # Pass the course object to the template
    })
   # return render(request,'student/check_marks.html',{'results':results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})



def extract_resume_content(file_path):
    # Extract content from PDF file
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfFileReader(file)
        text = ''
        for page_num in range(reader.numPages):
            text += reader.getPage(page_num).extractText()
    # Process extracted content as needed (e.g., split into points)
    points = text.split('\n')
    return points



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

from django.shortcuts import render, redirect
from .forms import ResumeForm
import PyPDF2
from .models import Resume
def upload_resume(request):
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            #return redirect('analyze_resume')
            latest_resume = Resume.objects.last()  # Get the latest uploaded resume
                # Extract text from PDF file
            text = pdf_reader(latest_resume.resume_file.path)
            print(text)
            
            resume_data = ResumeParser(latest_resume.resume_file.path).get_extracted_data()
            print("resume_data", resume_data)

            # Save the extracted text into a JSON file
            with open('student/Uploaded_Resumes/resume_text.json', 'w') as json_file:
                json.dump({'text': resume_data}, json_file, indent=4)

            # Read the JSON file containing the extracted text
            with open('student/Uploaded_Resumes/resume_text.json', 'r') as json_file:
                data = json.load(json_file)
                text = data['text']
            resume_skills = text['skills']

            print('candidate_name', text['name'], 'Email', text['email'], 'Mobile Number', text['mobile_number'], 'Skills', text['skills'])
            # Read the JSON file containing job data
            with open("student/Uploaded_Resumes/recommended_jobs.json", 'r') as json_file:
                jobs_data = json.load(json_file)
            
            resume_skills_lower = [skill.lower() for skill in resume_skills]

            recommended_jobs = []
            for job in jobs_data['jobs']:
                # Extract skills required for the job
                job_skills = job.get('Skills', '').split(', ')
                
                # Check if any of the required skills for the job are present in the resume
                matched_skills = [skill.strip().lower() for skill in job_skills if skill.strip().lower() in resume_skills_lower]
                if matched_skills:
                    job['Skills'] = matched_skills
                    recommended_jobs.append(job)

            
            #return 
            print("Recommended jobs: ",recommended_jobs)
            for job in recommended_jobs:
                print(job['title'], "at", job['company'], "in", job['location'])

            # Pass the extracted data to the template for rendering
            return render(request, 'student/analyze_resume.html', {
                'resumes': latest_resume,  # Pass all resumes to the template
                'candidate_name': text['name'],
                'Email': text['email'],
                'Mobile_Number': text['mobile_number'],
                'Skills': text['skills'],
                'Experiance': text['total_experience'],
                'recommended_jobs':recommended_jobs,
            })
        else:
            return render(request, 'student/analyze_resume.html', {'resumes': latest_resume})

        
    else:
        form = ResumeForm()
    return render(request, 'student/upload_resume.html', {'form': form})

# def analyze_resume(request):
#     resumes = Resume.objects.all()  # Fetch all resumes

#     if request.method == 'POST':
#         resume_id = request.POST.get('resume_id')
#         resume = Resume.objects.get(id=resume_id)
#         print(resume.resume_file.path)
        
#         # Extract text from PDF file
#         text = pdf_reader(resume.resume_file.path)
#         print(text)
        
#         resume_data = ResumeParser(resume.resume_file.path).get_extracted_data()
#         print("resume_data", resume_data)

#         # Save the extracted text into a JSON file
#         with open('student/resume_text.json', 'w') as json_file:
#             json.dump({'text': resume_data}, json_file, indent=4)

#         # Read the JSON file containing the extracted text
#         with open('D:/100% AI-Resume-Analyzer/100% AI-Resume-Analyzer/AI-Resume-Analyzer-main/App/Uploaded_Resumes/resume_text.json', 'r') as json_file:
#             data = json.load(json_file)
#             text = data['text']
#             print(text['name'])

#         print('candidate_name', text['name'], 'Email', text['email'], 'Mobile Number', text['mobile_number'], 'Skills', text['skills'])

#         # Pass the extracted data to the template for rendering
#         return render(request, 'student/analyze_resume.html', {
#             'resumes': resumes,  # Pass all resumes to the template
#             'candidate_name': text['name'],
#             'Email': text['email'],
#             'Mobile_Number': text['mobile_number'],
#             'Skills': text['skills'],
#             'Experiance': text['total_experience'],
#         })
#     else:
#         return render(request, 'student/analyze_resume.html', {'resumes': resumes})
