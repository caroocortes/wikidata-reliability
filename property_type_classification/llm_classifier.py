import argparse
from reliability.property_type_classification.llm_call import LLMCall

if __name__ == "__main__":
    # parser = argparse.ArgumentParser("vllm_node")
    # parser.add_argument("vllm_node", help="VLLM server node.", type=str)
    # args = parser.parse_args()
    vllm_node = 'gx03'
    # llm_caller = LLMCall(vllm_server_node=args.vllm_node)
    llm_caller = LLMCall(vllm_server_node=vllm_node)
    sample_size = None
    print("Calling LLM to classify property types - SAMPLE SIZE =  - With features")
    llm_caller.get_results('data/features_property_type.csv', with_features=True, sample_size=sample_size)

    # print("Calling LLM to classify property types - SAMPLE SIZE = 30 - Without features")
    # llm_caller.get_results('data/features_property_type.csv', with_features=False, sample_size=30)