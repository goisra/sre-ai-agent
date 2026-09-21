export interface ToolCall {
	tool: string;
	duration_ms: number;
}

export interface ChatResponse {
	conversation_id: string;
	message: string;
	tool_calls: ToolCall[];
}

export interface ApiError {
	error: {
		code: string;
		message: string;
	};
	request_id: string | null;
}

export type ChatMessage =
	| { role: 'user'; content: string }
	| { role: 'assistant'; content: string; toolCalls: ToolCall[] };
