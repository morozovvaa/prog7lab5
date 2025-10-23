from django.urls import path, include
from . import views

app_name = 'polls'

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.VoteView.as_view(), name="vote"),
    path("new/", views.PollNewView.as_view(), name="poll_new"),
    path('<int:pk>/edit/', views.PollEditView.as_view(), name='poll_edit'),

    # Подключаем статистику
    path("statistics/", include('polls_analytics.urls')),
]
