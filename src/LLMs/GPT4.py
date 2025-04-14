import os
import openai
from retry import retry

@retry(tries=5, delay=5, backoff=2, jitter=(1, 3))
def api_call(client, model, messages, temperature, top_p, stop=None, response_format="text"):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        stop=stop,
        response_format={"type": response_format}
    )

def call_gpt(messages, model="gpt-4o", temperature=0.5, top_p=0,stop=None, response_format="text"):
    client = openai.OpenAI(
        # 如果您没有配置环境变量，请在此处用您的 API Key 进行替换
        api_key="OPENAI_API_KEY", 
        
        # 填写 DashScope 服务的 base_url
        base_url="https://api.gpts.vin/v1",
    )

    try:
        completion = api_call(client, model, messages, temperature, top_p, stop,response_format)
        return completion.choices[0].message.content
    except openai.APIError as e:
        # Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
    except openai.APIConnectionError as e:
        # Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
    except openai.RateLimitError as e:
        # Handle rate limit error after retries are exhausted
        print(f"OpenAI API request exceeded rate limit after retries: {e}")
    except Exception as e:
        # Handle unexpected exceptions
        print(f"An unexpected error occurred: {e}")

    print("Exceeded max retries or encountered an unrecoverable error. Aborting.")
    return None

if __name__ == '__main__':
    prompt = """
    Your task is to break down a complex, multi-hop question into smaller, manageable sub-questions to systematically address and solve the original problem.
Keep your output in the form of json of questions. 
Here is an example: 
question: What is the capital city of the country whose most populous city is Shanghai?
output: {{"sub_questions": ["Shanghai is the most populous city of which country?", "What is the capital city of that country?"]}}
Here is the question: {question}
"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt.format(question="Who directed the 1940 film in which John Arledge appeared?")},
    ]
    response = call_gpt(messages,response_format="json_object")
    print(response) 