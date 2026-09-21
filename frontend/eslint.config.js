import js from '@eslint/js';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';

export default [
	js.configs.recommended,
	...svelte.configs['flat/recommended'],
	{
		languageOptions: {
			globals: { ...globals.browser }
		}
	},
	{
		files: ['**/*.ts'],
		languageOptions: {
			parser: tsParser
		},
		plugins: { '@typescript-eslint': tseslint },
		rules: {
			...tseslint.configs.recommended.rules
		}
	},
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parserOptions: { parser: tsParser }
		}
	},
	{
		files: ['svelte.config.js', 'vite.config.ts', 'eslint.config.js'],
		languageOptions: {
			globals: { ...globals.node }
		}
	},
	{
		files: ['tests/**/*.ts'],
		languageOptions: {
			globals: { ...globals.node }
		}
	},
	{
		ignores: ['build/', '.svelte-kit/', 'dist/', 'node_modules/']
	}
];
