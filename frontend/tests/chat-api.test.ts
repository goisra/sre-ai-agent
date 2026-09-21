import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ChatApiError, sendChatMessage } from '../src/lib/api/chat';

describe('sendChatMessage', () => {
	beforeEach(() => {
		vi.restoreAllMocks();
	});

	it('returns the parsed response on success', async () => {
		const payload = {
			conversation_id: 'c1',
			message: 'Payments is degraded.',
			tool_calls: [{ tool: 'get_service_status', duration_ms: 12 }]
		};
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				ok: true,
				json: async () => payload
			})
		);

		const result = await sendChatMessage('Why is payments failing?', null);

		expect(result).toEqual(payload);
		expect(fetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/v1/chat'),
			expect.objectContaining({ method: 'POST' })
		);
	});

	it('throws a ChatApiError with the server error code and message', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				ok: false,
				json: async () => ({
					error: { code: 'AGENT_UNAVAILABLE', message: 'The AI agent is temporarily unavailable.' },
					request_id: 'r1'
				})
			})
		);

		await expect(sendChatMessage('hello', null)).rejects.toMatchObject({
			code: 'AGENT_UNAVAILABLE',
			message: 'The AI agent is temporarily unavailable.'
		});
	});

	it('throws a network ChatApiError when fetch itself fails', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockRejectedValue(new TypeError('fetch failed'))
		);

		const error = await sendChatMessage('hello', null).catch((e) => e);

		expect(error).toBeInstanceOf(ChatApiError);
		expect(error.code).toBe('NETWORK_ERROR');
	});
});
