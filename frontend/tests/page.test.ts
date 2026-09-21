import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';

vi.mock('$lib/api/chat', () => ({
	ChatApiError: class ChatApiError extends Error {
		code: string;
		constructor(code: string, message: string) {
			super(message);
			this.code = code;
		}
	},
	sendChatMessage: vi.fn()
}));

import { sendChatMessage } from '$lib/api/chat';
import Page from '../src/routes/+page.svelte';

describe('Chat page', () => {
	it('sends a message and renders the agent response with tool badges', async () => {
		vi.mocked(sendChatMessage).mockResolvedValue({
			conversation_id: 'c1',
			message: 'Payments is degraded with an 8.4% error rate.',
			tool_calls: [{ tool: 'get_service_status', duration_ms: 42 }]
		});

		render(Page);

		const input = screen.getByLabelText('Message');
		await fireEvent.input(input, { target: { value: 'Why is payments failing?' } });
		await fireEvent.click(screen.getByRole('button', { name: 'Send' }));

		expect(screen.getByText('Why is payments failing?')).toBeInTheDocument();

		await waitFor(() => {
			expect(screen.getByText('Payments is degraded with an 8.4% error rate.')).toBeInTheDocument();
		});
		expect(screen.getByText(/get_service_status/)).toBeInTheDocument();
		expect(screen.getByText(/Conversation: c1/)).toBeInTheDocument();
	});

	it('shows an error message when the API call fails', async () => {
		const { ChatApiError } = await import('$lib/api/chat');
		vi.mocked(sendChatMessage).mockRejectedValue(
			new ChatApiError('AGENT_UNAVAILABLE', 'The AI agent is temporarily unavailable.')
		);

		render(Page);

		await fireEvent.input(screen.getByLabelText('Message'), {
			target: { value: 'status of payments' }
		});
		await fireEvent.click(screen.getByRole('button', { name: 'Send' }));

		await waitFor(() => {
			expect(screen.getByRole('alert')).toHaveTextContent(
				'The AI agent is temporarily unavailable.'
			);
		});
	});
});
