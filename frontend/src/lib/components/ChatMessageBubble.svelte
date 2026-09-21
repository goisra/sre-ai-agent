<script lang="ts">
	import type { ChatMessage } from '$lib/types/chat';
	import ToolBadge from '$lib/components/ToolBadge.svelte';

	let { message }: { message: ChatMessage } = $props();
</script>

<div class="row {message.role}">
	<div class="label">{message.role === 'user' ? 'You' : 'Agent'}</div>
	<div class="bubble">
		<p>{message.content}</p>
		{#if message.role === 'assistant' && message.toolCalls.length > 0}
			<div class="tools">
				<div class="tools-label">Tools used</div>
				{#each message.toolCalls as call (call.tool)}
					<ToolBadge tool={call.tool} durationMs={call.duration_ms} />
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.row {
		display: flex;
		flex-direction: column;
		margin-bottom: 1rem;
	}

	.row.user {
		align-items: flex-end;
	}

	.row.assistant {
		align-items: flex-start;
	}

	.label {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		opacity: 0.6;
		margin-bottom: 0.25rem;
	}

	.bubble {
		max-width: 32rem;
		padding: 0.75rem 1rem;
		border-radius: 0.75rem;
		background: var(--bubble-bg, #f3f4f6);
	}

	.row.user .bubble {
		background: #2455e6;
		color: white;
	}

	.bubble p {
		margin: 0;
		white-space: pre-wrap;
	}

	.tools {
		margin-top: 0.6rem;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(0, 0, 0, 0.08);
	}

	.tools-label {
		font-size: 0.75rem;
		opacity: 0.6;
		margin-bottom: 0.25rem;
	}
</style>
