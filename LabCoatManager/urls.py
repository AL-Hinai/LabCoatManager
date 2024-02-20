from django.contrib import admin
from django.urls import path
from labcoat import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home_view'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('stock/', views.stock_view, name='stock_view'),
    path('add_stock/', views.add_stock_view, name='add_stock_view'),
    path('distribute_lab_coat/', views.distribute_lab_coat, name='distribute_lab_coat'),
    path('student_distributions/', views.student_distributions_view, name='student_distributions_view'),
    path('staff_distributions/', views.staff_distributions_view, name='staff_distributions_view'),
    path('upload_excel_distribution/', views.upload_excel_distribution, name='upload_excel_distribution'),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


