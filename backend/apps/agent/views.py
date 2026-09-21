from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agent.serializers import ChatRequestSerializer, ChatResponseSerializer
from apps.agent.services import ChatService


class ChatView(APIView):
    """POST /api/v1/chat"""

    def post(self, request: Request) -> Response:
        request_serializer = ChatRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        service = ChatService()
        result = service.handle_chat(
            message=data["message"],
            conversation_id=data.get("conversation_id"),
            request_id=getattr(request, "request_id", None),
        )

        response_serializer = ChatResponseSerializer(
            {
                "conversation_id": result.conversation_id,
                "message": result.message,
                "tool_calls": result.tool_calls,
            }
        )
        return Response(response_serializer.data)
