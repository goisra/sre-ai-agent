<script lang="ts">
	import { ChatApiError, sendChatMessage } from '$lib/api/chat';
	import ChatMessageBubble from '$lib/components/ChatMessageBubble.svelte';
	import type { ChatMessage } from '$lib/types/chat';

	let messages = $state<ChatMessage[]>([]);
	let draft = $state('');
	let conversationId = $state<string | null>(null);
	let isLoading = $state(false);
	let errorMessage = $state<string | null>(null);

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		const text = draft.trim();
		if (!text || isLoading) return;

		messages = [...messages, { role: 'user', content: text }];
		draft = '';
		isLoading = true;
		errorMessage = null;

		try {
			const response = await sendChatMessage(text, conversationId);
			conversationId = response.conversation_id;
			messages = [
				...messages,
				{ role: 'assistant', content: response.message, toolCalls: response.tool_calls }
			];
		} catch (error) {
			errorMessage =
				error instanceof ChatApiError ? error.message : 'Something went wrong. Please try again.';
		} finally {
			isLoading = false;
		}
	}
</script>

<main>
	<header>
		<h1>SRE AI Agent</h1>
		{#if conversationId}
			<span class="conversation-id">Conversation: {conversationId}</span>
		{/if}
	</header>

	<section class="messages" aria-live="polite">
		{#if messages.length === 0}
			<p class="empty">
				Ask about a service, e.g. "Why is payments failing?" or "What is the status of auth?"
			</p>
		{/if}
		{#each messages as message, index (index)}
			<ChatMessageBubble {message} />
		{/each}
		{#if isLoading}
			<p class="loading">Agent is investigating…</p>
		{/if}
		{#if errorMessage}
			<p class="error" role="alert">{errorMessage}</p>
		{/if}
	</section>

	<form onsubmit={handleSubmit}>
		<input
			type="text"
			bind:value={draft}
			placeholder="Ask something…"
			disabled={isLoading}
			aria-label="Message"
		/>
		<button type="submit" disabled={isLoading || !draft.trim()}>Send</button>
	</form>
</main>

<style>
	main {
		max-width: 40rem;
		margin: 0 auto;
		padding: 1.5rem 1rem;
		display: flex;
		flex-direction: column;
		height: 100vh;
		box-sizing: border-box;
		font-family:
			system-ui,
			-apple-system,
			sans-serif;
	}

	header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		border-bottom: 1px solid #e5e7eb;
		padding-bottom: 0.75rem;
		margin-bottom: 1rem;
	}

	h1 {
		font-size: 1.25rem;
		margin: 0;
	}

	.conversation-id {
		font-size: 0.7rem;
		opacity: 0.5;
		font-family: monospace;
	}

	.messages {
		flex: 1;
		overflow-y: auto;
		margin-bottom: 1rem;
	}

	.empty {
		opacity: 0.6;
		font-size: 0.9rem;
	}

	.loading {
		opacity: 0.6;
		font-size: 0.85rem;
		font-style: italic;
	}

	.error {
		color: #b42318;
		background: #fef3f2;
		border: 1px solid #fda29b;
		border-radius: 0.5rem;
		padding: 0.5rem 0.75rem;
		font-size: 0.85rem;
	}

	form {
		display: flex;
		gap: 0.5rem;
	}

	input {
		flex: 1;
		padding: 0.6rem 0.75rem;
		border: 1px solid #d0d5dd;
		border-radius: 0.5rem;
		font-size: 0.95rem;
	}

	button {
		padding: 0.6rem 1.2rem;
		border: none;
		border-radius: 0.5rem;
		background: #2455e6;
		color: white;
		font-weight: 600;
		cursor: pointer;
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
