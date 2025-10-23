# Лабораторная работа 5 
## Django REST Framework: (микро)сервисы
### Цель работы
Улучшение (improvement) приложения для голосований  
Для улучшения функциональности приложения для создания голосований (polls) из предыдущих лабораторных работ, создайте микросервис (или несколько микросервисов), написанный с использованием Django REST Framework
(DRF), который предоставляет возможность анализа результатов голосований и предоставления статистики по голосованиям.
Этот микросервис (poll analytics) будет вторым приложением в вашем Django-проекте

### Практическая часть

#### Модели для голосований и вариантов
```python
from django.db import models

class Poll(models.Model):
    question = models.CharField(max_length=255)
    pub_date = models.DateTimeField(auto_now_add=True)

class Choice(models.Model):
    poll = models.ForeignKey(Poll, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=255)
    votes = models.IntegerField(default=0)

```

#### Сериализаторы
```python
from rest_framework import serializers
from .models import Poll, Choice

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'votes']

class PollSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = ['id', 'question', 'pub_date', 'choices']
```


#### ViewSet для статистики голосований
```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Poll
import matplotlib.pyplot as plt
import io
import base64
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class PollStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['pub_date', 'choices__votes']
    ordering = ['pub_date']

    @action(detail=True)
    def stats(self, request, pk=None):
        poll = self.get_object()
        choices = poll.choices.all()
        total_votes = sum(choice.votes for choice in choices)
        data = []

        for choice in choices:
            percent = (choice.votes / total_votes * 100) if total_votes else 0
            data.append({
                'choice_text': choice.choice_text,
                'votes': choice.votes,
                'percent': round(percent, 2)
            })

        labels = [c['choice_text'] for c in data]
        sizes = [c['percent'] for c in data]
        plt.figure(figsize=(6,4))
        plt.bar(labels, sizes, color='skyblue')
        plt.ylabel('Процент голосов')
        plt.title(f'Статистика голосования: {poll.question}')

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        return Response({'total_votes': total_votes, 'results': data, 'chart': image_base64})

```

#### Маршрутизация
```python
from rest_framework.routers import DefaultRouter
from .views import PollStatsViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'polls', PollStatsViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

```


## Реализованные возможности микросервиса

- **Агрегация статистики голосований**: общее количество голосов, количество голосов на каждый вариант, процентное соотношение.
- **Сортировка и фильтрация голосований**: по дате проведения и количеству голосов.
- **Визуализация данных**: построение столбчатой диаграммы с процентами вариантов и передача её через API.
- **Фронтенд**: динамическое отображение диаграммы и статистики голосов через JavaScript.

## Выводы

- Микросервис собирает и визуализирует статистику голосований.
- Пользователи могут сортировать, фильтровать данные и видеть результаты на диаграммах.
- Получен опыт интеграции Django REST Framework с matplotlib и передачей графиков через API.

## Структура проекта
```
Django/
├── .venv/                      # Виртуальное окружение
├── mysite/                     # Главный модуль
│   ├── __init__.py
│   ├── settings.py             # Конфигурация django-allauth, REST Framework и настройки OAuth        
│   ├── urls.py                 # Маршруты allauth и маршруты микросервисов статистики
│   ├── wsgi.py
│   └── asgi.py
│ 
├── polls/                      # Основное приложение для голосований
│   ├── migrations/
│   ├── templates/
│   │   └── polls/              # Шаблоны для страниц голосований  
│   ├── static/
│   ├── __init__.py
│   ├── adapters.py             # Кастомный адаптер OAuth для Google  
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py                 # Маршруты для API микросервиса статистики
│   ├── views.py                # Методы для отображения статистики голосований
│   └── tests.py
│ 
├── polls_analitics/           # Новое приложение для микросервиса статистики
│   ├── migrations/
│   ├── __init__.py
│   ├── serializers.py         # Сериализаторы моделей для API
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py                # Маршруты API для статистики
│   ├── views.py               # Методы агрегации и генерации графиков
│   └── tests.py
│ 
├── templates/                 # Глобальные шаблоны
│   ├── account/           
│   │   ├── login.html  
│   │   ├── logout.html    
│   │   └── signup.html
│   ├── socialaccount/         
│   │   ├── login.html
│   │   └── signup.html
│   └── base.html              
│  
├── db.sqlite3                
├── .env                       # Переменные окружения
├── manage.py
└── requirements.txt           
```

## Скриншоты проекта

### Главная страница с вкладкой "Статистика"
![Главная страница](https://github.com/user-attachments/assets/9242001f-4ec4-4bcf-ac03-77f2aaeb3455)

### Страница статистики
![Страница статистики](https://github.com/user-attachments/assets/cf044726-0e1a-4e3a-931b-4086c0b95612)

### Фильтрация по дате
![Фильтрация по дате](https://github.com/user-attachments/assets/7936acec-e45f-49fc-8eb3-b68ef2cf5d58)

### Статистика для выбранного голосования
![Статистика для выбранного голосования](https://github.com/user-attachments/assets/77d4bdce-7207-4c1c-83ee-acb9e64ecd73)


главная страница с вкладкрй статистика
<img width="1919" height="924" alt="image" src="https://github.com/user-attachments/assets/9242001f-4ec4-4bcf-ac03-77f2aaeb3455" />

страница статистики
<img width="1919" height="906" alt="image" src="https://github.com/user-attachments/assets/cf044726-0e1a-4e3a-931b-4086c0b95612" />

фильтрация по дате
<img width="708" height="663" alt="image" src="https://github.com/user-attachments/assets/7936acec-e45f-49fc-8eb3-b68ef2cf5d58" />

статистика для выбранного голосования
<img width="1919" height="924" alt="image" src="https://github.com/user-attachments/assets/77d4bdce-7207-4c1c-83ee-acb9e64ecd73" />



