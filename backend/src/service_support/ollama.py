import requests

def generate_answer(prompt: str):

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,  # MUST be zero
                "top_p": 0.1,
                "repeat_penalty": 1.1,
                "num_predict": 150,
                "stop": ["TEXT:", "QUESTION:", "INSTRUCTION:"]
            }
        }
    )

    if response.status_code != 200:
        return f"LLM Error: {response.text}"

    return response.json()["response"].strip()