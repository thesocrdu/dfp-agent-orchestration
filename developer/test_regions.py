from google import genai
models=['gemini-3-pro-preview', 'gemini-3-flash-preview', 'gemini-3.1-flash-lite-preview', 'gemini-3.1-flash-lite']
client = genai.Client(vertexai=True, location='us-central1', project='dpf-agent-project')
for m in models:
    try:
        response = client.models.generate_content(model=m, contents='hello')
        print(f'{m}: SUCCESS')
    except Exception as e:
        if '404' not in str(e):
            print(f'{m}: {e}')
