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
