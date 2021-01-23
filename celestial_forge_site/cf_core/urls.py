from django.urls import path

from . import views

urlpatterns = [
	path('accounts/new_account/', views.new_account, name='new-account'),
	path('accounts/logout_view/', views.logout_view, name='logout-view'),
	path('', views.index, name='index'),
	path('new_perk/', views.new_perk, name='new-perk'),
	path('edit_perk/<int:perk_id>/', views.edit_perk, name='edit-perk'),
	path('run/', views.new_run, name='new_run'),
	path('run/<int:run_id>/', views.run, name='run')
]

# For handling image uploads
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL,
                              document_root=settings.MEDIA_ROOT)
# #