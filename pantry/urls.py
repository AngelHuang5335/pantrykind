from django.urls import path
from pantry.views import home
urlpatterns=[path('',home.landing,name='landing')]

from django.contrib.auth import views as auth_views
from pantry.views import accounts
urlpatterns += [path('accounts/signup/',accounts.signup,name='signup'),path('accounts/login/',auth_views.LoginView.as_view(),name='login'),path('accounts/logout/',auth_views.LogoutView.as_view(),name='logout'),path('app/',home.dashboard,name='dashboard')]

from pantry.views import households

urlpatterns += [path('households/new/', households.create, name='household_create')]

from pantry.views import inventory

urlpatterns += [path('pantry/', inventory.index, name='inventory')]

urlpatterns += [path('pantry/new/', inventory.create, name='item_create')]

urlpatterns += [path('pantry/<int:pk>/edit/', inventory.edit, name='item_edit')]

urlpatterns += [path('pantry/<int:pk>/', inventory.detail, name='item_detail')]

urlpatterns += [path('pantry/<int:pk>/action/<str:kind>/', inventory.stock_action, name='stock_action')]

urlpatterns += [path('pantry/<int:pk>/archive/', inventory.archive, name='item_archive')]

urlpatterns += [path('pantry/<int:pk>/duplicate/', inventory.duplicate, name='item_duplicate')]

from pantry.views import shopping

urlpatterns += [path('shopping/', shopping.index, name='shopping')]

urlpatterns += [path('shopping/<int:pk>/toggle/', shopping.toggle, name='shopping_toggle')]

urlpatterns += [path('shopping/<int:pk>/edit/', shopping.edit, name='shopping_edit')]

urlpatterns += [path('shopping/<int:pk>/delete/', shopping.delete, name='shopping_delete')]

urlpatterns += [path('shopping/clear-checked/', shopping.clear_checked, name='shopping_clear_checked')]

urlpatterns += [path('shopping/low-stock/', shopping.add_low_stock, name='shopping_low_stock')]

from pantry.views import recipes

urlpatterns += [path('recipes/', recipes.index, name='recipes')]

urlpatterns += [path('recipes/new/', recipes.edit, name='recipe_create')]

urlpatterns += [path('recipes/<int:pk>/edit/', recipes.edit, name='recipe_edit')]

urlpatterns += [path('recipes/<int:pk>/', recipes.detail, name='recipe_detail')]

urlpatterns += [path('recipes/<int:pk>/shop/', recipes.shop_missing, name='recipe_shop')]

urlpatterns += [path('recipes/<int:pk>/cook/', recipes.cook, name='recipe_cook')]

urlpatterns += [path('recipes/<int:pk>/delete/', recipes.delete, name='recipe_delete')]

urlpatterns += [path('households/settings/', households.settings, name='household_settings')]

urlpatterns += [path('households/<int:pk>/switch/', households.switch, name='household_switch')]

urlpatterns += [path('households/invite/', households.invite, name='household_invite')]

urlpatterns += [path('join/<str:token>/', households.accept, name='invitation_accept')]

urlpatterns += [path('households/invitations/<int:pk>/revoke/', households.revoke, name='invitation_revoke')]

urlpatterns += [path('households/members/<int:pk>/remove/', households.remove_member, name='member_remove')]

urlpatterns += [path('households/members/<int:pk>/transfer/', households.transfer, name='member_transfer')]

urlpatterns += [path('households/leave/', households.leave, name='household_leave')]

urlpatterns += [path('accounts/password/',auth_views.PasswordChangeView.as_view(template_name='registration/password.html',success_url='/accounts/password/done/'),name='password_change'),path('accounts/password/done/',auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_done.html'),name='password_change_done')]

from pantry.views import planner

urlpatterns += [path('plan/', planner.index, name='planner')]

urlpatterns += [path('plan/<int:pk>/edit/', planner.edit, name='plan_edit')]

urlpatterns += [path('plan/<int:pk>/delete/', planner.delete, name='plan_delete')]

urlpatterns += [path('plan/<int:pk>/cook/', planner.cook, name='plan_cook')]

urlpatterns += [path('plan/calendar.ics', planner.export_calendar, name='plan_calendar')]

from pantry.views import insights

urlpatterns += [path('insights/', insights.index, name='insights')]

urlpatterns += [path('activity/', insights.activity, name='activity')]

from pantry.views import transfers

urlpatterns += [path('data/pantry.csv', transfers.export_inventory, name='inventory_export')]

urlpatterns += [path('data/shopping.csv', transfers.export_shopping, name='shopping_export')]

urlpatterns += [path('data/import/', transfers.import_inventory, name='inventory_import')]
