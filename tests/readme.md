# test for chattool

## Urls

Referenced from https://gitee.com/lzhpo/chatgpt-spring-boot-starter.

```bash
openai:
  urls:
    moderations: "https://api.openai.com/v1/moderations"
    completions: "https://api.openai.com/v1/completions"
    edits: "https://api.openai.com/v1/edits"
    chat-completions: "https://api.openai.com/v1/chat/completions"
    list-models: "https://api.openai.com/v1/models"
    retrieve-model: "https://api.openai.com/v1/models/{model}"
    embeddings: "https://api.openai.com/v1/embeddings"
    list-files: "https://api.openai.com/v1/files"
    upload-file: "https://api.openai.com/v1/files"
    delete-file: "https://api.openai.com/v1/files/{file_id}"
    retrieve-file: "https://api.openai.com/v1/files/{file_id}"
    retrieve-file-content: "https://api.openai.com/v1/files/{file_id}/content"
    create_fine_tune: "https://api.openai.com/v1/fine-tunes"
    list_fine_tune: "https://api.openai.com/v1/fine-tunes"
    retrieve_fine_tune: "https://api.openai.com/v1/fine-tunes/{fine_tune_id}"
    cancel_fine_tune: "https://api.openai.com/v1/fine-tunes/{fine_tune_id}/cancel"
    list_fine_tune_events: "https://api.openai.com/v1/fine-tunes/{fine_tune_id}/events"
    delete_fine_tune_events: "https://api.openai.com/v1/models/{model}"
    create-transcription: "https://api.openai.com/v1/audio/transcriptions"
    create-translation: "https://api.openai.com/v1/audio/translations"
    create_image: "https://api.openai.com/v1/images/generations"
    create_image_edit: "https://api.openai.com/v1/images/edits"
    create_image_variation: "https://api.openai.com/v1/images/variations"
    billing-credit-grants: "https://api.openai.com/dashboard/billing/credit_grants"
    users: "https://api.openai.com/v1/organizations/{organizationId}/users"
    billing-subscription: "https://api.openai.com/v1/dashboard/billing/subscription"
    billing-usage: "https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
```