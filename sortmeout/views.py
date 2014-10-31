'''
Created on Sep 25, 2013

@author: siddhardha
'''
##################################################################################################################
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import login
from django.shortcuts import HttpResponseRedirect

from members.forms import MemberLoginForm
from django.contrib.auth import authenticate
from members.models import Member
from django.core.urlresolvers import reverse
from members.views import add_csrf
from django.contrib.auth.views import logout

##################################################################################################################
def thankyou(request):
    return render_to_response('thankyou.html', context_instance=RequestContext(request))

##################################################################################################################
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('sortmeout.views.login_view'))
#     loginform = MemberLoginForm()
#     dictionary = add_csrf(request, form=loginform)
#     return HttpResponseRedirect('/signin/')
#     return render_to_response('index.html', dictionary)

##################################################################################################################
def login_view(request):
    loginform = MemberLoginForm()
    
    mId = -1
    member = None
    try:
        mId = request.session['member_id']
        member = request.session['member']
    except:
        mId = -1
        member = None
    
    if request.method == 'POST':
        keypress = request.POST['keypress']
        
        if keypress == 'sign(me)up':
#             return HttpResponseRedirect('/signup/member/')
            return HttpResponseRedirect(reverse('members.views.signup_view', args=['member', ]))
#             return HttpResponseRedirect(reverse('/signup/', args=['member']))
        
        elif keypress == 'log(me)in':
            loginform = MemberLoginForm(request.POST)
            if loginform.is_valid():
                username = loginform.cleaned_data['username']
                password = loginform.cleaned_data['password']
                
                user = authenticate(username = username, password = password)
            
                if user is None:
                    loginform._errors["username"] = loginform.error_class(["Oops!!! Could not log(you)in. Please check your login credentials"])
            
                else:
                    if user.is_active:
                        login(request, user)
                        
                        member = Member.objects.get(user_id=user.id)
                        if member.is_member():
                            memberType = "Member"
                        elif member.is_expert():
                            memberType = "Expert"
                        else:
                            memberType = "User of unknown memberType"
                        print("%s %s mId#%d logged in." % (memberType, user.username, user.id))
                        
                        request.session['member_id'] = user.id
                        try: 
                            request.session['member'] = member
                        except Exception, e:
                            print "Caught:", e

#                         return HttpResponseRedirect(reverse('/grievances/'))
#                         return HttpResponseRedirect('/grievances/')
                        if member.is_member():
                            return HttpResponseRedirect(reverse('members.views.all_grievances_view', args=['private_forum', ]))
#                             return all_grievances_view(request, scope="private_forum")
                        elif member.is_expert():
                            return HttpResponseRedirect(reverse('members.views.all_grievances_view', args=['expert_forum', ]))
#                             return all_grievances_view(request, scope="expert_forum")
                            
                    else:
                        loginform._errors["username"] = loginform.error_class(["Oops!!! Could not log(you)in. Please check your login credentials"])
#                         raise loginform.ValidationError("Oops! Could not log(you)in. Your account has been disabled.")
    
    dictionary = add_csrf(request, form=loginform, mId=mId, member=member, disableLogin=True)
    return render_to_response('index.html', dictionary)

##################################################################################################################
# def login_view(request):
#     errors = []
#     username = ''
#      
#     if 'keypress' in request.POST:
#         keypress = request.POST['keypress']
#          
#         if keypress == 'signmeup':
#             return HttpResponseRedirect('/signup/')
#          
#         elif keypress == 'logmein':
#             if 'username' in request.POST:
#                 username = request.POST['username']
#                 if not username:
#                     errors.append('Please enter your username')
#                              
#             if 'password' in request.POST:
#                 password = request.POST['password']
#                 if not password:
#                     errors.append('Please enter your password')
#              
#             if len(errors) == 0:
#                 member = authenticate(username = username, password = password)
#                 if member is None:
#                     # the authentication system was unable to verify the username and password
#                     errors.append('Oops! Could not log(you)in. Please check your login credentials.')
#              
#                 else:
#                     # the password verified for the member
#                     if member.is_active:
#                         print("User is valid, active and authenticated")
#                         login(request, member)
#                         # Redirect to a success page.
#                     else:
#                         errors.append('Oops! Could not log(you)in. Your account has been disabled.')
#                  
#     return render_to_response('index.html', {'errors': errors, 'username': username,}, context_instance=RequestContext(request))
##################################################################################################################    