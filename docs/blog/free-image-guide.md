# AI 生图白嫖指南

AI image provider tools have moved from ChatTool to the standalone `ChatImg` package.

## Current Entry Point

Install through the ChatTool aggregate dependency when you want ChatArch packages together:

```bash
pip install "chattool[images]"
```

Then use the first-class CLI:

```bash
chatimg pollinations generate "a cat in space" -o cat.png
chatimg siliconflow generate "a cyberpunk city at night" -o city.png
chatimg tongyi generate "一只在屋顶晒太阳的赛博朋克猫" --style "<auto>" --size "1024*1024" -o tongyi.png
chatimg huggingface generate "A futuristic city at night, neon lights" -o hf.png
chatimg liblib generate "A cute dog" --model-id liblib-sdxl-model -o liblib.png
chatimg codex generate "a watercolor fox"
chatimg openai generate "a clean app icon"
```

`chattool image` has been removed so ChatTool no longer carries duplicate image provider business logic.

## Provider Notes

- Pollinations.ai (`pollinations`): lightweight image endpoint, account/API-key policy depends on Pollinations.
- SiliconFlow (`siliconflow`): free and paid text-to-image model choices depend on account limits.
- Tongyi (`tongyi`): Aliyun DashScope ecosystem.
- Hugging Face (`huggingface`): open model ecosystem.
- LiblibAI (`liblib`): Liblib model/workflow ecosystem.
- Codex/OpenAI OAuth (`codex`): ChatGPT/Codex OAuth image bridge.
- OpenAI-compatible (`openai`): OpenAI Images API compatible endpoint, including CRS proxy use cases.

Provider credentials and defaults now belong to `chatimg.config.ChatImgConfig` / `chatenv -t chatimg`, not `chattool.config`.
