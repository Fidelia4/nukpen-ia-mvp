# import base64
# from openai import OpenAI
# from prompt import build_prompt
# import os
# from dotenv import load_dotenv

# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def analyze_outfit(image, occasion):
#     import io
#     buffered = io.BytesIO()
#     image.save(buffered, format="PNG")
#     img_base64 = base64.b64encode(buffered.getvalue()).decode()

#     response = client.chat.completions.create(
#         model="gpt-4.1-mini",
#         messages=[
#             {"role":"system","content":"Tu es un styliste professionnel."},
#             {"role":"user","content":[
#                 {"type":"text","text":build_prompt(occasion)},
#                 {"type":"image_url","image_url":{"url":f"data:image/png;base64,{img_base64}"}}
#             ]}
#         ],
#         max_tokens=800
#     )

#     return response.choices[0].message.content
import base64
from openai import OpenAI
from prompt import build_prompt
import os
from dotenv import load_dotenv
import io

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_outfit(image, occasion):

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Tu es un styliste professionnel spécialisé en mode africaine et contemporaine."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_prompt(occasion)},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=900
    )

    return response.choices[0].message.content
