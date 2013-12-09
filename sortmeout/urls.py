'''
Created on Sep 25, 2013

@author: rkhapare
'''
##################################################################################################################
from django.conf.urls import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

##################################################################################################################
urlpatterns = patterns('sortmeout.views',
                        url('^signin/$', 'login_view'),
                        url('^logout/$', 'logout_view'),
                        url(r'^thankyou/$', 'thankyou', name='home'),
#                         url(r'^select2/', include('django_select2.urls')),
#                        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'C:/prjgit/sortmeoutgit/sortmeout/sortmeout/static/images/', 'show_indexes': True}),

#                        ('^hello/$', views.helloworld),
    # Examples:
    # url(r'^$', 'django_example.views.home', name='home'),
    # url(r'^django_example/', include('django_example.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
#     (r'^admin/jsi18n/', 'django.views.i18n.javascript_catalog'),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('members.views',
                        url(r'^$', 'all_grievances_view', {'scope': 'public_forum'}),
                        url('^signup/(\w+)/$', 'signup_view'),
                        url('^grievances/(\w+)/$', 'all_grievances_view'),
                        url('^grievances/grievance/(\d+)/(\d+)/$', 'grievance_view'),
                        url('^newgrievance/$', 'post_new_grievance_view'),
                        url(r'^lookup/$', 'category_lookup'),
                        url(r'^expertise/$', 'category_expertise_level'),
)
##################################################################################################################