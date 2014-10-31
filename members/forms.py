'''
Created on Sep 25, 2013

@author: siddhardha
'''
##################################################################################################################
from django import forms
from members.models import Member, Grievance, Griscat, Category, Solution,\
    Author
from django.forms.extras.widgets import SelectDateWidget
import datetime
from django.contrib.auth.models import User

##################################################################################################################
class MemberLoginForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = User
        fields = ('username', 'password')
        widgets = {
           'password': forms.PasswordInput(),
        }
        
    def clean(self):
        cleaned_data = super(MemberLoginForm, self).clean()
        
        username = cleaned_data.get("username", None)
        password = cleaned_data.get("password", None)
        
        if not username:
            self._errors["username"] = self.error_class(["Please enter your username"])
            
        if not password:
            self._errors["password"] = self.error_class(["Please enter your password"])
            
        return cleaned_data

##################################################################################################################        
class MemberSignupForm1(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={'cols': 32, 'rows': 5}))
    designation = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = Member
        exclude = ('user','status','expertises')
        thisyear = datetime.datetime.now().year 
        widgets = {
            'dob': SelectDateWidget(years=range(thisyear-10, thisyear-60, -1)),
        }
    
    def clean(self):
        cleaned_data = super(MemberSignupForm1, self).clean()
        
        address = cleaned_data.get("address")
        dob = cleaned_data.get("dob")
                
        if not address:
            self._errors["address"] = self.error_class(["Please enter your address"])
        
        if not dob:
            self._errors["dob"] = self.error_class(["Please enter your birth date"])
            
        return cleaned_data
        
##################################################################################################################        
class MemberSignupForm2(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput(), required=True)
    repassword = forms.CharField(max_length=30, widget=forms.PasswordInput(), required=True)
    email = forms.EmailField(max_length=75)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')
        widgets = {
            'password': forms.PasswordInput(),
        }
        
    def clean(self):
        cleaned_data = super(MemberSignupForm2, self).clean()
        
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        repassword = cleaned_data.get("repassword")
        first_name = cleaned_data.get("first_name")
        
        if not email:
            self._errors["email"] = self.error_class(["Please enter your email address for communication. It will never be shared/published"])
            
        if not username:
            self._errors["username"] = self.error_class(["Please enter your username"])
            
        if not password:
            self._errors["password"] = self.error_class(["Please enter your password"])
        
        if not repassword:
            self._errors["repassword"] = self.error_class(["Please enter the same password again"])
        
        
        if not password == repassword:
            self._errors["repassword"] = self.error_class(["Entered passwords do not match"])
            
        if not first_name:
            self._errors["first_name"] = self.error_class(["Please enter your first name for external communication. It will never be shared/published"])
            
        return cleaned_data

##################################################################################################################    
# ModelMultipleChoiceField
class PostNewGrievanceForm1(forms.ModelForm): 
    statement = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 10, 'overflow': 'auto'}))
#     CHOICES = (('1', 'Private',), ('2', 'Public',))
#     visibility = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES)
    
    class Meta:
        model = Grievance
        fields = ('title', 'statement', 'status')
        CHOICES = (('1', 'Private',), ('2', 'Public',))
        widgets = {
            'status': forms.RadioSelect(choices=CHOICES)
        }
        
    def clean(self):
        cleaned_data = super(PostNewGrievanceForm1, self).clean()
        
        title = cleaned_data.get("title")
        statement = cleaned_data.get("statement")
        status = cleaned_data.get("status")
        
        if not title:
            self._errors["title"] = self.error_class(["Please enter the title of your grievance"])
        
        if not statement:
            self._errors["statement"] = self.error_class(["Please describe your grievance"])
            
        if not status:
            self._errors["status"] = self.error_class(["Please enter a visibility scope for your grievance"])
            
        return cleaned_data

##################################################################################################################    
# class TagChoices(ModelSelect2MultipleField):
#     queryset = Category.objects
#     search_fields = ['name__icontains']
# 
#     def get_model_field_values(self, value):
#         return {'name': value }

##################################################################################################################
class PostNewGrievanceForm2(forms.Form):
#     category = forms.ModelMultipleChoiceField(queryset=Category.objects.all())
    category = forms.CharField(max_length=100, required=False)
    CHOICES = (('1', 'Very Low',), ('2', 'Low',), ('3', 'Moderate',), ('4', 'High',), ('5', 'Very High',))
    understanding = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES, required=False)
#     category = TagChoices(required=False)
    
    class Meta:
        model = Category
        exclude = ('id','prnt_cat','level')
        
    def clean(self):
        cleaned_data = super(PostNewGrievanceForm2, self).clean()
        
        category = cleaned_data.get("category")
        
        if not category:
            self._errors["category"] = self.error_class(["Please enter at least 1 (maximum 5) suitable/applicable category"])
            
        return cleaned_data
#         CHOICES = (('1', 'Very Low',), ('2', 'Low',), ('3', 'Moderate',), ('4', 'High',), ('5', 'Very High',))
#         widgets = {
#             'status': forms.RadioSelect(choices=CHOICES)
#         }

##################################################################################################################
class PostInterimGrievanceForm(forms.Form): 
    statement = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 10, 'overflow': 'auto'}))
    
    class Meta:
        model = Grievance
        fields = ('statement')
        
    def clean(self):
        cleaned_data = super(PostInterimGrievanceForm, self).clean()
        
        statement = cleaned_data.get("statement")
        
        if not statement:
            self._errors["statement"] = self.error_class(["Please describe your grievance"])
            
        return cleaned_data

##################################################################################################################
class SolutionForm(forms.ModelForm):
    statement = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 10}))
    expected_outcome = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 5}), required=False)
    
    class Meta:
        model = Solution
        fields = ('statement', 'expected_outcome')
        
    def clean(self):
        cleaned_data = super(SolutionForm, self).clean()
        
        statement = cleaned_data.get("statement")
        
        if not statement:
            self._errors["statement"] = self.error_class(["Please describe your solution"])
            
        return cleaned_data

##################################################################################################################        
class SolutionFeedbackForm(forms.ModelForm):
    actual_outcome = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 5}), required=False)
    
    class Meta:
        model = Solution
        fields = ('actual_outcome', 'status')
        CHOICES = (('1', 'Barely satisfied',), ('2', 'Slightly Satisfied',), ('3', 'Quite Satisfied',), ('4', 'Satisfied',), ('5', 'Fully Satisfied',))
        widgets = {
            'status': forms.RadioSelect(choices=CHOICES)
        }
    
    def clean(self):
        cleaned_data = super(SolutionFeedbackForm, self).clean()
        
        status = cleaned_data.get("status")
        
        if not status:
            self._errors["status"] = self.error_class(["Please select the satisfaction level"])
            
        return cleaned_data
##################################################################################################################        
class VisitorForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, initial='Anonymous')
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.CharField(max_length=75, required=False)
    phone_no = forms.CharField(max_length=13, required=False)
    
    class Meta:
        model = Author
#         fields = ('first_name', 'last_name', 'email', 'phone_no')
        
#     def clean(self):
#         cleaned_data = super(VisitorForm, self).clean()
#         
#         first_name = cleaned_data.get("first_name")
#         last_name = cleaned_data.get("last_name")
#         email = cleaned_data.get("email")
#         phone_no = cleaned_data.get("phone_no")
#         
#         if not first_name:
#             cleaned_data.set("first_name", "Anonymous")
#             
#         if not last_name:
#             cleaned_data.set("last_name", "")
#             
#         if not email:
#             cleaned_data.set("email", "")
#             
#         if not phone_no:
#             cleaned_data.set("phone_no", "")
#             
#         return cleaned_data

##################################################################################################################        
class SearchForm(forms.Form):
    srchStr = forms.CharField(max_length=100, required=False)
#     category = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), required=False)
    category = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = Category
        exclude = ('id','prnt_cat','level')
##################################################################################################################