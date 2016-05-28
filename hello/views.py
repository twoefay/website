import os
import requests
import json

from hyper.contrib import HTTP20Adapter
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse

from .forms import CustomerForm
from .forms import LoginForm
from .forms import BackupForm
from .models import Customer

def index(request):
    r = requests.post('http://twoefay.xyz:8080/register', json={'username' : 'test', 'email': 'email', 'phone':'phone'})
    print (r.json()['authenticated'])
    return HttpResponse('hi')
    #r = requests.get('https://lh6.ggpht.com/8R2VbnmJNqIHQZDB9gJ5FgnYlFcUO1c14BRQT2yahNKIDo1AXryjqX2waWt2cU-GPw=w300')
    #print r.text
    #return HttpResponse('<pre>' + r.text + '</pre>')

    #times = int(os.environ.get('TIMES',3))
    #return HttpResponse('Hello! ' * times)

def customer_new (request, template='customer_new.html'):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            if username:
                print('cleaned username:' + username)
            else:
                print('no username')
            password = form.cleaned_data.get('password')
            if password:
                print('cleaned password: ' + password)
            else:
                print('no password')
            email = form.cleaned_data.get('email')
            if email:
                print('cleaned email: ' + email)
            else:
                print('no email')
            phone = form.cleaned_data.get('phone')
            if phone:
                print('cleaned phone: ' + phone)
            else:
                print('no phone')

            token = ''
            
            try:
                #TODO For PROD:
                #s = requests.Session()
                #s.mount("https://twoefay.xyz", HTTP20Adapter())
                #r = s.post("https://twoefay.xyz/register", json={'username':username, 'email':email, 'phone':phone})
                
                #For test env:
                r = requests.post('http://http.test.twoefay.xyz/register', json={'username':username, 'email':email, 'phone':phone})
                print (r.content)
                json_response = r.json()
                print (json_response['token'])
                token = json_response['token']
            except requests.exceptions.ConnectTimeout as e:
                print ("Signup connect timeout")
            except requests.exceptions.ReadTimeout as e:
                print ("Signup read timeout")
            except requests.exceptions.RequestException as e:
                print ("Signup request exception")
                
            customer = Customer(username=username, password=password, email=email, phone=phone, token=token)
            customer.save()
            
            if token == '':
                return HttpResponse("Sign up successful but no twoefay")
                #return render(request, 'half_success.html')
            return HttpResponse("Sign up successful")
            #return render(request, 'success.html') 

    else:
        form = CustomerForm()
    
    return render(request, template, {'form':form})

#TODO Remove in PROD
def success(request):
    return render(request, 'success.html')

def login(request):
    print('log in time!')
    form_type = ''

    if 'auth_stage' in request.session:
        print ('auth_stage : ' + request.session['auth_stage'])
        if request.session['auth_stage'] == 'Backup':
            template = 'backup.html'
            form_type = 'backup'
            form = BackupForm()
        elif request.session['auth_stage'] == 'Logged In':
            print ('you are already logged in')
            #TODO: Give them option to log out, don't auto log them out
            del request.session['auth_stage']
            return HttpResponse('you already logged in. go log out first')
            #template = 'login.html'
            #form_type = 'login'
            #form = LoginForm()
        else:
            print ('are they equal ' + request.session['auth_stage'] + ' to ' + 'Backup')
            del request.session['auth_stage']
            print ('del request session')
            return HttpResponse('this should never happen')
    else:
        template = 'login.html'
        form_type = 'login'
        form = LoginForm()

    if request.method == 'POST':
        if form_type == 'login': 
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
            if username:
                print('cleaned username:' + username)
            else:
                print('no username')
            password = form.cleaned_data.get('password')
            if password:
                print('cleaned password: ' + password)
            else:
                print('no password')

            try:
                customer = Customer.objects.get(username=username)
            except Customer.DoesNotExist:
                customer = None
            
            if customer == None:
                return HttpResponse('username does not exist. please go sign up for an account')
            else:
                if password == customer.password:
                    if customer.token == '':
                        request.session['member_username'] = username
                        request.session['auth_stage'] = 'Logged In'
                        return HttpResponse('successful one-factor twoefay.')
                        #TODO Include link to sign up for two-factor on a one-factor account
                    else:
                        verified = 'False'
                        try:
                            r = requests.post('http://http.test.twoefay.xyz/login', json={'token':customer.token})
                            print (r.json()['login'])
                            json_response = r.json()
                            #TODO Remove in PROD
                            verified = json_response['login']
                            #verified = 'unverified'
                            print('login success/failure/unverified: ' + verified)
                        except requests.exceptions.ReadTimeout as e:
                            print ("Login read timeout")
                        except requests.exceptions.ConnectTimeout as e:
                            print ("Login connect timeout")
                        except requests.exceptions.RequestException as e:
                            print ("Login request exception")

                        if verified == 'success':
                            request.session['member_username'] = username
                            request.session['auth_stage'] = 'Logged In'
                            return HttpResponse('successful sign in with twoefay')
                        elif verified == 'failure':
                            if 'member_id' in request.session:
                                del request.session['member_id']
                            if 'auth_stage' in request.session:
                                del request.session['auth_stage']
                            return HttpResponse('failure sign in with twoefay: you didnt authenticate with app, but you have one installed on your phone')
                        elif verified == '':
                            del request.session['member_id']
                            del request.session['auth_stage']
                            return HttpResponse('failure sign in with twoefay: twoefay server is down')
                        elif verified == 'unverified':
                            request.session['member_id'] = username
                            request.session['auth_stage'] = 'Backup'
                            return render(request, 'backup.html', {'form':BackupForm()})
                        else:
                            return HttpResponse('ERROR: This should not happen ever.')
                else:
                    if 'member_id' in request.session:
                        del request.session['member_id']
                    if 'auth_stage' in request.session:
                        del request.session['auth_stage']
                    return HttpResponse('password is incorrect!')

        if form_type == 'backup':
            form = BackupForm(request.POST)
            print ('customer submitted form')
            print (request.session['auth_stage'])
            print (request.session['member_id'])
            if form.is_valid():
                otp = form.cleaned_data.get('otp')
                if otp:
                    print('cleaned otp:' + otp)
                else:
                    print('no otp')
                if 'member_id' in request.session:
                    username = request.session['member_id']
                    print ('username: ' + username)
                    r = requests.post('http://http.test.twoefay.xyz/backup', json={'username':username, 'otp':otp})
                    print (r.content)
                    json_response = r.json()
                    print (json_response['login'])
                    login = json_response['login']
                    if login == 'success':
                        request.session['auth_stage'] = 'Logged In'
                        return HttpResponse('successful sign in' + username)
                    else:
                        if 'auth_stage' in request.session:
                            del request.session['auth_stage']
                        return HttpResponse('unsuccessful backup sign in')
                else:
                    return HttpResponse('no member id but backup auth_stage session flag. big error')
            else:
                return HttpResponse('form invalid')

    else: 
        if form_type == 'login':
            form = LoginForm()
        elif form_type == 'backup':
            form = BackupForm()

    return render(request, template, {'form':form})

def logout (request):
    if 'auth_stage' in request.session:
        del request.session['auth_stage']
    if 'member_id' in request.session:
        del request.session['member_id']
    return HttpResponse('logged out')

def backup_deprecated(request, template='backup.html'):
    print ('serve backup page')
    if 'auth_stage' in request.session:
        if request.session['auth_stage'] == 'Logged In':
            print ('auth_stage set to logged in')
            return HttpResponse('You are already logged in...')
        if request.session['auth_stage'] == 'Backup':
            print ('auth_stage set to Backup')
            form = BackupForm()
            if request.method == 'POST':
                form = BackupForm(request.POST)
                print ('customer submitted form')
                if form.is_valid():
                    otp = form.cleaned_data.get('otp')
                    if otp:
                        print('cleaned otp:' + otp)
                    else:
                        print('no otp')
                    if 'member_id' in request.session:
                        username = request.session['member_id']
                        print ('username: ' + username)
                        r = requests.post('http://http.test.twoefay.xyz/backup', json={'username':username, 'otp':otp})
                        print (r.content)
                        json_response = r.json()
                        print (json_response['login'])
                        login = json_response['login']
                        if login == 'success':
                            return HttpResponse('successful sign in' + username)
                        else:
                            return HttpResponse('unsuccessful backup sign in')
                    else:
                        return HttpResponse('no member id but backup auth_stage session flag. big error')
                else:
                    return HttpResponse('form invalid')
            else:
                form = BackupForm()
            return render(request, template, {'form' : form})

    else:
        return HttpResponse('You do not need a backup method since you have not logged in one factor yet. Please visit the login page')



#def db(request):

#    greeting = Greeting()
#    greeting.save()

#    greetings = Greeting.objects.all()

#    return render(request, 'db.html', {'greetings': greetings})

