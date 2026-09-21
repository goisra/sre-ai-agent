import { env } from '$env/dynamic/public';
import type { ApiError, ChatResponse } from '$lib/types/chat';

export class ChatApiError extends Error {
	code: string;

	constructor(code: string, message: string) {
		super(message);
		this.code = code;
	}
}

function apiBaseUrl(): string {
	return env.PUBLIC_API_BASE_URL || 'http://localhost:8000';
}

export async function sendChatMessage(
	message: string,
	conversationId: string | null
): Promise<ChatResponse> {
	let response: Response;

	try {
		response = await fetch(`${apiBaseUrl()}/api/v1/chat`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ message, conversation_id: conversationId })
		});
	} catch {
		throw new ChatApiError('NETWORK_ERROR', 'Could not reach the SRE agent. Is the backend running?');
	}

	const body = await response.json();

	if (!response.ok) {
		const apiError = body as ApiError;
		throw new ChatApiError(
			apiError.error?.code ?? 'UNKNOWN_ERROR',
			apiError.error?.message ?? 'Something went wrong.'
		);
	}

	return body as ChatResponse;
}
