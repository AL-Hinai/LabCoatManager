from django.contrib import admin
from django.urls import path
from labcoat import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home_view'),
    path('stock/', views.stock_view, name='stock_view'),
    path('add_stock/', views.add_stock_view, name='add_stock_view'),
    path('distribute_lab_coat/', views.distribute_lab_coat, name='distribute_lab_coat'),
    path('student_distributions/', views.student_distributions_view, name='student_distributions_view'),
    path('staff_distributions/', views.staff_distributions_view, name='staff_distributions_view'),
    path('ocr_process/', views.ocr_process_view, name='ocr_process_view'),
    ]


