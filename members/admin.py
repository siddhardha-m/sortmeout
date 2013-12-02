'''
Created on Sep 25, 2013

@author: rkhapare
'''

from django.contrib import admin
from members.models import Member, Grievance, Category

admin.site.register(Member)
admin.site.register(Grievance)
admin.site.register(Category)