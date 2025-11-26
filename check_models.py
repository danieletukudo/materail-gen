from finetune_gpt import client
from datetime import datetime

def list_my_models():
    """List all fine-tuned models and their training jobs"""
    print(f"\n{'='*90}")
    print("My Fine-tuned Models History")
    print(f"{'='*90}")
    
    try:
        # List jobs (default limit is 20, increasing to see more history)
        jobs = client.fine_tuning.jobs.list(limit=50)
        
        print(f"{'Job ID':<30} | {'Status':<15} | {'Created At':<20} | {'Fine-tuned Model ID'}")
        print("-" * 90)
        
        count = 0
        for job in jobs.data:
            created_at = datetime.fromtimestamp(job.created_at).strftime('%Y-%m-%d %H:%M:%S')
            model_id = job.fine_tuned_model if job.fine_tuned_model else "-"
            status = job.status
            
            # Color code status if running in a terminal that supports it
            status_str = status
            if status == "succeeded":
                status_str = f"✓ {status}"
            elif status == "failed":
                status_str = f"✗ {status}"
            elif status == "running":
                status_str = f"⟳ {status}"
            
            print(f"{job.id:<30} | {status_str:<15} | {created_at:<20} | {model_id}")
            if job.fine_tuned_model:
                count += 1
        
        print("-" * 90)
        print(f"Found {count} successfully trained models in the last 50 jobs.")
        print(f"{'='*90}\n")
        
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_my_models()

