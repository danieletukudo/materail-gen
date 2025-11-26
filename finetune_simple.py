"""
Simple OpenAI Fine-tuning Script - Easy to use in ChatGPT or standalone
"""

import os
import time
from openai import OpenAI

# Set your API key here or as environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'your-api-key-here'))

# Configuration
TRAINING_FILE = "training_updated.jsonl"
MODEL = "gpt-4o-mini"  # Use "gpt-4o-mini" or "gpt-3.5-turbo"

# Step 1: Upload file
print("Uploading training file...")
with open(TRAINING_FILE, 'rb') as f:
    file = client.files.create(file=f, purpose='fine-tune')
print(f"File uploaded: {file.id}")

# Step 2: Create fine-tuning job
print("Creating fine-tuning job...")
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model=MODEL
)
print(f"Job created: {job.id}")
print(f"Status: {job.status}")

# Step 3: Monitor progress
print("\nMonitoring training (press Ctrl+C to stop monitoring, job continues)...")
while True:
    job = client.fine_tuning.jobs.retrieve(job.id)
    print(f"Status: {job.status}")
    
    if job.status == "succeeded":
        print(f"\n✓ Training complete!")
        print(f"Fine-tuned model: {job.fine_tuned_model}")
        
        # Step 4: Test the model
        print("\nTesting model...")
        response = client.chat.completions.create(
            model=job.fine_tuned_model,
            messages=[{"role": "user", "content": "Lluis Companys, 23 - Punto 2 y 3"}]
        )
        print(f"Response: {response.choices[0].message.content}")
        break
    elif job.status == "failed":
        print(f"\n✗ Training failed!")
        break
    
    time.sleep(10)

