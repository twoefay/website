import os
import requests
import json

from hyper.contrib import HTTP20Adapter
from hyper import HTTPConnection
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse

from .forms import CustomerForm
from .forms import LoginForm
from .forms import BackupForm
from .models import Customer

c = HTTPConnection ('twoefay.xyz', port=443)

def index(request):
    if 'member_id' in request.session:
        member_id = request.session['member_id']
    else:
        request.session['member_id'] = 'Guest'
        member_id = request.session['member_id']

    return render(request, 'index.html', {'member_id':member_id})

def customer_new (request, template='customer_new.html'):
    if 'member_id' in request.session:
        if request.session['member_id'] != 'Guest':
            return HttpResponse('youre already logged in!')
    else:
        request.session['member_id'] = 'Guest'

    member_id = request.session['member_id']

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            email = form.cleaned_data.get('email')
            phone = form.cleaned_data.get('phone')
            token = ''
            
            try:
                message = '{"username":"' + username + '", "email":"' + email + '", "phone":"' + phone + '"}'
                print ('making post request')
                c.request('POST', '/register', body=message.encode())
                resp = c.get_response()
                print ('got response')
                decoded = (resp.read()).decode()
                json_response = json.loads(decoded)
                print (json_response)
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
                return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'onefactor'}) 
            return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'success'}) 

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
            return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'error'}) 
    else:
        template = 'login.html'
        form_type = 'login'
        form = LoginForm()

    if request.method == 'POST':
        if form_type == 'login': 
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')

                try:
                    customer = Customer.objects.get(username=username)
                except Customer.DoesNotExist:
                    customer = None
            
                if customer == None:
                    member_id = 'Guest'
                    request.session['member_id'] = member_id
                    if 'auth_stage' in request.session:
                        del request.session['auth_stage']
                    return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'noaccount'}) 
                else:
                    if password == customer.password:
                        if customer.token == '':
                            request.session['member_username'] = username
                            request.session['auth_stage'] = 'Logged In'
                            return HttpResponse('successful one-factor twoefay.')
                        #TODO Include link to sign up for two-factor on a one-factor account
                        else:
                            verified = 'failure'
                        try:
                            message = '{"token":"'+ customer.token + '"}' 
                            c.request('POST', '/login', body=message.encode())
                            print ('made request')
                            resp = c.get_response()
                            print ('got response')
                            decoded = (resp.read()).decode()
                            print (decoded)
                            print (type(decoded))
                            json_response = json.loads(decoded)
                            print (json_response)
                            verified = json_response['login']

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
                            member_id = 'Guest'
                            request.session['member_id'] = member_id
                            if 'auth_stage' in request.session:
                                del request.session['auth_stage']
                            return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'failtwoefay'}) 
                        elif verified == '':
                            member_id = 'Guest'
                            request.session['member_id'] = member_id
                            del request.session['auth_stage']
                            return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'notwoefay'}) 
                        elif verified == 'unverified':
                            request.session['member_id'] = username
                            request.session['auth_stage'] = 'Backup'
                            return render(request, 'backup.html', {'form':BackupForm()})
                        else:
                            return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'error'}) 
                    else:
                        member_id = 'Guest'
                        request.session['member_id'] = member_id
                        if 'auth_stage' in request.session:
                            del request.session['auth_stage']
                        return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'wrongpwd'}) 

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
                if 'member_id' in request.session and request.session['member_id'] != 'Guest':
                    username = request.session['member_id']
                    print ('username: ' + username)
                    login = 'failure'
                    
                    try:
                        message = '{"username":"' + username + '", "otp":"' + otp + '"}'
                        print ('making post request')
                        c.request('POST', '/backup', body=message.encode())
                        print ('made request')
                        resp = c.get_response()
                        print ('got response')
                        decoded = (resp.read()).decode()
                        print ('decoded: ' + decoded)
                        print (len(decoded))
                        if len(decoded) != 0:
                            json_response = json.loads(decoded)
                            print (json_response)
                            login = json_response['login']
                    except requests.exceptions.ReadTimeout as e:
                            print ("backup read timeout")
                    except requests.exceptions.ConnectTimeout as e:
                            print ("backup connect timeout")
                    except requests.exceptions.RequestException as e:
                            print ("backup request exception")

                    if login == 'success':
                        request.session['auth_stage'] = 'Logged In'
                        return HttpResponse('successful sign in' + username)
                    else:
                        if 'auth_stage' in request.session:
                            del request.session['auth_stage']
                        return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'failbackup'}) 
                else:
                    return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'error'}) 
                    print('no member id but backup auth_stage session flag. big error')
            else:
                return render(request, 'big-notice.html', {'member_id':member_id, 'notice': 'error'}) 

    else: 
        if form_type == 'login':
            form = LoginForm()
        elif form_type == 'backup':
            form = BackupForm()

    return render(request, template, {'form':form})

def logout (request):
    if 'auth_stage' in request.session:
        del request.session['auth_stage']
    request.session['member_id'] = 'Guest'
    return render(request, 'big-notice.html', {'member_id':'Guest','notice': 'logout'}) 
