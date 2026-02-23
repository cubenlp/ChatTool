
def mask_secret(api_key: str) -> str:
    """Mask the secret key
    
    Args:
        api_key (str): The secret key to be masked.
    
    Returns:
        str: The masked secret key.
    """
    if not api_key:
        return ""
        
    length = len(api_key)
    if length == 1 or length == 2:
        masked_key = '*' * length
    elif 3 <= length <= 6:
        masked_key = api_key[0] + '*' * (length - 2) + api_key[-1]
    elif 7 <= length <= 14:
        masked_key = api_key[:2] + '*' * (length - 4) + api_key[-2:]
    elif 15 <= length <= 30:
        masked_key = api_key[:4] + '*' * (length - 8) + api_key[-4:]
    else:
        masked_key = api_key[:8] + '*' * (length - 12) + api_key[-8:]
    return masked_key
