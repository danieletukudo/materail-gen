# OpenAI Fine-tuning Guide

## Important Note
**GPT-5 does not exist yet.** This script uses `gpt-4o-mini` which is the latest model available for fine-tuning. You can also use `gpt-3.5-turbo`.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements_finetune.txt
```

2. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or set it directly in the script.

## Usage

### Option 1: Full-featured script (Recommended)
```bash
python finetune_gpt.py
```

This script provides:
- File upload with progress
- Job creation
- Real-time training monitoring
- Training metrics
- Model testing

### Option 2: Simple script
```bash
python finetune_simple.py
```

A minimal version that's easy to understand and modify.

## Code for ChatGPT

If you want to use this code in ChatGPT, here's a clean version you can paste:

```python
import os
import time
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'your-key-here'))

# Upload training file
with open('training_updated.jsonl', 'rb') as f:
    file = client.files.create(file=f, purpose='fine-tune')

# Create fine-tuning job
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model='gpt-4o-mini'  # or 'gpt-3.5-turbo'
)

print(f"Job ID: {job.id}")

# Monitor training
while True:
    job = client.fine_tuning.jobs.retrieve(job.id)
    print(f"Status: {job.status}")
    
    if job.status == "succeeded":
        print(f"Model: {job.fine_tuned_model}")
        break
    elif job.status == "failed":
        print("Training failed")
        break
    
    time.sleep(10)

# Test the model
response = client.chat.completions.create(
    model=job.fine_tuned_model,
    messages=[{"role": "user", "content": "Your test prompt here"}]
)
print(response.choices[0].message.content)
```

## Monitoring Training

The full script (`finetune_gpt.py`) provides real-time monitoring with:
- Current status updates
- Training events
- Token usage
- Error messages (if any)

## Testing Your Model

After training completes, you'll get a model ID like `ft:gpt-4o-mini:org-name:model-name:timestamp`

Use it like this:
```python
response = client.chat.completions.create(
    model='ft:gpt-4o-mini:org-name:model-name:timestamp',
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

## Cost Estimation

Fine-tuning costs:
- **gpt-4o-mini**: ~$3.00 per 1M training tokens
- **gpt-3.5-turbo**: ~$8.00 per 1M training tokens

Your dataset appears to be large, so costs may be significant. Check OpenAI's pricing page for current rates.

## Troubleshooting

1. **"File not found"**: Make sure `training_updated.jsonl` is in the same directory
2. **"Invalid API key"**: Verify your API key is set correctly
3. **"Training failed"**: Check the job events for error details
4. **"Model not available"**: Ensure you're using a supported model (`gpt-4o-mini` or `gpt-3.5-turbo`)

## Next Steps

After fine-tuning:
1. Save your model ID
2. Test with various prompts
3. Integrate into your application
4. Monitor usage and costs

