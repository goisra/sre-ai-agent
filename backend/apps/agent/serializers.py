from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, trim_whitespace=True, allow_blank=False)
    conversation_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class ToolCallSerializer(serializers.Serializer):
    tool = serializers.CharField()
    duration_ms = serializers.IntegerField()


class ChatResponseSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField()
    message = serializers.CharField()
    tool_calls = ToolCallSerializer(many=True)
