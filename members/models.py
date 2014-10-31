'''
Created on Sep 25, 2013

@author: siddhardha
'''
##################################################################################################################
from django.db import models, connection
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import User
from django.utils.datetime_safe import datetime
from django.db.models import Q
# net stop MySQLRK_1
# net start MySQLRK_1
##################################################################################################################
# SET SQL_AUTO_IS_NULL = 0
# http://www.mercurytide.co.uk/news/article/django-full-text-search/
##################################################################################################################
class SearchQuerySet(models.query.QuerySet):
    def __init__(self, model=None, fields=None, query=None, using=None):
        super(SearchQuerySet, self).__init__(model, query, using)
        self._search_fields = fields

    def search(self, searchString):
        meta = self.model._meta
        searchFields = self._search_fields

        # Get the table name and column names from the model
        # in `table_name`.`column_name` style
        # backend -> connection.ops
        columns = [meta.get_field(name, many_to_many=False).column for name in searchFields]
        table_name = connection.ops.quote_name(meta.db_table)
        full_names = ["%s.%s" % (table_name, connection.ops.quote_name(column)) for column in columns]

        # Create the MATCH...AGAINST expressions 
        # WITH QUERY EXPANSION
        fulltext_columns = ", ".join(full_names)
        match_expr = ("MATCH(%s) AGAINST (%%s)" % fulltext_columns)

        # Add the extra SELECT and WHERE options
#         relevance_column_name = table_name + '.' + connection.ops.quote_name('relevance')
        relevance_column_name = 'relevance'
        return self.extra(select={relevance_column_name: match_expr}, \
                          select_params=[unicode(searchString)], \
                          where=[match_expr], \
                          params=[unicode(searchString)], \
                          order_by = ['-' + relevance_column_name])

class SearchManager(models.Manager):
    def __init__(self, fields):
        super(SearchManager, self).__init__()
        self._search_fields = fields

    def get_query_set(self):
        return SearchQuerySet(self.model, self._search_fields)

    def search(self, searchString):
            return self.get_query_set().search(searchString)
        
##################################################################################################################
class Member(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    phone_no = models.CharField(max_length=13, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    status = models.IntegerField(default=0)
    expertises = models.ManyToManyField('Category', through="Expertise")  # category-wise expertise   
#     membership_date = models.DateField()
        
    def is_member(self):        # is bit 0 = 0, bit 1 = 0 and bit 2 = 0
        if (self.status & 7) == 0:
            return True
        else:
            return False
        
    def set_member(self):       # reset bit 0 = 0, bit 1 = 0 and bit 2 = 0
        self.status = self.status & (~7)
        
        print "%s set as member." % self.user.username
        
        return self.status
        
    def is_expert(self):        # is bit 0 = 1, bit 1 = 0 and bit 2 = 0
        if (self.status & 7) == 1:
            return True
        else:
            return False
        
    def set_expert(self):       # set bit 0 = 1 and reset bit 1 = 0 and bit 2 = 0
        self.status = self.status | 1
        self.status = self.status & (~6)
        
        print "%s set as expert." % self.user.username
        
        return self.status
 
##################################################################################################################           
class Expertise(models.Model):
    ex = ForeignKey('Member')
    cat = ForeignKey('Category')
    level = models.IntegerField(default=0)
    expertise = models.IntegerField(default=0)
    
    def gain_expertise(self, inc):
        self.expertise += inc
        self.save()
        
        print "Awarded expertise %d to %s", (inc, self.ex.user.username)
        
        return self.expertise            
 
##################################################################################################################          
class Category(models.Model):
    prnt_cat = ForeignKey('self', blank=True, null=True)
#     cats = models.ManyToManyField(through="Catkeys")        # category keywords
    name = models.CharField(max_length=50, unique=True)
    level = models.IntegerField(default=0)                  # either 0 or (1 + parent_category's level)
    
    def __unicode__(self):
        return u'%s' % (self.name)
    
#     def __unicode__(self):
#         return u'%s %d' % (self.name, self.level)

##################################################################################################################
class Catkeys(models.Model):
    cat = ForeignKey(Category)
    keyword = models.CharField(max_length=30)
    
    # Use a SearchManager for retrieving objects, and tell it which fields to search. 
    objects = SearchManager(('keyword',))

##################################################################################################################
class Grievance(models.Model):
    prnt_gr = ForeignKey('self', blank=True, null=True)         # parent grienvance's grievance_id
    ath = ForeignKey(Member, blank=False, null=False)           # author's member_id
    fnl_sl = ForeignKey('Solution', null=True)                  # final solution's solution_id
    level = models.IntegerField(default=0)                      # grievance level
    cats = models.ManyToManyField(Category, through="Griscat")  # grievance categories
    
    title = models.CharField(max_length=100)
    statement = models.CharField(max_length=10000)
    creation_tstmp = models.DateTimeField()                     # auto_now_add=True ... not applicable since every update will change this time
    resolution_tstmp = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(default=0)
    
    # Use a SearchManager for retrieving objects, and tell it which fields to search. 
    objects = SearchManager(('title', 'statement'))
    
    class Meta:
        ordering = ["-creation_tstmp"]
        
#    def get_user_grievance_parents(self):
#        return Grievance.objects.filter(ath=self.ath, prnt_gr__isnull=True)
    
#    def get_user_grievances(self):
#         return Grievance.objects.filter(ath=self.ath)

    def update_selected_solution(self, newlyRatedSolution):
        if newlyRatedSolution is not None and (self.fnl_sl is None or not newlyRatedSolution.is_rated() or newlyRatedSolution.get_satisfaction_rating() >= self.fnl_sl.get_satisfaction_rating()):
            if self.fnl_sl is not None:
                self.fnl_sl.set_not_selected()
                self.fnl_sl.save()
            
            self.fnl_sl = newlyRatedSolution
            print "Grievance#%d trying solution#%d." % (self.pk, self.fnl_sl.pk)
            
        self.set_solution_selected()
        self.save()
        
    def is_awaiting_review(self):       # is bit 0 = 0 and bit 1 = 0
        if (self.status & 3) == 0:
            return True
        else:
            return False
    
    def set_awaiting_review(self):      # reset bit 0 = 0 and bit 1 = 0
        self.status = self.status & (~3)
        return self.status
        
    def is_open(self):                  # is bit 0 = 1 and bit 1 = 0
        if (self.status & 3) == 1:
            return True
        else:
            return False
        
    def set_open(self):                 # set bit 0 = 1 and reset bit 1 = 0
        self.status = self.status | 1
        self.status = self.status & (~2)
        return self.status
        
    def is_closed_by_author(self):      # is bit 0 = 0 and bit 1 = 1
        if (self.status & 3) == 2:
            return True
        else:
            return False
        
    def set_closed_by_author(self):     # reset bit 0 = 0 and set bit 1 = 1
        self.status = self.status & (~1)
        self.status = self.status | 2
        
        try:
            if self.fnl_sl is not None and self.fnl_sl.ath is not None and self.fnl_sl.ath.is_expert():
                selected_grs = Grievance.objects.filter(Q(id=self.pk) | Q(prnt_gr=self)).order_by('-level')
                selected_gr = selected_grs[0]
                
                relevantGriscats = Griscat.objects.filter(gr=self).distinct()
                if relevantGriscats is not None and len(relevantGriscats) > 0:
                    relevantCategories = relevantGriscats.values_list('cat', flat=True)
                    
                    expertises = Expertise.objects.filter(ex=selected_gr.fnl_sl.ath, cat__in=relevantCategories)
                    for expertise in expertises:
                        expertise.gain_expertise(selected_gr.fnl_sl.get_satisfaction_rating())
                        
        except Exception, e:
            print "Failed to award closing expertise. Caught: ", e
            
        self.resolution_tstmp = datetime.now()
        print "Grievance#%d closed by author." % self.pk
        
        if self.fnl_sl is not None and self.fnl_sl.is_rated():
            self.set_solution_finalized()
        
        return self.status
        
    def is_declined_by_moderator(self): # is bit 0 = 1 and bit 1 = 1
        if (self.status & 3) == 3:
            return True
        else:
            return False
        
    def set_declined_by_moderator(self):# set bit 0 = 1 and set bit 1 = 1
        self.status = self.status | 3
        print "Grievance#%d declined by moderator." % self.pk
        return self.status
        
#     def is_awaiting_solutions(self):    # is bit 2 = 0
#         if (self.status & 4) == 0:
#             return True
#         else:
#             return False
#          
#     def set_awaiting_solutions(self):   # reset bit 2 = 0
#         self.status = self.status & (~4)
#         return self.status
         
    def has_solution_finalized(self):   # is bit 2 = 1
        if (self.status & 4) == 4:
            return True
        else:
            return False
         
    def set_solution_finalized(self):   # set bit 2 = 1
        self.status = self.status | 4
        
        thisLvlSolutions = Solution.objects.none()
        if self.prnt_gr is not None:
            thisLvlSolutions = Solution.objects.filter(Q(gr=self) | Q(gr=self.prnt_gr)).filter(level=self.level)
        else:
            thisLvlSolutions = Solution.objects.filter(gr=self).filter(level=self.level)
        
        for thisLvlSolution in thisLvlSolutions:
            if thisLvlSolution.get_satisfaction_rating() > self.fnl_sl.get_satisfaction_rating():
                if self.fnl_sl.is_selected():
                    self.fnl_sl.set_not_selected()
                self.fnl_sl = thisLvlSolution
        
        self.fnl_sl.set_finalized()
        self.fnl_sl.save()
        
        print "Grievance#%d finalized solution#%d" % (self.pk, self.fnl_sl.pk)
        
        return self.status
         
    def has_solution_selected(self):    # is bit 3 = 1
        if (self.status & 8) == 8:
            return True
        else:
            return False
        
    def set_solution_selected(self):    # set bit 3 = 1
        self.status = self.status | 8
        
        print "Grievance#%d selected solution#%d" % (self.pk, self.fnl_sl.pk)
        
        self.fnl_sl.set_selected()
        self.fnl_sl.save()
        
        return self.status
    
    def set_solution_not_selected(self):# reset bit 3 = 0
        self.status = self.status & (~8)
        
#         self.fnl_sl = None
        
        return self.status
    
    def is_public(self):                # is bit 4 = 0
        if (self.status & 16) == 0:
            return True
        else:
            return False
        
    def set_public(self):               # reset bit 4 = 0
        self.status = self.status & (~16)
        
        if self.pk is not None:
            print "Grievance#%d set as public." % self.pk
        else:
            print "New grievance set as public."
        
        return self.status
        
    def is_private(self):               # is bit 4 = 1
        if (self.status & 16) == 16:
            return True
        else:
            return False
        
    def set_private(self):              # set bit 4 = 1
        self.status = self.status | 16
        
        if self.pk is not None:
            print "Grievance#%d set as private." % self.pk
        else:
            print "New grievance set as private."
        
        return self.status
    
    def set_depth_of_understanding(self, value):        # set status in bits 8,7,6
        if value > 0 and value <= 5:                    # 8   7  6  5  4 3 2 1
            self.status = self.status | (value * 32)    # 128 64 32 16 8 4 2 1
            
            if self.pk is not None:
                print "Grievance#%d demands expertise level %d." % (self.pk, value)
            else:
                print "New grievance demands expertise level %d." % value
            
        return self.status
    
    def get_depth_of_understanding(self):               # get rating value from bits 7,6,5
        return (self.status & 224)/32

##################################################################################################################    
class Griscat(models.Model):
    gr = ForeignKey(Grievance)      # grievance_id
    cat = ForeignKey(Category)      # associated category's category_id

##################################################################################################################    
class Author(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=75)
    phone_no = models.CharField(max_length=13) 

##################################################################################################################
class Solution(models.Model):
    gr = ForeignKey(Grievance)                  # associated grievance's grievance_id
    level = models.IntegerField(default=0)      # solution-grievance level
    ath = ForeignKey(Member, null=True)         # author's member_id
    vath = ForeignKey(Author, null=True)        # visitor's temporary_id
    
    statement = models.CharField(max_length=10000)
    expected_outcome = models.CharField(max_length=5000)
    actual_outcome = models.CharField(max_length=5000)
    cost = models.IntegerField(default=0)
    currency = models.CharField(max_length=20)
    creation_tstmp = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=0)
    
    def is_selected(self):          # is bit 0 = 1
        if (self.status & 1) == 1:
            return True
        else:
            return False
        
    def set_selected(self):         # set bit 0 = 1
        self.status = self.status | 1
        
        print "Solution#%d selected." % self.pk
        
        return self.status
    
    def set_not_selected(self):     # reset bit 0 = 0
        self.status = self.status & (~1)
        
        print "Solution#%d un-selected." % self.pk
        
        return self.status
        
    def is_finalized(self):         # is bit 1 = 1
        if (self.status & 2) == 2:
            return True
        else:
            return False
        
    def set_finalized(self):        # set bit 1 = 1
        self.status = self.status | 2
        
        print "Solution#%d finalized." % self.pk
        
        return self.status
    
    def set_not_finalized(self):    # reset bit 1 = 0
        self.status = self.status & (~2)
        
        print "Solution#%d un-finalized." % self.pk
        
        return self.status
    
    def set_satisfaction_rating(self, value):  # set status in bits 4,3,2
        if value > 0 and value <= 5:
            self.status = self.status | (value  * 4) 
            print "Solution#%d rated %d." % (self.pk, value)
            self.set_not_selected()
            
            try:
                if self.ath is not None and self.ath.is_expert():
                    relevantGriscats = Griscat.objects.filter(gr=self.gr).distinct()
                    if relevantGriscats is not None and len(relevantGriscats) > 0:
                        relevantCategories = relevantGriscats.values_list('cat', flat=True)
                    
                        expertises = Expertise.objects.filter(ex=self.ath, cat__in=relevantCategories)
                        for expertise in expertises:
                            expertise.gain_expertise(value)
                            
            except Exception, e:
                print "Failed to award trial expertise. Caught: ", e
            
        return self.status
    
    def get_satisfaction_rating(self):          # get rating value from bits 4,3,2
        return (self.status & 28)/4             # 4  3 2 1 0
                                                # 16 8 4 2 1
    def is_rated(self):                         # is rating > 0
        if 0 < self.get_satisfaction_rating():
            return True
        return False
##################################################################################################################