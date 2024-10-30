import json

from dns.message import make_response
from flask import Flask, render_template, request
import os
from openai import OpenAI
from dotenv import load_dotenv
# from output_models.obj_design_structre import *

load_dotenv()  # Load environment variables from .env

openai_api_key = ""
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_KEY = openai_api_key
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)


def read_context(file_path):
    with open(file_path, 'r') as file:
        context = file.read()
    return context


root_path = "/home/malineni/ROS_WS/tpycram_ws/src/pycram/src/pycram/llms"
context_file = root_path + "/resources/llm_action_designators.txt"
context = read_context(context_file)


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/plan', methods=['GET', 'POST'])
def planner():
    if request.method == 'POST':
        prompt = request.form['prompt']

        context_file = root_path + "/resources/llm_contexts/llm_action_designators.txt"
        context = read_context(context_file)

        context = context + "\n\n" + read_context(root_path + "/resources/llm_contexts/sample.txt")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a python code generator for robotic actions using the functions from the context."},
                {"role": "assistant", "content": context},
                {"role": "user",
                 "content": f"resolve the natural language instruction {prompt} into a python code of action designators from the context"},
                {"role": "user",
                 "content": "also plan navigation for robot if necessary assuming it was somewhere in the environment"},
                {"role": "user",
                 "content": "output python code of robot plan to perform, take the sample plan in the context for reference."
                            " no any other explanation is needed"}
            ],
            max_tokens=1000,
            temperature=0
            # messages=[
            #     {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            #     {"role": "user", "content": prompt}
            # ]
        )

        code = response.choices[0].message.content.strip()

        with open(root_path + "/outputs/gen_code.py", "w") as file:
            file.write(code)

        return render_template('home.html', prompt=prompt, response=response.choices[0].message.content)
    else:
        return render_template('home.html')


@app.route('/segment', methods=['GET', 'POST'])
def resolve_objects():
    if request.method == 'POST':
        prompt = request.form['prompt']

        env = ("{'floor': {'name': 'floor', 'obj_type': <ObjectType.ENVIRONMENT: 9>}, "
               "'kitchen': {'name': 'kitchen', 'obj_type': <ObjectType.ENVIRONMENT: 9>}, "
               "'milk': {'name': 'milk', 'obj_type': <ObjectType.MILK: 3>}, "
               "'froot_loops': {'name': 'froot_loops', 'obj_type': <ObjectType.BREAKFAST_CEREAL: 6>}, "
               "'spoon': {'name': 'spoon', 'obj_type': <ObjectType.SPOON: 4>}}")

        env_context = (f"Objects in the environment and their names, types are as follows "
                       f"{env}")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that can detect objects in prompt and "
                            "match semantically to objects in environment context"},
                {"role": "assistant", "content": env_context},
                {"role": "user", "content": f"find all the objects in the prompt {prompt} that exactly matches"
                                            f"with the objects in environment context and "
                                            f"print their names only no explanation needed"},
                {"role": "user", "content": "mention 'No Such Object in the Environment' if nothing matches"}
            ],
            max_tokens=1000,
            temperature=0
        )

        # code = response.choices[0].message.content.strip()

        # with open("/home/malineni/ROS_WS/tpycram_ws/src/pycram/src/pycram/llms/outputs/gen_code.py", "w") as file:
        #     file.write(code)

        return render_template('segment_home.html', prompt=prompt, response=response.choices[0].message.content)
    else:

        return render_template('segment_home.html')


# @app.route('/segment', methods=['GET', 'POST'])
# def decompose_disambiguate():
#     if request.method == 'POST':
#         prompt = request.form['prompt']
#
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system",
#                  "content": "You are a helpful assistant that separate high level natural language instructions into simpler instructions suitable for robots"},
#                 # {"role": "assistant", "content": context},
#                 {"role": "user", "content": f"resolve the natural language instruction {prompt} into separate meaningful sentences"},
#                 # {"role": "user", "content": "plan navigation for robot if needed and Output only python code"}
#             ],
#             max_tokens=1000,
#             temperature=0
#             # messages=[
#             #     {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
#             #     {"role": "user", "content": prompt}
#             # ]
#         )
#
#         # code = response.choices[0].message.content.strip()
#
#         # with open("/home/malineni/ROS_WS/tpycram_ws/src/pycram/src/pycram/llms/outputs/gen_code.py", "w") as file:
#         #     file.write(code)
#
#         return render_template('segment_home.html', prompt=prompt, response=response.choices[0].message.content)
#     else:
#         return render_template('segment_home.html')

@app.route('/classifier', methods=['GET', 'POST'])
def classifier():
    if request.method == 'POST':
        prompt = request.form['prompt']

        world_context_file = root_path + "/resources/world.txt"
        world_context = read_context(world_context_file)

        state_context_file = root_path + "/resources/world_state.txt"
        state_context = read_context(state_context_file)

        obj_context_file = root_path + "/resources/llm_object_designators.txt"
        obj_context = read_context(obj_context_file)

        act_context_file = root_path + "/resources/llm_action_designators.txt"
        act_context = read_context(act_context_file)

        cons = f"""
                Functions to enquire about the world and object are: \n\n {world_context} \n\n
                Objects State Information in the world : \n\n {state_context} \n\n
                Object Designators for the Objects in the world : \n\n {obj_context} \n\n
                Action Designators for the different actions : \n\n {act_context} \n\n
                """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are an intelligent robot agent that can plan navigation and manipulation strategies to"
                            "complete the queried task"},
                {"role": "assistant", "content": cons},
                {"role": "user",
                 "content": f"resolve {prompt} into subtasks if needed and match best suited action designator for each"},
                {"role": "user",
                 "content": "Only output python code needed to execute, no explanation needed"}
            ],
            max_tokens=3000,
            temperature=0,
            # response_format =
        )

        # res = response.choices[0].message.content
        # json_res = json.loads(res)
        # print("MODEL RESPONSE : ", res, type(res), type(json_res))
        # print(f"ObjectDesignatorDescription(names={json_res['names']}, types={json_res['types']})")
        # print(f"ObjectDesignatorDescription(names={response.choices[0].message.content["names"]})")
        print(type(response.choices[0].message.content.split('\n')))
        queried_obj_designators = response.choices[0].message.content.split('\n')
        print("queried_obj_designators : ", queried_obj_designators)

        # obj_context = f"Object designators of queried objects are \n\n {queried_obj_designators}"
        # act_context_file = root_path + "/resources/llm_contexts/llm_action_designators.txt"
        # act_context = read_context(act_context_file)
        # act_context = act_context + "\n\n" + obj_context + "\n\n" + f"PROMPT = {prompt}"
        #
        # response = client.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system",
        #          "content": "You are a helpful assistant that can map the prompt and object designators "
        #                     "from the context into best suited action designators from the context"},
        #         {"role": "assistant", "content": act_context},
        #         {"role": "user", "content": f"resolve the prompt {prompt} into best "
        #                                     f"suited action designators, not action performables, from the context"},
        #         {"role": "user", "content": "Only output action designators with resolved parameters, no explanation needed"}
        #     ],
        #     max_tokens=1000,
        #     temperature=0
        # )

        return render_template('classifier_home.html', prompt=prompt, response=response.choices[0].message.content)

    else:
        return render_template('classifier_home.html')


@app.route('/chatGPT', methods=['GET', 'POST'])
def chatGPT():
    if request.method == 'POST':
        # prompt = request.form['prompt']
        data = request.get_json()
        prompt = data['prompt']
        contexts = read_context(root_path + "/resources/world.txt")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are an assistant that responds with a python code to user prompts accordingly, no additional text needed"},
                {"role" : "assistant", "content": contexts},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0,
            # response_format =
        )

        # with open(root_path + "/outputs/gpt_responses.txt", "w") as file:
        #     file.write(str(response))
        return response.choices[0].message.content
        # return render_template('chatGPT.html', prompt=prompt, response=response.choices[0].message.content)

    # else:
    #     return render_template('chatGPT.html')

@app.route('/chatGPTFunctionCalling', methods=['GET', 'POST'])
def chatGPTFunctionCalling():
    if request.method == 'POST':
        prompt = request.form['prompt']

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_object_by_name",
                    "description": "Get the objects in the simulation world by name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "object name"
                            }
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_object_by_id",
                    "description": "Get the objects in the simulation world by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "obj_id": {
                                "type": "string",
                                "description": "object ID"
                            }
                        },
                        "required": ["obj_id"],
                        "additionalProperties": False
                    }
                }
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that responds to user prompts accordingly"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0,
            tools=tools,
            tool_choice= "auto",
            # response_format =
        )

        with open(root_path + "/outputs/gpt_responses.txt", "w") as file:
            file.write(str(response))

        if response.choices[0].message.tool_calls:

            print("TOOL CALLS PRESENT")

            tool_call = response.choices[0].message.tool_calls[0]

            print(tool_call)

            arguments = json.loads(tool_call.function.arguments)
            if arguments:
                output = eval(f"{tool_call.function.name}(**{arguments})")
                print("OUTPUT ", output)

            return render_template('chatGPTFunctionCalling.html', prompt=prompt,
                                   response=tool_call)
        else:
            return render_template('chatGPTFunctionCalling.html', prompt=prompt,
                                   response=response.choices[0].message.content)

    else:
        return render_template('chatGPTFunctionCalling.html')


@app.route('/textapi', methods=['GET', 'POST'])
def textapi():
    if request.method == 'POST':
        data = request.get_json()
        prompt = data['prompt']
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_object_by_name",
                    "description": "Get the objects in world by name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "object name"
                            }
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_object_by_id",
                    "description": "Get the objects in world by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "obj_id": {
                                "type": "string",
                                "description": "object ID"
                            }
                        },
                        "required": ["obj_id"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "objects",
                    "description": "Get or find all objects in world"
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_position",
                    "description": "Get the position or location of the object in world",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name" : {
                                "type": "string",
                                "description": "object name"
                            }
                        }
                    }
                }
            },
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that responds to user prompts accordingly"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0,
            tools=tools,
            tool_choice="auto"
        )

        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            if arguments:
                output = f"{tool_call.function.name}(**{arguments})"
                return output
            else:
                output = f"{tool_call.function.name}"
                return output
        else:
            return response.choices[0].message.content

@app.route('/analyze_environment', methods=['GET', 'POST'])
def analyze_environment():
    if request.method == 'POST':
        data = request.get_json()
        prompt = data['prompt']
        context = data['context']

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that anaylses the context given and "
                            "responds to user prompts accordingly"},
                {"role": "assistant", "content": context},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0,
        )

        return response.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True)