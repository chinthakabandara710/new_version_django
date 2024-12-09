from django.urls import path
from . import views

urlpatterns = [
    path("firebase-data/", views.display_firebase_data, name="firebase_data"),
    path('', views.index_template,name='index'),
    path('register-view/', views.register_view, name='register-view'),
    path('login/', views.login, name='login'),
    path('api/login/', views.login, name='login'),
    path('api/register/', views.register, name='register'),
    path('login_view/', views.login_view, name='login_view'),
    path('api/all-users/', views.get_all_users, name='all_users'),
    path('api/user-profile/<str:uid>/', views.get_user_profile, name='get_user_profile'),
    path('api/all-assets/', views.get_all_assets, name='all_assets'),
    path('api/data/', views.index, name='index'),  
    path('api/update-status/', views.update_status, name='update_status'),  
    path('api/assets-with-assignedid/', views.get_assets_with_assigned_id, name='get_assets_with_assigned_id'),
    path('api/approve_assets/', views.approve_assets, name='approve_assets'),
    path('add-assets/', views.add_assets_page, name='add_assets_page'),
    path('api/add-assets/', views.add_assets, name='add_assets'),

    path("add-category/", views.add_category, name="add_category"),
    path("add-subcategory/", views.add_subcategory, name="add_subcategory"),
    path("categories/", views.get_categories, name="get_categories"),
    path("categories/<str:category_id>/subcategories/", views.get_subcategories, name="get_subcategories"),


]
