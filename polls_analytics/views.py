from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from polls.models import Question, Choice
from .serializers import QuestionSerializer
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta


# --- Главная страница статистики ---
def statistics_index(request):
    return render(request, 'polls/statistics.html')


# --- Список вопросов (необязательный, для API) ---
class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer

    def get_queryset(self):
        queryset = Question.objects.all().order_by('-pub_date')
        sort_by = self.request.query_params.get('sort', None)
        if sort_by == 'popularity':
            queryset = sorted(queryset, key=lambda q: q.get_total_votes(), reverse=True)
        elif sort_by == 'date':
            queryset = queryset.order_by('-pub_date')
        return queryset


# --- Фильтрация вопросов по диапазону дат ---
class QuestionFilterByDateView(APIView):
    def post(self, request):
        data = request.data.get('publication-dates', {})
        from_date = data.get('from')
        to_date = data.get('to')

        if not from_date or not to_date:
            return Response({"error": "Both 'from' and 'to' dates must be provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Парсим даты из строки
            from_naive = datetime.strptime(from_date, '%Y-%m-%d')
            to_naive = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)  # включаем весь день

            # Делаем aware datetime с текущей таймзоной
            from_aware = timezone.make_aware(from_naive, timezone.get_current_timezone())
            to_aware = timezone.make_aware(to_naive, timezone.get_current_timezone())
        except ValueError:
            return Response({"error": "Invalid date format (YYYY-MM-DD expected)."}, status=status.HTTP_400_BAD_REQUEST)

        # Фильтруем вопросы по диапазону
        questions = Question.objects.filter(pub_date__range=[from_aware, to_aware]).order_by('-pub_date')
        serializer = QuestionSerializer(questions, many=True)
        return Response({"questions": serializer.data})


# --- Статистика конкретного вопроса ---
class QuestionStatsAPIView(APIView):
    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return Response({"error": "Question not found"}, status=404)

        choices = question.choice_set.all()
        total_votes = choices.aggregate(Sum('votes'))['votes__sum'] or 0

        data = []
        most_votes = -1
        least_votes = float('inf')
        most_popular_choice = None
        least_popular_choice = None

        for choice in choices:
            percentage = (choice.votes / total_votes * 100) if total_votes > 0 else 0
            data.append({
                'choice_text': choice.choice_text,
                'votes': choice.votes,
                'percentage': round(percentage, 2)
            })

            if choice.votes > most_votes:
                most_votes = choice.votes
                most_popular_choice = choice.choice_text
            if choice.votes < least_votes:
                least_votes = choice.votes
                least_popular_choice = choice.choice_text

        # Построение графика Plotly
        labels = [c['choice_text'] for c in data]
        votes = [c['votes'] for c in data]
        fig = go.Figure(data=[go.Bar(x=labels, y=votes, text=votes, textposition='auto')])
        fig.update_layout(title=f"{question.question_text}", xaxis_title="Choice", yaxis_title="Votes")
        svg = pio.to_image(fig, format='svg')

        return Response({
            'question_text': question.question_text,
            'total_votes': total_votes,
            'choices': data,
            'most_popular_choice': most_popular_choice,
            'least_popular_choice': least_popular_choice,
            'histogram_svg': svg.decode('utf-8')
        })
