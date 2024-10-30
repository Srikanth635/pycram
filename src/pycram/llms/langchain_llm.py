from langchain_openai import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

k = ""

llm = OpenAI(
    temperature=0.9,
    openai_api_key= k
)

text = '''
What is a good name for online blog which writes about DevOps best practices?
'''

chat = ChatOpenAI(
    temperature=0.0,
    model_name="gpt-3.5-turbo",
    openai_api_key=k
)

# print(chat.invoke([
#         HumanMessage(content="Please help me to translate this text from English to Japanese: I'm working as a DevOps Engineer")
#     ]))

translation_prompt = PromptTemplate.from_template('''
Translate the following text from {origin_language} to {target_language}.

Text: """
{input_text}
"""
''')

t = translation_prompt.format(
    origin_language = "english",
    target_language = "german",
    input_text = "how are you",
)

# print(llm.invoke(t))

template = """Question: {question}

Answer: Let's think step by step."""

prompt = ChatPromptTemplate.from_template(template)

model = OllamaLLM(model="llama3")

chain = prompt | model

out = chain.invoke({"question": "What is LangChain?"})

print(out)