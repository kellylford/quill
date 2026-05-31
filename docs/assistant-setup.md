# Writing Assistant setup

Quill supports a local-first Writing Assistant workflow. By default, Quill does not send document content to the network.

## Local provider (recommended)

1. Install and start Ollama.
2. In Quill, open **Tools > Authoring and Automation > AI Connection Preferences**.
3. Set provider to **ollama** and choose a local model.
4. Leave API key blank for local-only endpoints.
5. Use **Verify Connection** to confirm local endpoint access.
6. Use **List Models** to discover available models and select one.
7. Save settings and confirm AI menu status shows **Ready**.

## Authenticated endpoint

1. Open **AI Connection Preferences**.
2. Enter host, model, and provider values supplied by your endpoint.
3. Enter API key if required.
4. Select **Verify Connection** to confirm key and endpoint.
5. Use **List Models** to fetch available models.
6. Save settings and review the AI status/detail lines for verification feedback.

## Ollama cloud key mode (no local Ollama required)

1. Open **AI Connection Preferences** from **AI > AI Connection...** or **Preferences > AI Connection**.
2. Set provider to **Ollama Cloud (API key)**.
3. Set host to `https://ollama.com` (default for this provider).
4. Enter your Ollama API key.
5. Select **Verify Connection**.
6. Select **List Models** and choose a model.

Quill stores API keys encrypted with Windows DPAPI.

After saving, Quill automatically re-checks the connection and updates:

- **AI Status** (`Ready` or `Needs attention`)
- **AI Detail** (short reason shown directly in the AI menu)

The same plain-language verification message is announced for screen-reader users.

On Windows, Quill stores the optional key in a DPAPI-protected local file so the plaintext key is not written to disk.
