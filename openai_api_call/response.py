# Response class for OpenAI API call

from typing import Dict
import tiktoken

# model cost($ per 1K tokens)\
## https://openai.com/pricing
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
}

class Resp():
    
    def __init__(self, response:Dict) -> None:
        self.response = response
    
    def is_valid(self):
        """Check if the response is an error"""
        return 'error' not in self.response
    
    def cost(self):
        """Calculate the cost of the response"""
        return response_cost(self.model, self.prompt_tokens, self.completion_tokens)
    
    def __repr__(self) -> str:
        return f"`Resp`: {self.content}"
    
    def __str__(self) -> str:
        return self.content

    @property
    def id(self):
        return self.response['id']
    
    @property
    def model(self):
        return self.response['model']
    
    @property
    def created(self):
        return self.response['created']
    
    @property
    def usage(self):
        """Token usage"""
        return self.response['usage']
    
    @property
    def total_tokens(self):
        """Total number of tokens"""
        return self.usage['total_tokens']
    
    @property
    def prompt_tokens(self):
        """Number of tokens in the prompt"""
        return self.usage['prompt_tokens']
    
    @property
    def completion_tokens(self):
        """Number of tokens of the response"""
        return self.usage['completion_tokens']
    
    @property
    def message(self):
        """Message"""
        return self.response['choices'][0]['message']
    
    @property
    def content(self):
        """Content of the response"""
        return self.message['content']
    
    @property
    def object(self):
        return self.response['object']
    
    @property
    def error(self):
        """Error"""
        return self.response['error']
    
    @property
    def error_message(self):
        """Error message"""
        return self.error['message']
    
    @property
    def error_type(self):
        """Error type"""
        return self.error['type']
    
    @property
    def error_param(self):
        """Error parameter"""
        return self.error['param']
    
    @property
    def error_code(self):
        """Error code"""
        return self.error['code']

    @property
    def finish_reason(self):
        """Finish reason"""
        return self.response['choices'][0]['finish_reason']

def response_cost(model:str, prompt_tokens:int, completion_tokens:int):
    """Calculate the cost of the response

    Args:
        model (str): model name
        prompt_tokens (int): number of tokens in the prompt
        completion_tokens (int): number of tokens of the response

    Returns:
        float: cost of the response
    """
    assert model in model_cost_perktoken, f"Model {model} is not known!"
    input_price, output_price = model_cost_perktoken[model]
    return (input_price * prompt_tokens + output_price * completion_tokens) / 1000

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