// Force this route to render per-request rather than being prerendered to
// static HTML at build time. It needs to be dynamic because it reads
// $env/dynamic/public (PUBLIC_API_BASE_URL) at runtime, which only gets
// injected into the client when the page actually goes through SSR.
export const prerender = false;
