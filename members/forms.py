'''
Created on Sep 25, 2013

@author: rkhapare
'''
from django import forms
from members.models import Member, Grievance, Griscat, Category, Solution,\
    Author
from django.forms.extras.widgets import SelectDateWidget
import datetime
from django.contrib.auth.models import User
# from django_select2 import ModelSelect2MultipleField

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
            self._errors["username"] = self.error_class(["Please enter your username."])
            
        if not password:
            self._errors["password"] = self.error_class(["Please enter your password."])
            
        return cleaned_data
        
class MemberSignupForm1(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={'cols': 40, 'rows': 4}))
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
        
        dob = cleaned_data.get("dob")
        
        if not dob:
            self._errors["dob"] = self.error_class(["Please enter your birth-date."])
            
        return cleaned_data
        
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
        firstname = cleaned_data.get("first_name")
        
        if not email:
            self._errors["email"] = self.error_class(["Please enter your email address for communication. It will never be shared/published."])
            
        if not username:
            self._errors["username"] = self.error_class(["Please enter your username."])
            
        if not password:
            self._errors["password"] = self.error_class(["Please enter your password."])
            
        if not password == repassword:
            self._errors["repassword"] = self.error_class(["Entered passwords do not match."])
            
        if not firstname:
            self._errors["firstname"] = self.error_class(["Please enter your first-name for external communication. It will never be shared/published."])
            
        return cleaned_data
    
# ModelMultipleChoiceField
class PostNewGrievanceForm1(forms.ModelForm): 
    statement = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 10}))
#     CHOICES = (('1', 'Private',), ('2', 'Public',))
#     visibility = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES)
    
    class Meta:
        model = Grievance
        fields = ('title', 'statement', 'status')
        CHOICES = (('1', 'Private',), ('2', 'Public',))
        widgets = {
            'status': forms.RadioSelect(choices=CHOICES)
        }
    
# class TagChoices(ModelSelect2MultipleField):
#     queryset = Category.objects
#     search_fields = ['name__icontains']
# 
#     def get_model_field_values(self, value):
#         return {'name': value }

class PostNewGrievanceForm2(forms.Form):
#     category = forms.ModelMultipleChoiceField(queryset=Category.objects.all())
    category = forms.CharField(max_length=100, required=False)
#     category = TagChoices(required=False)
    
    class Meta:
        model = Category
        exclude = ('id','prnt_cat','level')
#         widgets = {
#             'category': forms.ModelMultipleChoiceField(queryset=Category.objects.all())
#         }

class SolutionForm(forms.ModelForm):
    statement = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 10}))
    expected_outcome = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 5}), required=False)
    
    class Meta:
        model = Solution
        fields = ('statement', 'expected_outcome')
        
class SolutionFeedbackForm(forms.ModelForm):
    actual_outcome = forms.CharField(widget=forms.Textarea(attrs={'cols': 100, 'rows': 5}), required=False)
    
    class Meta:
        model = Solution
        fields = ('actual_outcome', 'status')
        CHOICES = (('1', 'Barely satisfied',), ('2', 'Slightly Satisfied',), ('3', 'Quite Satisfied',), ('4', 'Satisfied',), ('5', 'Fully Satisfied',))
        widgets = {
            'status': forms.RadioSelect(choices=CHOICES)
        }
    
        
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
        
class SearchForm(forms.Form):
    srchStr = forms.CharField(max_length=100, required=False)
#     category = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), required=False)
    category = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = Category
        exclude = ('id','prnt_cat','level')