<script lang="ts">
	let { tool, durationMs }: { tool: string; durationMs: number } = $props();
</script>

<span class="badge">✓ {tool} <small>({durationMs}ms)</small></span>

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		background: #eef7ee;
		color: #1f6d33;
		border: 1px solid #cfe8cf;
		border-radius: 999px;
		padding: 0.15rem 0.65rem;
		font-size: 0.8rem;
		margin: 0.15rem 0.35rem 0.15rem 0;
	}

	small {
		opacity: 0.7;
	}
</style>
