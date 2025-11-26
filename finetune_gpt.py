"""
OpenAI Fine-tuning Script
This script handles:
1. Uploading the training dataset
2. Creating a fine-tuning job
3. Monitoring training progress
4. Testing the fine-tuned model
"""

import os
import time
import json
from openai import OpenAI
from datetime import datetime
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Install with: pip install tiktoken")

# Initialize OpenAI client
# Make sure to set your OpenAI API key as an environment variable:
# export OPENAI_API_KEY='your-api-key-here'
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
TRAINING_FILE = "training_no_submaterials.jsonl"
# For Supervised Fine-tuning (SFT), use one of these models:
# - gpt-4.1-2025-04-14 (full model)
# - gpt-4.1-mini-2025-04-14 (recommended - smaller, faster, cheaper)
# - gpt-4.1-nano-2025-04-14 (smallest)
MODEL_NAME = "gpt-4.1-mini-2025-04-14"  # Recommended for supervised fine-tuning

# Context size limits (in tokens) for each model
MODEL_CONTEXT_LIMITS = {
    "gpt-4.1-2025-04-14": 128000,
    "gpt-4.1-mini-2025-04-14": 65536,
    "gpt-4.1-nano-2025-04-14": 32768,
}

def list_available_models():
    """List available models for fine-tuning"""
    print(f"\n{'='*60}")
    print("Checking Available Fine-tuning Models")
    print(f"{'='*60}")
    
    try:
        # Try to get models list (this may vary by API version)
        models = client.models.list()
        print("Available models:")
        for model in models.data:
            if 'fine-tune' in model.id.lower() or 'gpt' in model.id.lower():
                print(f"  - {model.id}")
        
        # Supported supervised fine-tuning models
        sft_models = ["gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14"]
        print(f"\nSupported supervised fine-tuning models:")
        for model in sft_models:
            print(f"  - {model}")
        
        return sft_models
    except Exception as e:
        print(f"Note: Could not list models: {e}")
        # Return supported models as fallback
        return ["gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14"]

def count_tokens(text, model_name="gpt-4.1-mini-2025-04-14"):
    """Count tokens in text using tiktoken"""
    if not TIKTOKEN_AVAILABLE:
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    try:
        # Use cl100k_base encoding for GPT-4 models
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Warning: Could not count tokens accurately: {e}")
        # Fallback estimate
        return len(text) // 4

def validate_and_fix_training_file(file_path, model_name, max_context_tokens=None):
    """Validate training file and fix examples that exceed context limit"""
    if max_context_tokens is None:
        max_context_tokens = MODEL_CONTEXT_LIMITS.get(model_name, 65536)
    
    print(f"\n{'='*60}")
    print("Validating Training File")
    print(f"{'='*60}")
    print(f"Model: {model_name}")
    print(f"Context limit: {max_context_tokens:,} tokens")
    
    examples = []
    long_examples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    example = json.loads(line)
                    # Convert to string to count tokens
                    example_str = json.dumps(example, ensure_ascii=False)
                    token_count = count_tokens(example_str, model_name)
                    
                    if token_count > max_context_tokens:
                        long_examples.append({
                            'line': line_num,
                            'tokens': token_count,
                            'example': example
                        })
                        print(f"⚠ Example {line_num}: {token_count:,} tokens (exceeds limit by {token_count - max_context_tokens:,})")
                    else:
                        examples.append(example)
                        print(f"✓ Example {line_num}: {token_count:,} tokens")
                        
                except json.JSONDecodeError as e:
                    print(f"✗ Error parsing line {line_num}: {e}")
                    return None, None
        
        choice = None
        if long_examples:
            print(f"\n⚠ Found {len(long_examples)} example(s) that exceed the context limit.")
            print("Options:")
            print("  1. Truncate long examples (may lose data)")
            print("  2. Skip long examples")
            print("  3. Exit and fix manually")
            
            choice = input("\nEnter choice (1/2/3) [default: 2]: ").strip() or "2"
            
            if choice == "1":
                # Truncate long examples
                print("\nTruncating long examples...")
                for long_ex in long_examples:
                    # Truncate the assistant content (usually the longest part)
                    example = long_ex['example']
                    if 'messages' in example:
                        for msg in example['messages']:
                            if msg.get('role') == 'assistant' and 'content' in msg:
                                content = msg['content']
                                # Estimate how much to keep (leave some buffer)
                                target_tokens = max_context_tokens - 1000  # Buffer
                                # Rough truncation - keep first part
                                # Better approach: truncate from end or intelligently
                                if count_tokens(content, model_name) > target_tokens:
                                    # Simple truncation: keep first 80% of characters
                                    # This is approximate - for better results, use proper token truncation
                                    truncated_len = int(len(content) * 0.8)
                                    msg['content'] = content[:truncated_len] + "\n[...truncated...]"
                                    print(f"  Truncated example {long_ex['line']}")
                    examples.append(example)
                print("✓ Truncation complete")
            elif choice == "2":
                # Skip long examples
                print(f"\n⚠ Skipping {len(long_examples)} long example(s)")
                for long_ex in long_examples:
                    print(f"  Skipped example {long_ex['line']} ({long_ex['tokens']:,} tokens)")
            else:
                print("\nExiting. Please fix the training file manually.")
                return None, None
        
        if not examples:
            print("\n✗ No valid examples remaining after validation.")
            return None, None
        
        print(f"\n✓ Validation complete: {len(examples)} valid example(s)")
        
        # Create a temporary file with validated examples if we modified anything
        if long_examples and choice in ["1", "2"]:
            temp_file = file_path + ".validated"
            with open(temp_file, 'w', encoding='utf-8') as f:
                for example in examples:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
            print(f"✓ Created validated file: {temp_file}")
            return temp_file, examples
        else:
            return file_path, examples
            
    except Exception as e:
        print(f"✗ Error validating file: {e}")
        return None, None

def upload_training_file(file_path):
    """Upload the training file to OpenAI"""
    print(f"\n{'='*60}")
    print("STEP 1: Uploading Training File")
    print(f"{'='*60}")
    
    try:
        with open(file_path, 'rb') as f:
            file = client.files.create(
                file=f,
                purpose='fine-tune'
            )
        print(f"✓ File uploaded successfully!")
        print(f"  File ID: {file.id}")
        
        print(f"  File Name: {file.filename}")
        print(f"  File Size: {file.bytes} bytes")
        return file.id
    except Exception as e:
        print(f"✗ Error uploading file: {e}")
        return None

def create_fine_tuning_job(file_id, model_name):
    """Create a fine-tuning job"""
    print(f"\n{'='*60}")
    print("STEP 2: Creating Fine-tuning Job")
    print(f"{'='*60}")
    
    try:
        job = client.fine_tuning.jobs.create(
            training_file=file_id,
            model=model_name,
            hyperparameters={
                "n_epochs": 3,  # Number of training epochs (adjust as needed)
            }
        )
        print(f"✓ Fine-tuning job created successfully!")
        print(f"  Job ID: {job.id}")
        print(f"  Model: {job.model}")
        print(f"  Status: {job.status}")
        return job.id
    except Exception as e:
        print(f"✗ Error creating fine-tuning job: {e}")
        error_str = str(e)
        if "model_not_available" in error_str or "not available for fine-tuning" in error_str:
            print(f"\n⚠ Model '{model_name}' is not available for supervised fine-tuning.")
            print(f"\nSupported models for supervised fine-tuning (SFT):")
            print(f"  - gpt-4.1-2025-04-14 (full model)")
            print(f"  - gpt-4.1-mini-2025-04-14 (recommended)")
            print(f"  - gpt-4.1-nano-2025-04-14 (smallest)")
            print(f"\nNote: o4-mini-2025-04-16 is only for reinforcement fine-tuning (RFT), not SFT.")
            print(f"\nCheck OpenAI documentation for the latest supported models:")
            print(f"  https://platform.openai.com/docs/guides/fine-tuning")
        return None

def monitor_training(job_id):
    """Monitor the fine-tuning job progress"""
    print(f"\n{'='*60}")
    print("STEP 3: Monitoring Training Progress")
    print(f"{'='*60}")
    print("Press Ctrl+C to stop monitoring (job will continue running)\n")
    
    try:
        while True:
            job = client.fine_tuning.jobs.retrieve(job_id)
            
            # Clear previous output (works in most terminals)
            print("\033[2J\033[H", end="")
            print(f"{'='*60}")
            print(f"Training Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            print(f"Job ID: {job.id}")
            print(f"Status: {job.status}")
            print(f"Model: {job.model}")
            
            if hasattr(job, 'fine_tuned_model') and job.fine_tuned_model:
                print(f"Fine-tuned Model: {job.fine_tuned_model}")
            
            # Show training metrics if available
            if hasattr(job, 'trained_tokens') and job.trained_tokens:
                print(f"Trained Tokens: {job.trained_tokens}")
            
            # Show events/history
            if hasattr(job, 'events') and job.events:
                print(f"\nRecent Events:")
                for event in job.events.data[-5:]:  # Show last 5 events
                    print(f"  [{event.created_at}] {event.level}: {event.message}")
            
            # Check if job is complete
            if job.status == "succeeded":
                print(f"\n{'='*60}")
                print("✓ Training completed successfully!")
                print(f"{'='*60}")
                if hasattr(job, 'fine_tuned_model') and job.fine_tuned_model:
                    print(f"Fine-tuned Model ID: {job.fine_tuned_model}")
                    return job.fine_tuned_model
                break
            elif job.status == "failed":
                print(f"\n{'='*60}")
                print("✗ Training failed!")
                print(f"{'='*60}")
                if hasattr(job, 'error') and job.error:
                    print(f"Error: {job.error}")
                break
            
            # Wait before next check
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped. Job will continue running.")
        print(f"You can check status later with job ID: {job_id}")
        return None
    except Exception as e:
        print(f"\n✗ Error monitoring job: {e}")
        return None

def get_training_metrics(job_id):
    """Get detailed training metrics"""
    print(f"\n{'='*60}")
    print("STEP 4: Training Metrics")
    print(f"{'='*60}")
    
    try:
        job = client.fine_tuning.jobs.retrieve(job_id)
        
        # Get training events for detailed metrics
        events = client.fine_tuning.jobs.list_events(job_id=job_id, limit=50)
        
        print(f"\nTraining Events Summary:")
        print(f"{'-'*60}")
        
        for event in events.data:
            print(f"[{event.created_at}] {event.level}: {event.message}")
        
        # Try to get metrics if available
        if hasattr(job, 'result_files') and job.result_files:
            print(f"\nResult Files:")
            for file_id in job.result_files:
                file_info = client.files.retrieve(file_id)
                print(f"  - {file_info.filename} (ID: {file_id})")
                # You can download and parse this file for detailed metrics
        
        return True
    except Exception as e:
        print(f"✗ Error getting metrics: {e}")
        return False

def test_fine_tuned_model(model_id, test_prompt):
    """Test the fine-tuned model with a sample prompt"""
    print(f"\n{'='*60}")
    print("STEP 5: Testing Fine-tuned Model")
    print(f"{'='*60}")
    
    try:
        print(f"Test Prompt: {test_prompt}\n")
        print("Response:")
        print("-" * 60)
        
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        print(response.choices[0].message.content)
        print("-" * 60)
        
        print(f"\nModel: {response.model}")
        print(f"Tokens Used: {response.usage.total_tokens}")
        print(f"  - Prompt: {response.usage.prompt_tokens}")
        print(f"  - Completion: {response.usage.completion_tokens}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing model: {e}")
        return False

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("OpenAI Fine-tuning Pipeline")
    print("="*60)
    print(f"Training File: {TRAINING_FILE}")
    print(f"Base Model: {MODEL_NAME}")
    print("="*60)
    
    # Step 0: Validate training file
    validated_file, examples = validate_and_fix_training_file(TRAINING_FILE, MODEL_NAME)
    if not validated_file:
        print("\n✗ Failed to validate training file. Exiting.")
        return
    
    # Step 1: Upload training file
    file_id = upload_training_file(validated_file)
    if not file_id:
        print("\n✗ Failed to upload file. Exiting.")
        return
    
    # Clean up temporary file if created
    if validated_file != TRAINING_FILE and os.path.exists(validated_file):
        try:
            os.remove(validated_file)
            print(f"\n✓ Cleaned up temporary file: {validated_file}")
        except:
            pass
    
    # Wait a moment for file to be processed
    print("\nWaiting for file to be processed...")
    time.sleep(5)
    
    # Step 2: Create fine-tuning job
    job_id = create_fine_tuning_job(file_id, MODEL_NAME)
    if not job_id:
        print("\n✗ Failed to create fine-tuning job. Exiting.")
        return
    
    # Step 3: Monitor training
    fine_tuned_model_id = monitor_training(job_id)
    
    if fine_tuned_model_id:
        # Step 4: Get training metrics
        get_training_metrics(job_id)
        
        # Step 5: Test the model
        print("\n" + "="*60)
        test_prompt = input("Enter a test prompt to try the fine-tuned model (or press Enter for default): ").strip()
        if not test_prompt:
            # Use a sample prompt based on your dataset
            test_prompt = "Lluis Companys, 23 - Punto 2 y 3"
        
        test_fine_tuned_model(fine_tuned_model_id, test_prompt)
        
        print(f"\n{'='*60}")
        print("✓ Fine-tuning pipeline completed!")
        print(f"{'='*60}")
        print(f"Fine-tuned Model ID: {fine_tuned_model_id}")
        print(f"You can now use this model in your applications.")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("Training is still in progress or failed.")
        print(f"Job ID: {job_id}")
        print(f"You can check status later using:")
        print(f"  client.fine_tuning.jobs.retrieve('{job_id}')")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    # Check for API key
   
    
    main()

