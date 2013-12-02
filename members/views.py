# from django.http import HttpResponse
from django import forms
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from members.models import Member, Grievance, Solution, Griscat, Expertise,\
    Category, Catkeys, Author
from django.contrib.auth.models import Group
from django.db.models import Q
from collections import OrderedDict

from members.forms import MemberLoginForm, MemberSignupForm1, MemberSignupForm2,\
    PostNewGrievanceForm1, PostNewGrievanceForm2, SolutionForm,\
    SearchForm, VisitorForm, SolutionFeedbackForm
from django.db import IntegrityError
from django.http.response import HttpResponseRedirect
from members.utils import get_griscats, get_grievances, get_category_names,\
    add_csrf, mk_paginator, expand_grievance, extract_categories_from_string
from django.core.urlresolvers import reverse
import itertools
import re

MEMBERS = 'members'

def category_lookup(request):
    categories = Category.objects.none()
    if request.method == 'POST':
        categoryStart = request.POST['lookup_text']
        pattern = re.compile('\s*,\s*')
        tokens = pattern.split(categoryStart)
        categoryStart = tokens[-1]
        
        if categoryStart is not None and not categoryStart == "":
            categories = Category.objects.filter(name__istartswith=categoryStart).order_by('-level') 
#         else:
#             categories = Category.objects.all()
        
    return render_to_response('category_lookup.html', {'categories' : categories})
        

def signup_view(request, signuptype='member'):
    signupform1 = MemberSignupForm1()
    signupform2 = MemberSignupForm2()
    signupform3 = PostNewGrievanceForm2()
    
    isMemberSignup = False      # default member signup
    isExpertSignup = False      # expert member signup
    if signuptype == 'expert':
        isExpertSignup = True
    else:
        isMemberSignup = True
    
    if request.method == 'POST':
        keypress = request.POST['keypress']
        
        if keypress == 'signmeup':
            isValidMemberSignupForm = False
            if isMemberSignup or isExpertSignup:
                signupform1 = MemberSignupForm1(request.POST)
                signupform2 = MemberSignupForm2(request.POST)
                isValidMemberSignupForm = signupform1.is_valid() and signupform2.is_valid()
            
            isValidExpertSignupForm = True
            if isExpertSignup:
                signupform3 = PostNewGrievanceForm2(request.POST)
                isValidExpertSignupForm = signupform3.is_valid()
        
            if isValidMemberSignupForm and isValidExpertSignupForm:
                username = signupform2.cleaned_data["username"]
                password = signupform2.cleaned_data["password"]
                email = signupform2.cleaned_data["email"]
                
                if isExpertSignup:
                    designation = signupform1.cleaned_data["designation"]
                    temp = signupform3.cleaned_data["category"]
                    categories = extract_categories_from_string(temp) 

                try:
                    print("Checking availability of entered username.")
                    newUser = User.objects.create_user(username, email, password)
                    newUser.first_name = signupform2.cleaned_data["first_name"]
                    newUser.last_name = signupform2.cleaned_data["last_name"]
                    #g = Group.objects.get(name=MEMBERS) 
                    #g.user_set.add(newUser)
                    newUser.save()
                    
                    if newUser.pk:
                        print("Signing up new user.")
                        phone = signupform1.cleaned_data["phone_no"]
                        address = signupform1.cleaned_data["address"]
                        dob = signupform1.cleaned_data["dob"]
                    
                        if isMemberSignup:
                            newMember = Member(user_id = newUser.id, phone_no = phone, address = address, dob = dob)
                            newMember.status = 0
                            newMember.status = newMember.set_member()
                            newMember.save()
                            
                        elif isExpertSignup:
                            newMember = Member(user_id = newUser.id, phone_no = phone, address = address, dob = dob, designation = designation)
                            newMember.status = 0
                            newMember.status = newMember.set_expert()
                            newMember.save()
                            
                            for category in categories:
                                newExpertise = Expertise(ex=newMember, cat=category, level=1, expertise=0)
                                newExpertise.save()
                            
                        print("Created new %s :%s_%s: mId#%d" % (signuptype, newMember.user.first_name, newMember.user.last_name, newMember.user.id))
#                         HttpResponseRedirect('/signin/')
#                         loginform = MemberLoginForm()
                        request.session.flush()
                        dictionary = add_csrf(request, form=MemberLoginForm())
                        return HttpResponseRedirect(reverse('sortmeout.views.login_view'))
#                         return render_to_response('index.html', dictionary)
                 
                    #else:
                        #raise forms.ValidationError('The username of your choice is unavailable. Please choose a different one.')
                
                except IntegrityError,e:
                    #raise signupform2.ValidationError('The username of your choice is unavailable. Please choose a different one.')
                    signupform2._errors["username"] = signupform2.error_class(["Oops!!! Cannot sign(you)up with this username. Please select a different one."])
                
                except Exception,e :
                    signupform2._errors["username"] = signupform2.error_class(["Oops!!! Failed to sign(you)up. Please try again later."])
                    print "Caught:", e
        
    request.session.flush()
    request.method = 'POST'
    dictionary = add_csrf(request, form1=signupform1, form2=signupform2, form3=signupform3, signuptype=signuptype)
    return render_to_response('registration.html', dictionary)
#     return render_to_response('registration.html', {'form1': signupform1, 'form2': signupform2, }, context_instance=RequestContext(request))

def all_grievances_view(request, scope):
    searchform = SearchForm()
    
    isPublicForum = True
    isPrivateForum = False
    isExpertForum = False
    if scope == 'private_forum':
        isPrivateForum = True
        scope_number = 1
    elif scope == 'expert_forum':
        isExpertForum = True
        scope_number = 2
    else:
        isPublicForum = True
        scope_number = 0
    
    isValidSearch = False
    searchString = None
    categories = None
    
    if request.method == 'POST':
        keypress = request.POST['keypress']
        if keypress == 'search': 
            searchform = SearchForm(request.POST)
            
            isValidSearch = searchform.is_valid()
            if isValidSearch:
                searchString = searchform.cleaned_data['srchStr'] 
                temp = searchform.cleaned_data['category']
                categories = extract_categories_from_string(temp)
    
    dictionary = None
    try:
        mId = request.session['member_id']
        member = request.session['member']
            
        grievances = get_grievances(scope_number, searchString, categories, mId, member)
        griscats = get_griscats(grievances)
        grievanceCategories = get_category_names(griscats)

        if not isExpertForum:
            grievances = mk_paginator(request, grievances, 20)
            dictionary = add_csrf(request, form=searchform, grievances=grievances, \
                                      griscats=griscats, categories=grievanceCategories, mId=mId, member=member)
            
        elif member.is_expert():
            grievanceAuthors = Member.objects.filter(pk__in=list(list(grievances.values_list('ath', flat=True))))
            
            grievances = mk_paginator(request, grievances, 20)
            dictionary = add_csrf(request, form=searchform, grievances=grievances, \
                                      grievanceAuthors=grievanceAuthors, griscats=griscats, \
                                      categories=grievanceCategories, mId=mId, member=member)

    except (KeyError, Exception):#, e:
#         unregisteredUser = User(pk=-1, first_name='anonymous')
#         member = Member(user=unregisteredUser)
        grievances = get_grievances(scope_number, searchString, categories, None, None)
        griscats = get_griscats(grievances)
        grievanceCategories = get_category_names(griscats)
        
        grievances = mk_paginator(request, grievances, 20)
        dictionary = add_csrf(request, form=searchform, grievances=grievances, \
                              griscats=griscats, categories=grievanceCategories, mId=-1)
            
    return render_to_response("grievance_list.html", dictionary)

def post_new_grievance_view(request):
#     action = reverse("new_grievance", args=[post_id])
    try:
        mId = request.session['member_id']
        postNewGrievanceForm1 = PostNewGrievanceForm1()
        postNewGrievanceForm2 = PostNewGrievanceForm2()
        
        if request.method == 'POST':
            keypress = request.POST['keypress']
        
            if keypress == 'submitnewgrievance':
                postNewGrievanceForm1 = PostNewGrievanceForm1(request.POST)
                postNewGrievanceForm2 = PostNewGrievanceForm2(request.POST)
                
                if(postNewGrievanceForm1.is_valid() and postNewGrievanceForm2.is_valid()):
                    title = postNewGrievanceForm1.cleaned_data["title"]
                    statement = postNewGrievanceForm1.cleaned_data["statement"]
                    temp = postNewGrievanceForm2.cleaned_data["category"]
                    categories = extract_categories_from_string(temp)
                    visibility = postNewGrievanceForm1.cleaned_data["status"]
                    
                    try:
                        newGrievance = Grievance(ath=request.session['member'], title=title, statement=statement)
                        newGrievance.status = 0
                        newGrievance.set_open()         # normally it should be awaiting_review
                        if visibility == 1:             # Grievance visibility set to private
                            newGrievance.set_private()
                        else:                           # Grievance visibility set to public
                            newGrievance.set_public()
                        newGrievance.save()
                        
                        for category in categories:
                            newGrisCat = Griscat(gr=newGrievance, cat=category)
                            newGrisCat.save() 
                    
                        if newGrievance.pk:
                            print("New grievance grId#%d from mId#%d" % (newGrievance.pk, mId))
                            return all_grievances_view(request, scope="member_forum")
                            
                        else:
                            postNewGrievanceForm1._errors["title"] = postNewGrievanceForm1.error_class(["Oops!!! Could not register your grievance. Please try again later."])
                            
                    except Exception, e:
                        postNewGrievanceForm1._errors["title"] = postNewGrievanceForm1.error_class(["Oops!!! Failed to register your grievance. Please try again later."])
                        print "Caught:", e
            
        dictionary = add_csrf(request, form1=postNewGrievanceForm1, form2=postNewGrievanceForm2)
        return render_to_response('newgrievance.html', dictionary)
#         return render_to_response('newgrievance.html', {'form1': postNewGrievanceForm1, 'form2': postNewGrievanceForm2}, context_instance=RequestContext(request))
    
    except KeyError:
        mId = -1
        
        loginform = MemberLoginForm()
        dictionary = add_csrf(request, form=loginform)
        return HttpResponseRedirect(reverse('sortmeout.views.login_view'))
#         return render_to_response('index.html', dictionary)
#     return render_to_response('index.html', {'form': loginform}, context_instance=RequestContext(request))
#     title = "Knock knock !!! Sort(Me)Out !!!"
#     subject = ''

#     return render_to_response("new_grievance.html", add_csrf(request, subject=subject, action=action, title=title))

# Algorithm ... grievance_view
#
# public grievance ...
# originating member - can view originating grievance with option to choose solutions and post interim grievance
# expert/ other member/ visitor - can view grievance with option to post solution
#
# private grievance ...
# originating member - can view originating grievance with option to choose solutions and post interim grievance
# relevant expert - can view grievance with option to post solution
# non-relevant expert/ other member/ visitor - cannot view grievance
def grievance_view(request, grId, slId):
    try:
        mId = request.session['member_id']
        member = request.session['member']
        
    except (KeyError, Exception):
        mId = -1
        unregisteredUser = User(pk=-1, first_name='anonymous')
        member = Member(user=unregisteredUser)
        
    grievances = Grievance.objects.filter(id=grId)
        
    try:
        slId = int(slId)
    except:
        slId = 0
    if slId > 0 and request.method == 'GET':
        selected_sls = Solution.objects.filter(id=slId)
        if (selected_sls is not None) and (len(selected_sls) > 0):
            selected_grs = Grievance.objects.filter(Q(id=grId) | Q(prnt_gr=grievances[0].pk)).order_by('-level')
            selected_gr = selected_grs[0]
            selected_gr.update_finalized_solution(selected_sls[0])
            selected_gr.set_solution_selected()
            selected_gr.save()
            
            selected_sl = selected_sls[0]
            selected_sl.set_selected()
            selected_sl.save()
    
    interimGrievanceForm = PostNewGrievanceForm1()
    newSolutionForm = SolutionForm()
    solutionFeedbackForm = SolutionFeedbackForm()
    visitorForm = VisitorForm()
    if request.method == 'POST':
        keypress = request.POST['keypress']
        
        if mId >= 0 and (keypress == 'closegrievance' or keypress == 'submitrevisedgrievance'):
            interimGrievanceForm = PostNewGrievanceForm1(request.POST)
            solutionFeedbackForm = SolutionFeedbackForm(request.POST)
            
            closable_gr = None
            closable_lvl = 0
            selected_sl = None
            
            try:
                closable_gr = request.session['closable_gr']
                closable_lvl = request.session['closable_lvl']
            except:
                print "Session does not contain a closable grievance, level."
                
            try:
                selected_sl = request.session['selected_sl']
                
                if selected_sl is not None:
                    if solutionFeedbackForm.is_valid():
                        actual_outcome = solutionFeedbackForm.cleaned_data["actual_outcome"]
                        rating = solutionFeedbackForm.cleaned_data["status"]
                        
                        selected_sl.actual_outcome = actual_outcome
                        selected_sl.set_satisfaction_rating(rating)
                        selected_sl.save()
                        
                        closable_grs = Grievance.objects.filter(prnt_gr=selected_sl.gr).order_by('-level')
                        closable_gr = closable_grs[0]
                        closable_lvl = closable_grs[0].level
                        closable_gr.update_finalized_solution(selected_sl)
                        print "New closable grievance identified at level %d." % (closable_lvl)
            except:
                print "Session does not contain a selected solution."
                
            if closable_gr is not None:
                closable_gr.set_solution_finalized()
                
            if keypress == 'closegrievance':
                selected_sl.gr.set_closed_by_author()
                    
            elif keypress == 'submitrevisedgrievance':
                if interimGrievanceForm.is_valid():
                    statement = interimGrievanceForm.cleaned_data["statement"]
                        
                    interimGrievance = Grievance(prnt_gr=grievances[0], ath=member, statement=statement, status=0, level=closable_lvl+1)
                    interimGrievance.save()
            
        elif keypress == 'submitnewsolution':
            newSolutionForm = SolutionForm(request.POST)
            
            if newSolutionForm.is_valid():
                statement = newSolutionForm.cleaned_data["statement"]
                expected_outcome = newSolutionForm.cleaned_data["expected_outcome"]
                
                if mId >= 0:
                    newSolution = Solution(gr=grievances[0], ath=member, statement=statement, expected_outcome=expected_outcome)
                    newSolution.save()
                    
                else:
                    visitorForm = VisitorForm(request.POST)
                
                    if visitorForm.is_valid():
                        first_name = visitorForm.cleaned_data["first_name"]
                        last_name = visitorForm.cleaned_data["last_name"]
                        email = visitorForm.cleaned_data["email"]
                        phone_no = visitorForm.cleaned_data["phone_no"]
                
                        visitorAuthor = Author.objects.none()
                        if first_name == "Anonymous" and last_name == "" and email == "" and phone_no == "":
                            visitorAuthor = Author.objects.get(pk=1)
                        else:
                            visitorAuthor = Author(first_name=first_name, last_name=last_name, email=email, phone_no=phone_no)
                            visitorAuthor.save()
                
                        newSolution = Solution(gr=grievances[0], vath=visitorAuthor, statement=statement, expected_outcome=expected_outcome)
                        newSolution.save()
        
#         if member.is_member():
    grievanceAuthor = ''
    isPublicGrievance = False
    
    if (grievances is not None) and (len(grievances) > 0):
        grievanceAuthor = Member.objects.get(pk=grievances[0].ath)
        isPublicGrievance = grievances[0].is_public()
        
    isRelevantExpert = False    
    if (not isPublicGrievance) and (mId >= 0) and (not mId == grievanceAuthor.user.id):      # if other than visitor or originating member/expert
        
        if not member.is_expert():                  # if not expert, deny access
            print "Access to %s's private grievance denied to member %s." % (grievanceAuthor.user.username, member.user.username)
            return HttpResponseRedirect(reverse('members.views.all_grievances_view', args=['public_forum', ]))
        
        else:                                       # if expert, check expertise
            expertises = Expertise.objects.filter(ex=member.user.id).order_by("-level")
            expertiseCategories = expertises.values_list('cat', flat=True)
            griscats = Griscat.objects.filter(gr=grId)
            grievanceCategories = griscats.values_list('cat', flat=True)
            
            for grievanceCategory in grievanceCategories:
                
                if isRelevantExpert:
                    break
                    
                for expertiseCategory in expertiseCategories:
                    if grievanceCategory == expertiseCategory:      # if expert in this grievance's category 
                        isRelevantExpert = True                     # validate as relevant expert
                        break
                        
            if not isRelevantExpert:                # if not relevant expert, deny access
                print "Access to %s's private grievance denied to expert %s." % (grievanceAuthor.user.username, member.user.username)
                return HttpResponseRedirect(reverse('members.views.all_grievances_view', args=['public_forum', ]))    
    
    # if accessible grievance
    grievances, solutions = expand_grievance(grievances[0])
    
    canBeClosed = False
    if grievances[-1].fnl_sl is not None and grievances[-1].fnl_sl.is_rated():
        canBeClosed = True
        request.session['closable_gr'] = grievances[-1]
        request.session['closable_lvl'] = grievances[-1].level
    else:
        canBeClosed = False
        request.session['closable_gr'] = None
        
#     for grievance in grievances:
#         if grievance.fnl_sl is None or (not grievance.fnl_sl.is_rated()):
#             canBeClosed = False
#             request.session['closable_gr'] = grievance
    
    solutionAuthors = []
    solutionIsSelected = False
    for solution in solutions:
        if solution.ath is not None:
            solutionAuthors.append(solution.ath)
        elif solution.vath is not None:
            solutionAuthors.append(solution.vath)
        
        if solution.is_selected():
            solutionIsSelected = True
            request.session['selected_sl'] = solution

    if mId == grievanceAuthor.user.id:          # if originating member/expert
        dictionary = add_csrf(request, grievances=grievances, solutions=solutions, grievanceAuthor=member, \
                              solutionAuthors=solutionAuthors, grisolaths=itertools.izip_longest(grievances, solutions, solutionAuthors), \
                              solutionIsSelected=solutionIsSelected, canBeClosed=canBeClosed, \
                              form=interimGrievanceForm, fbkform=solutionFeedbackForm, member=member, mId=mId)
    elif isRelevantExpert:                      # or if relevant expert
        dictionary = add_csrf(request, grievances=grievances, grievanceAuthor=grievanceAuthor, solutions=solutions, \
                              solutionAuthors=solutionAuthors, grisolaths=itertools.izip_longest(grievances, solutions, solutionAuthors), \
                              form=newSolutionForm, member=member, mId=mId)
    else:                                       # or if visitor
        dictionary = add_csrf(request, grievances=grievances, grievanceAuthor=grievanceAuthor, solutions=solutions, \
                              solutionAuthors=solutionAuthors, grisolaths=itertools.izip_longest(grievances, solutions, solutionAuthors),  \
                              form=newSolutionForm, visitorForm=visitorForm, member=member, mId=mId)

    return render_to_response("grievance.html", dictionary)
    
    
   
   
#             grievances = Grievance.objects.filter(Q(id=grievance_id) | Q(prnt_gr=grievance_id)).filter(ath=mId).order_by("-creation_tstmp")
#             solutions = Solution.objects.filter(gr__in=list(list(grievances.values_list('id', flat=True))))
#             solutionAuthors = Member.objects.filter(pk__in=list(list(solutions.values_list('ath', flat=True))))
            
#         elif member.is_expert():      
#             grievances = Grievance.objects.filter(Q(id=grievance_id) | Q(prnt_gr=grievance_id)).order_by("-creation_tstmp")
#             grievanceAuthor = Member.objects.get(pk=grievances[0].ath)
#             solutions = Solution.objects.filter(gr__in=list(list(grievances.values_list('id', flat=True))))
#             solutionAuthors = Member.objects.filter(pk__in=list(list(solutions.values_list('ath', flat=True))))
        
    
        
#         grievances = Grievance.objects.filter(id=grievance_id)
#         grievanceAuthor = Member.objects.get(pk=grievances[0].ath)
#         grievances, solutions = expand_grievance(grievances[0])
#         exIds = []
#         for solution in solutions:
#             exIds.append(solution.ath)
#         solutionAuthors = Member.objects.filter(pk__in=exIds)
#         
#         dictionary = add_csrf(request, grievances=grievances, grievanceAuthor=grievanceAuthor, solutions=solutions, solutionAuthors=solutionAuthors, form=SolutionForm(), member=member, mId=mId)
#         grievances = Grievance.objects.filter(Q(id=grievance_id) | Q(prnt_gr=grievance_id)).order_by("-creation_tstmp")
#         solutions = Solution.objects.filter(gr__in=list(list(grievances.values_list('id', flat=True))))
#         list(list(solutions.values_list('ath', flat=True)))
    
#     grievance = mk_paginator(request, grievances, 20)   

# def user_grievance_view(request):
#     mId = request.session['member_id']
#     solutions = Solution.objects.filter(gr=mId).order_by("-creation_tstmp")
#     solutions = mk_paginator(request, solutions, 20)
#     grievance = Grievance.objects.filter(mId=mId).order_by("-creation_tstmp")
#     
#     return render_to_response('grievance.html', add_csrf(request, grievance=grievance, mId=mId))