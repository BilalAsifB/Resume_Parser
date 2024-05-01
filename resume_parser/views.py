from django.shortcuts import redirect, render
from django.conf import settings
from django.http import HttpResponseBadRequest
from .forms import ResumeUploadForm
from .models import UploadedResume
import os
from pdfminer.high_level import extract_text
import pandas as pd
import re
import shutil
import spacy
from spacy.matcher import Matcher
from pdfminer.high_level import extract_text
from django.conf import settings

#THRESHOLD = 0.75  # tweak THRESHOLD to get optimal matching
THRESHOLD = 0.50
# Create your views here.

def home(request):
    return render(request, 'resume_parser/home.html')

def upload_resume(request):
    if request.method == 'POST':

        form = ResumeUploadForm(request.POST, request.FILES)
        
        uploaded_file = request.FILES.get('resume')
        
        if form.is_valid():
        
            if not uploaded_file.name.endswith(('pdf')) :
        
                return HttpResponseBadRequest('Only PDF files are allowed.')
        
            form.save()
        
            return render(request, 'resume_parser/upload_success.html')
        
        else:
        
            return HttpResponseBadRequest('No file uploaded.')
    
    else:
    
        form = ResumeUploadForm()
    
    return render(request, 'resume_parser/upload_resume.html', {'form': form})

def admin_options(request):

    return render(request, 'resume_parser/admin_options.html')

def admin_login(request):
    
    # redirects to djangos default admin login page
    
    return redirect('/admin/')

def parse_resume_login(request):
    
    # login for parsing resume
    
    if request.method == 'POST':
    
        username = request.POST.get('username')
    
        password = request.POST.get('password')
    
        # Authenticate user similar to superuser
    
        if username == 'admin' and password == '1234':
    
            # Redirect to the page with the resume parse button
    
            return redirect('parsed_resume')
    
        else:
    
            return HttpResponseBadRequest('Wrong Username/Password !!!')
    
    return render(request, 'resume_parser/parse_resume_login.html')

# orginal starts

def parsed_resume(request):
    
    uploaded_pdfs = UploadedResume.objects.all()

    pdf_list = []

    for pdf in uploaded_pdfs:

        pdf_url = settings.MEDIA_URL + str(pdf.resume)

        pdf_list.append(( pdf.candidate_name, pdf_url))

    context = {'pdf_list' : pdf_list}

    return render(request, 'resume_parser/parsed_resume.html', context)

# original ends


# this is the original function below

def parsed_selected_pdfs(request):
    if request.method == 'POST':

        skills = request.POST.get('skills').split(',')
        
        qualifications = request.POST.get('qualifications').split(',')

        xls_path = os.path.join(settings.MEDIA_ROOT, 'excel' ,'parsed_data.xlsx')
        
        data = {'SKILL': [], 'QUALIFICATION': []}
        
        for skill in skills :
            
            data['SKILL'].append(skill.strip())
            
            data['QUALIFICATION'].append('')

        for qualification in qualifications :
            
            data['SKILL'].append('')
            
            data['QUALIFICATION'].append(qualification.strip())

        
        df = pd.DataFrame(data)

        if os.path.exists(xls_path):
            
            os.remove(xls_path)

        df.to_excel(xls_path, index=False)



        selected_pdfs = request.POST.getlist('selected_pdfs')
        
        selected_pdf_contents = []
        pdf_path_list = []

        for pdf_url in selected_pdfs:
            pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_url[len(settings.MEDIA_URL):])  # Construct file path
            # main logic of parsing will be enclosed here between these 2 hashes and remember that the model 
            # has to return a pdf file so that it can be displayed on the next page
            pdf_path_list.append(pdf_path)

        req = pd.read_excel(xls_path)
        req = req.to_dict("list")
        for key, val in req.items() :
            req[key] = [x.lower() for x in val if x == x]


        if not req :
            return HttpResponseBadRequest("no reqs provided")
        else:
            dir_path = os.path.join(settings.MEDIA_ROOT , "selected_resumes")
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)    

            nlp = spacy.load("en_core_web_md")

            df_1 = pd.read_csv(os.path.join(settings.STATIC_ROOT , 'datasets' , 'jobs.csv'))    
            df_2 = pd.read_csv(os.path.join(settings.STATIC_ROOT , 'datasets' , 'names.csv'))
            df_3 = pd.read_csv(os.path.join(settings.STATIC_ROOT , 'datasets' , 'job_titles.csv'))
            df_4 = pd.read_csv(os.path.join(settings.STATIC_ROOT , 'datasets' , 'qualification.csv'))
            df_5 = pd.read_csv(os.path.join(settings.STATIC_ROOT , 'datasets' , 'skills.csv'))
            
            names = list( set( df_2["Names"].to_list() ) )
            company_names = df_1["Company Name"].to_list()
            job_titles = df_3["Job Title"].to_list()
            q_list = df_4.values.tolist()
            S_kills = df_5["Skills"].to_list()
            ruler = nlp.add_pipe("entity_ruler", before="ner")
            patterns = []
            for name in names:
                patterns.append({"label": "PERSON", "pattern": name.lower()})
            for name in company_names:
                if isinstance(name, str):
                    patterns.append({"label": "ORG", "pattern": name.lower()})
                else:
                    patterns.append({"label": "ORG", "pattern": name})
            for title in job_titles:
                patterns.append({"label": "JOB", "pattern": title.lower()})
            for q in q_list:
                patterns.append({"label": "LEVEL", "pattern": q[0].lower()})
            for q in q_list:
                patterns.append({"label": "QUALIFICATION", "pattern": q[2].lower()})
            for q in q_list:
                patterns.append({"label": "QUALIFICATION", "pattern": q[3].lower()})
            for skill in S_kills:
                patterns.append({"label": "SKILL", "pattern": skill.lower()})
            ruler.add_patterns(patterns)

            score = {}
            summary = {}
            num=1
            
            for file in pdf_path_list : 
                text = extract_text(file).lower()
                doc = nlp(text)
                num = filter_resumes(text, doc, nlp, req, num, score, summary, file)
        
        sort_summarize_resumes(score,summary)    
        # parsing logic ends over here

        selected_resumes_folder = os.path.join(settings.MEDIA_ROOT , 'selected_resumes')
        file_names = os.listdir(selected_resumes_folder)

        #Each element in this list is a dictionary containing two key-value pairs
        # name and url , so file_objects is a list of dictionaries
        file_objects = []

        for file_name in file_names :
            file_url = os.path.join(settings.MEDIA_URL , 'selected_resumes' , file_name)
            file_objects.append({'name':file_name, 'url':file_url})


        return render(request, 'resume_parser/parsed_results.html', {'file_names' : file_objects })
    else:
        return redirect('parsed_resume') 

# original function ends over here       

def word_search(req, label, search, nlp, vals) :

    for l in req[label]:
        matched_words = list()
        to_be_searched = nlp(l)
        for token in to_be_searched:
            if token.similarity(search) >= THRESHOLD:
                matched_words.append(token)
        if len(matched_words) != 0:
            vals.add(l)


def extract_qualifications(doc, nlp, req) :

    qual = set()
    for ent in doc.ents:
        if ent.label_ == "QUALIFICATION" :
            word_search(req, ent.label_, nlp(ent.text), nlp, qual)
    return qual

def extract_name(doc, nlp):
    matcher = Matcher(nlp.vocab)
    pattern = [{"POS": "PROPN", "OP": "+"}]
    matcher.add("PROPER_NOUNS", [pattern], greedy="LONGEST")
    matches = matcher(doc)
    for match in matches:
        text = str(doc[match[1] : match[2]])
        flag = True
        name_doc = nlp(text)
        for ent in name_doc.ents:
            if ent.label_ != "PERSON":
                flag = False
                break
        if flag:
            return text
    return None

def extract_email(doc, nlp) :
    matcher = Matcher(nlp.vocab)
    pattern = [{"LIKE_EMAIL": True}]
    matcher.add("EMAIL_ADDRESS", [pattern])
    matches = matcher(doc)
    return matches


def extract_number(text) :
    pattern = re.compile(r"[\+\(]?[0-9][0-9 .\-\(\)]{8,}[0-9]")
    matches = re.findall(pattern, text)
    return matches


def info_extraction(text, doc, nlp):
    info = []
    name = extract_name(doc, nlp)
    emails = extract_email(doc, nlp)
    numbers = extract_number(text)
    info.append([name])
    if len(emails) == 0:
        info.append([None])
    else:
        temp = []
        for email in emails:
            temp.append(doc[email[1] : email[2]])
        info.append(temp)
    if len(numbers) == 0:
        info.append([None])
    else:
        temp = []
        for num in numbers:
            temp.append(num)
        info.append(temp)
    return info

def extract_skills(doc,nlp,req):
    skills = set()
    for ent in doc.ents:
        if ent.label_ == "SKILL":
            word_search(req, ent.label_, nlp(ent.text), nlp, skills)
    return skills

def filter_resumes(text, doc, nlp, req, num, score, summary, path) :

    qual = extract_qualifications(doc, nlp, req)
    if len(qual) == len(req['QUALIFICATION']): 
        information = info_extraction(text, doc, nlp)
        temp = []
        for q in qual:
            temp.append(q)
        information.append(temp)
        skills = extract_skills(doc, nlp, req)
        information.append(list(skills))
        information.append([path])
        key = "resume_" + str(num) + ".txt"
        num += 1
        summary[key] = information
        score[key] = len(skills)
    return num


def sort_summarize_resumes(score,summary) :

    titles = ["~ NAME:", "~ EMAIL:", "~ NUMBER:", "~ QUALIFICATIONS:", "~ SKILLS:"]
    if score:
        temp = sorted(score.items(), key=lambda x: x[1], reverse=True)
        score = dict(temp)
    selected_resumes = {}
    i = 1
    for key in score.keys():
        for k, v in summary.items():
            if k == key:
                selected_resumes[k] = v
                new_key = "Resume_" + str(i) + "_summary" + ".txt"
                selected_resumes[new_key] = selected_resumes.pop(k)
        i += 1
    n = 1
    file_path = ''
    for k, v in selected_resumes.items():
        file_path = os.path.join(settings.MEDIA_ROOT, 'selected_resumes', k)
 
        f = open(file_path, "w")
        i = 0
        for info in v:
            if i == 5:
                break
            f.write(titles[i] + "\n")
            i += 1
            for x in info:
                f.write(str(x) + "\n")
        f.close()
        ext = os.path.splitext(v[-1][0])[-1].lower()
        file_name = "resume_" + str(n) + ext
        file_name = os.path.join(settings.MEDIA_ROOT, 'resumes' , file_name)
        os.rename(v[-1][0], file_name)
        shutil.move(file_name, os.path.join(settings.MEDIA_ROOT, 'selected_resumes'))
        n += 1