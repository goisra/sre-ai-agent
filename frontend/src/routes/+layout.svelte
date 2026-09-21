<script lang="ts">
	let { children } = $props();
</script>

{@render children()}

<style>
	:global(body) {
		margin: 0;
		background: #fafafa;
		color: #101828;
	}
</style>
