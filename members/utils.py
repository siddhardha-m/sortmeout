'''
Created on Nov 25, 2013

@author: Rohit
'''
##################################################################################################################
from members.models import Grievance, Griscat, Expertise, Category, Catkeys, Solution
from django.core.context_processors import csrf
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http.response import HttpResponseRedirect
from django.db.models import Q
import re

##################################################################################################################
def requires_login(view):
    def new_view(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login/')
        return view(request, *args, **kwargs)
    return new_view

##################################################################################################################
def add_csrf(request, ** kwargs):
#     try:
#         del request.session['keypress']
#     except:
#         print ""
    d = dict(user=request.user, ** kwargs)
    d.update(csrf(request))
    return d

##################################################################################################################
def mk_paginator(request, items, num_items):
    if items is None:
        return None
    
    paginator = Paginator(items, num_items)
    
    try:
        page = int(request.GET.get("page", '1'))
    except ValueError: 
        page = 1

    try:
        items = paginator.page(page)
    except (InvalidPage, EmptyPage):
        items = paginator.page(paginator.num_pages)
    return items

##################################################################################################################
def extract_categories_from_string(commaStr):
    pattern = re.compile('\s*,\s*')
    categoryNames = pattern.split(commaStr)
    categories = Category.objects.filter(name__in=categoryNames).order_by('-level')
    
    return categories

##################################################################################################################
# Algorithm: get_grievances
# scope ...
# case 0: public forum
# case 1: member forum
# case 2: expert forum
    
# required ...
# case 0: no search
# case 1: category search (without searchString)    => filter by category
# case 2: string search (without category)          => relevance-rank grievances on searchString
# case 3: string search, with category              => relevance-rank catkeys on searchString
#                                                   => then relevance rank grievances on catkeys+searchString
##################################################################################################################
def get_grievances(scope, searchString, categories, mId, member):
        
    isStringSearch = False
    isCategorySearch = False
    if (searchString is not None) and (len(searchString.strip()) > 0):
        isStringSearch = True
    if (categories is not None) and (len(categories) > 0):
        isCategorySearch = True
    
    keys = []
    if isCategorySearch and isStringSearch:
        relevantCatkeys = Catkeys.objects.search(searchString)
        if (relevantCatkeys is not None) and (len(relevantCatkeys) > 0):
            for catkey in relevantCatkeys:
                catkeySet = set(keys)
                if not catkey.keyword in catkeySet:
                    keys.append(catkey.keyword)
            
    # public forum
    if scope == 0:
        # no search
        if (not isCategorySearch) and (not isStringSearch):
            return Grievance.objects.extra(where=["status & 16 = 0"]).filter(level=0).order_by("-creation_tstmp")
        
        # category search
        elif isCategorySearch and (not isStringSearch):
            return Grievance.objects.extra(where=["status & 16 = 0"]).filter(cats__in=categories, level=0).order_by("-creation_tstmp").distinct()
        
        # string search
        elif isStringSearch and (not isCategorySearch):
            return Grievance.objects.search(searchString).extra(where=["status & 16 = 0"]).filter(level=0)
        
        # category based string search
        else:                       
            grievances = list(Grievance.objects.search(searchString).extra(where=["status & 16 = 0"]).filter(level=0))
            if (keys is not None) and (len(keys) > 0):
                for key in keys:
                    tempGrievances = list(Grievance.objects.search(key).extra(where=["status & 16 = 0"]).filter(level=0))
                    for tempGrievance in tempGrievances:
                        grievanceSet = set(grievances)
                        if not tempGrievance in grievanceSet:
                            grievances.append(tempGrievance)
                    
#                     grievances.extend(tempGrievances)
            
            return grievances
    
    # member forum
    elif scope == 1:
        # no search
        if (not isCategorySearch) and (not isStringSearch):
            return Grievance.objects.filter(ath=mId, level=0).order_by("-creation_tstmp")
        
        # category search
        elif isCategorySearch and (not isStringSearch):
            return Grievance.objects.filter(ath=mId, cats__in=categories, level=0).order_by("-creation_tstmp").distinct()

        # string search
        elif isStringSearch and (not isCategorySearch):
            return Grievance.objects.search(searchString).filter(ath=mId, level=0)
        
        # category based string search
        else:            
            grievances = list(Grievance.objects.search(searchString).extra(where=["status & 16 = 0"]).filter(ath=mId, level=0))
            if (keys is not None) and (len(keys) > 0):
                for key in keys:
                    tempGrievances = list(Grievance.objects.search(key).extra(where=["status & 16 = 0"]).filter(ath=mId, level=0))
                    for tempGrievance in tempGrievances:
                        grievanceSet = set(grievances)
                        if not tempGrievance in grievanceSet:
                            grievances.append(tempGrievance)
                    
#                     grievances.extend(tempGrievances)
            
            return grievances
        
    # expert forum
    elif scope == 2:
        expertises = Expertise.objects.filter(ex=member).order_by("-level")
        
        maxRelevantExpertiseLevel = 0
        relevantExpertises=[]
        relevantCategories=[]
        if not isCategorySearch:
            relevantExpertises = expertises
            relevantCategories = expertises.values_list('cat', flat=True)
            
            for expertise in expertises:
                if maxRelevantExpertiseLevel < expertise.level:
                    maxRelevantExpertiseLevel = expertise.level
            
        else:
            for expertise in expertises:
                categorySet = set(categories)
                if expertise.cat in categorySet:
                    relevantExpertises.append(expertise)
                    relevantCategories.append(expertise.cat)
                    
                    if maxRelevantExpertiseLevel < expertise.level:
                        maxRelevantExpertiseLevel = expertise.level
        
        relevantExpertiseClause = "(status & 224) <= " + str(32 * maxRelevantExpertiseLevel)
        openGrievancesClause = "(status & 3) = 1"       
#                 for category in categories:
#                     if expertise.cat == category.pk:
#                         relevantExpertises.append(category.pk)
                        
        griscats = Griscat.objects.filter(cat__in=relevantCategories, gr__level=0).distinct()#list(list(expertises.values_list('cat', flat=True)))
        if griscats is None:
            griscats = Griscat.objects.none()
        grIds = griscats.values_list('gr', flat=True)
                                          
        # no search
        if (not isCategorySearch) and (not isStringSearch):
            return Grievance.objects.filter(pk__in=grIds).extra(where=[relevantExpertiseClause]).extra(where=[openGrievancesClause]).order_by("-creation_tstmp").distinct()
        
        # category search
        elif isCategorySearch and (not isStringSearch):
            return Grievance.objects.filter(cats__in=categories, pk__in=grIds).extra(where=[relevantExpertiseClause]).extra(where=[openGrievancesClause]).order_by("-creation_tstmp").distinct()

        # string search
        elif isStringSearch and (not isCategorySearch):
            return Grievance.objects.search(searchString).filter(pk__in=grIds).extra(where=[relevantExpertiseClause]).extra(where=[openGrievancesClause]).distinct()
        
        # category based string search
        else:            
            grievances = list(Grievance.objects.search(searchString).filter(pk__in=grIds).extra(where=[relevantExpertiseClause]).extra(where=[openGrievancesClause]).distinct())
            if (keys is not None) and (len(keys) > 0):
                for key in keys:
                    tempGrievances = list(Grievance.objects.search(key).filter(pk__in=grIds).extra(where=[relevantExpertiseClause]).extra(where=[openGrievancesClause]).distinct())
                    for tempGrievance in tempGrievances:
                        grievanceSet = set(grievances)
                        if not tempGrievance in grievanceSet:
                            grievances.append(tempGrievance)
                            
#                     grievances.extend(tempGrievances)
            
            return grievances
    return None

# def filter_expertise_relevant_grievances(categoryRelevantGrievances, relevantExpertises):
#     grievances = []
#     
#     for relevantExpertise in relevantExpertises:
#         for grievance in categoryRelevantGrievances:
#             desiredExpertise = grievance.get_depth_of_understanding()
#             if grievance.cat == relevantExpertise.cat and desiredExpertise <= relevantExpertise.level:
#                 grievances.append(grievance)
#                 
#     return grievances
 
##################################################################################################################
def get_griscats(grievances):
    if grievances is not None:
#         return Griscat.objects.filter(gr__in=list(list(grievances.values_list('id'))))#, flat=True
        grids = []
        for grievance in grievances:
            grids.append(grievance.pk)
        return Griscat.objects.filter(gr__in=grids).order_by('-cat__level')#, flat=True
    else:
        return None

##################################################################################################################
def get_category_names(categories):
    if categories is not None:
        return Category.objects.filter(id__in=list(list(categories.values_list('cat', flat=True)))).order_by("-level")
    else:
        return None

##################################################################################################################
# Algorithm: expand_grievance
# fetch all interim grievances against this grievance (must be level 0)
# fetch finalized solution for all but the (last) outstanding grievance
# sort solutions proposed for the outstanding grievance by experts on ...
#     author's expertise's category-level, author's expertise's level in that category, author's expertise's expertise in that category 
################################################################################################################## 
def expand_grievance(grievance):
    grievances = Grievance.objects.none()
    if (grievance is not None) and (grievance.level == 0):
        grievances = list(Grievance.objects.filter(Q(id=grievance.pk) | Q(prnt_gr=grievance)).order_by('level'))
#         grievances.append(grievance)
# 
#         for thisLevelGrievance in grievances:
#             next_level_grievance = Grievance.objects.filter(prnt_gr=thisLevelGrievance.pk)
#             grievances.append(next_level_grievance)
        
        solutions = []
        expertSolutions = []
        visitorSolutions = []
        for thisLevelGrievance in grievances:
            if thisLevelGrievance.has_solution_finalized():
                finalized_solutions = Solution.objects.filter(pk = thisLevelGrievance.fnl_sl.pk)
                for finalized_solution in finalized_solutions:
                    solutionSet = set(solutions)
                    if not finalized_solution in solutionSet:
                        solutions.append(finalized_solution)
                
            #elif thisLevelGrievance.is_open() and thisLevelGrievance.is_awaiting_solutions():
            elif thisLevelGrievance.is_open():
                proposedSolutions = Solution.objects.filter(gr = grievance, level=thisLevelGrievance.level).select_related('member', 'author')
                
                griscats = get_griscats(grievances)
                if (griscats is not None) and (len(griscats) > 0):
#                     for griscat in griscats:
                        expertSolutions = list(proposedSolutions.filter(ath__isnull = False).order_by('-ath__expertises__category__level', '-ath__expertises__level', '-ath__expertises__expertise', '-status'))
                        for expertSolution in expertSolutions:
                            solutionSet = set(solutions)
                            if not expertSolution in solutionSet:
                                solutions.append(expertSolution)
#                                 solutions.extend(expertSolutions)      # possible only because only the last grievance can be the outstanding one
                        
                visitorSolutions = list(proposedSolutions.filter(vath__isnull = False).order_by('-status'))
                for visitorSolution in visitorSolutions:
                    solutionSet = set(solutions)
                    if not visitorSolution in solutionSet:
                        solutions.append(visitorSolution)
#                 solutions.extend(visitorSolutions)             # possible only because only the last grievance can be the outstanding one
             
        return grievances, solutions

    else:
        return None, None 
##################################################################################################################