import matplotlib.pyplot as plt
import numpy as np
import rospy
from pycram.datastructures.world import World
from pycram.worlds.bullet_world import BulletWorld, Object
from pycram.datastructures.pose import Pose
from pycram.datastructures.enums import ObjectType, WorldMode
from rospy import sleep
from openai import OpenAI
import json

openai_api_key = ""
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_KEY = openai_api_key
client = OpenAI(api_key=OPENAI_API_KEY)

def read_context(file_path):
    with open(file_path, 'r') as file:
        context = file.read()
    return context

root_path = "/home/malineni/ROS_WS/tpycram_ws/src/pycram/src/pycram/llms"
# world_context_file = root_path + "/resources/world.txt"
# world_context = read_context(world_context_file)

# state_context_file = root_path + "/resources/world_state.txt"
# state_context = read_context(state_context_file)

obj_context_file = root_path + "/resources/llm_object_designators.txt"
obj_context = read_context(obj_context_file)

act_context_file = root_path + "/resources/llm_action_designators.txt"
act_context = read_context(act_context_file)

loc_context_file = root_path + "/resources/llm_location_designators.txt"
loc_context = read_context(loc_context_file)


def explore_simulation_environment(world: World, prompt : str ):
        context = world.objects
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are an assistant that analyses the context given and "
                            "responds to user prompts accordingly in json, no additional text needed"},
                {"role": "assistant", "content": str(context)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0,
        )
        # dict_response = response.choices[0].message.content
        # print(response.choices[0].message.content)
        return response.choices[0].message.content

def task_strategy_planner(world: World, prompt: str):
    print()
    # Task Disambiguation and Segmentation
    context = world.objects

    tools = [
        {
            "type": "function",
            "function": {
                "name": "explore_designators",
                "description": "explore all the available designators",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "queries prompt"
                        }
                    },
                    "required": ["prompt"],
                    "additionalProperties": False
                }
            }
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are an assistant that explores the world and segments the prompt into tasks for the robot and "
                        "ask queries which are needed to finish the task, no additional text needed"},
            {"role": "assistant", "content": str(context)},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
        temperature=0,
        tools= tools
    )
    return response.choices[0].message.content

def explore_designators(world: World, prompt: str):
    print()
    context = f"World Information is given by \n\n {str(world.objects)} \n\n"
    context = context + (f"Available Location Designators to calculate the locations for the robot to reach or see a target objects are: \n\n {loc_context}"
               f"Available Object Designators to get reference to the object in the world are: \n\n {obj_context}"
               f"Available Action Designators to perform an action are: \n\n {act_context}")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are an assistant that analyses the context given and "
                        "responds to user prompts accordingly as python code, no additional text needed"},
            {"role": "assistant", "content": str(context)},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
        temperature=0,
    )
    return response.choices[0].message.content



if __name__ == '__main__':
    print("++++++++++++++")