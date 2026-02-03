from . import azure2openai, azure2claude, openai2claude, claude2azure

ADAPTERS = {
    "azure2openai": azure2openai.app,
    "azure2claude": azure2claude.app,
    "openai2claude": openai2claude.app,
    "claude2azure": claude2azure.app
}
