from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI

from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.indices.postprocessor import SimilarityPostprocessor
from llama_index.core.response.pprint_utils import pprint_response
import openai
k = ""
openai.api_key = k

documents = SimpleDirectoryReader("/home/malineni/ROS_WS/tpycram_ws/src/pycram/src/pycram/llms/resources_pdf").load_data()

index = VectorStoreIndex.from_documents(documents, show_progress=True)



if __name__ == "__main__":
    print("Hello")

    prompt = "bring the tea mug to the table"

    # retriever = VectorIndexRetriever(index,similarity_top_k=2)

    # query_engine = RetrieverQueryEngine(retriever)

    query_engine = index.as_query_engine()

    response = query_engine.query(
        f"resolve the command {prompt} into subgoals and then each subgoal to a sequence of action designators suitable for robot to perform.")


    pprint_response(response,show_source=True)
    print("Response :", response)