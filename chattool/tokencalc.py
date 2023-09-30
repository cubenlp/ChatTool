import tiktoken

# model cost($ per 1K tokens)
## Refernece: https://openai.com/pricing
## model | input | output
model_cost_perktoken ={
    "gpt-3.5-turbo": (0.0015, 0.002),
    "gpt-3.5-turbo-0613" : (0.0015, 0.002),
    "gpt-3.5-turbo-0301" : (0.0015, 0.002),
    "gpt-3.5-turbo-16k-0613" : (0.003, 0.004),
    "gpt-3.5-turbo-16k" : (0.003, 0.004),
    "gpt-4": (0.03, 0.06),
    "gpt-4-0613": (0.03, 0.06),
    "gpt-4-0301": (0.03, 0.06),
    "gpt-4-32k-0613": (0.06, 0.12),
    "gpt-4-32k": (0.06, 0.12),
    'ft-gpt-3.5': (0.012, 0.016)
}

def findcost(model:str, prompt_tokens:int, completion_tokens:int=0):
    """Calculate the cost of the response

    Args:
        model (str): model name
        prompt_tokens (int): number of tokens in the prompt
        completion_tokens (int): number of tokens of the response

    Returns:
        float: cost of the response
    """
    assert "gpt-" in model, "model name must contain 'gpt-'"
    if 'ft' in model: # finetuned model
        inprice, outprice = model_cost_perktoken['ft-gpt-3.5']
    elif 'gpt-3.5-turbo' in model:
        if '16k' in model:
            inprice, outprice = model_cost_perktoken['gpt-3.5-turbo-16k']
        else:
            inprice, outprice = model_cost_perktoken['gpt-3.5-turbo']
    elif 'gpt-4' in model:
        if '32k' in model:
            inprice, outprice = model_cost_perktoken['gpt-4-32k']
        else:
            inprice, outprice = model_cost_perktoken['gpt-4']
    return (inprice * prompt_tokens + outprice * completion_tokens) / 1000

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
