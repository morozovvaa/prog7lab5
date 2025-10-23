from django.urls import path
from . import views

app_name = 'polls_analytics'

urlpatterns = [
    path('', views.statistics_index, name='statistics_index'),
    path('question-filter/', views.QuestionFilterByDateView.as_view(), name='question-filter'),
    path('question-stats/<int:pk>/', views.QuestionStatsAPIView.as_view(), name='question-stats'),
]
