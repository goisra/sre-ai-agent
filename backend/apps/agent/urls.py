from django.urls import path

from apps.agent.views import ChatView

urlpatterns = [
    path("chat", ChatView.as_view(), name="chat"),
]
