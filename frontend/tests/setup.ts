import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/svelte';
import { afterEach, vi } from 'vitest';

vi.mock('$env/dynamic/public', () => ({ env: {} }));

afterEach(() => {
	cleanup();
});
