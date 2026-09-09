import argparse
from accuracy.llm_experiments.llm_call import LLMCall

if __name__ == "__main__":
    parser = argparse.ArgumentParser("vllm_node")
    parser.add_argument("vllm_node", help="VLLM server node.", type=str)
    args = parser.parse_args()

    llm_caller = LLMCall(vllm_server_node=args.vllm_node)

    # NOTE: first one I do it on the data, the rest I do it on the results of the first one so I can then compare the different results
    print('Running LLM with no features')
    llm_caller.get_results('data/sample_for_llm.csv', with_user_model=False, with_historic_features=False, with_change_type=False, dimension='accuracy')

    print('Running LLM with all features')
    llm_caller.get_results('results/llm_accuracy.csv', with_user_model=True, with_historic_features=True, with_change_type=True, dimension='accuracy')

    print('Running LLM only with user model features')
    llm_caller.get_results('results/llm_accuracy.csv', with_user_model=True, with_historic_features=False, with_change_type=False, dimension='accuracy')

    print('Running LLM only with historical features')
    llm_caller.get_results('results/llm_accuracy.csv', with_user_model=False, with_historic_features=True, with_change_type=False, dimension='accuracy')

    print('Running LLM only with change type features')
    llm_caller.get_results('results/llm_accuracy.csv', with_user_model=False, with_historic_features=False, with_change_type=True, dimension='accuracy')
