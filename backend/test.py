from openai import OpenAI
from dotenv import load_dotenv
import os
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType

load_dotenv()

# client = OpenAI(
#   base_url = "https://integrate.api.nvidia.com/v1",
#   api_key = os.getenv("NVIDIA_API_KEY")
# )

# input = input("Enter your prompt: ")

# completion = client.chat.completions.create(
#   model="nvidia/llama-3.1-nemotron-ultra-253b-v1",
#   messages=[{"role":"user","content":input}],
#   temperature=0.2,
#   top_p=0.7,
#   max_tokens=1024,
#   stream=True
# )

# for chunk in completion:
#   if chunk.choices[0].delta.content is not None:
#     print(chunk.choices[0].delta.content, end="")

    # Create an API context for production
api_context = ApiContext.create(
    # ApiEnvironmentType.PRODUCTION, # SANDBOX for testing
    ApiEnvironmentType.SANDBOX,
    os.getenv("BUNQ_PRODUCTION_API_KEY"),
    "My Device Description"
)

# Save the API context to a file for future use
api_context.save("bunq_api_context.conf")

# Load the API context into the SDK
BunqContext.load_api_context(api_context)