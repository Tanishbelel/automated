from celery import Celery, group
from celery.result import AsyncResult
import os
import time
import uuid

# macOS Fork Safety Fix for OpenCV/Tesseract
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

# Initialize Celery app
redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app = Celery('metadata_pipeline', broker=redis_url, backend=redis_url)

@app.task(name="process_file_task")
def process_file_task(filepath: str, original_filename: str, platform: str, encrypt: bool, password: str, user_id: int = None, job_id: str = None, apply_signature: bool = True, apply_redaction: bool = True):
    """
    Celery task to process a single file through the pipeline and save to DB.
    """
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automated.settings')
    django.setup()
    
    from .orchestrator import run_pipeline
    from main.models import FileAnalysis
    from django.core.files.base import ContentFile
    from django.contrib.auth.models import User
    
    file_analysis = None
    try:
        print(f"🔥 Task started for: {original_filename} (Job: {job_id})")
        
        # 1. Create initial record
        user = User.objects.get(id=user_id) if user_id else None
        file_analysis = FileAnalysis.objects.create(
            user=user,
            original_filename=original_filename,
            file_type='application/octet-stream',
            file_size=os.path.getsize(filepath),
            platform=platform,
            status='processing',
            job_id=job_id
        )
        
        # 2. SAVE THE ORIGINAL FILE BEFORE IT GETS MODIFIED IN PLACE
        with open(filepath, 'rb') as f:
            file_analysis.original_file.save(original_filename, ContentFile(f.read()), save=True)

        # 3. Run Pipeline (This modifies filepath in place)
        result = run_pipeline(filepath, platform, encrypt, password, apply_signature=apply_signature, apply_redaction=apply_redaction)
        
        # 4. Update the record with results
        file_analysis.risk_score = result.risk_score
        file_analysis.status = 'cleaned'
        
        with open(result.output_file_path, 'rb') as f:
            content = f.read()
            f_name = f"clean_{original_filename}"
            file_analysis.cleaned_file.save(f_name, ContentFile(content), save=True)
        
        print(f"✅ Record saved: {file_analysis.id}")
            
        res_dict = result.model_dump()
        res_dict['analysis_id'] = str(file_analysis.id)
        res_dict['status'] = 'cleaned'
        res_dict['original_filename'] = original_filename
        res_dict['download_url'] = f"/analyses/{file_analysis.id}/download_clean/"
        res_dict['processing_timestamp'] = res_dict['processing_timestamp'].isoformat()
        return res_dict
        
    except Exception as e:
        import traceback
        print(f"❌ Task Error: {str(e)}")
        print(traceback.format_exc())
        
        if file_analysis:
            file_analysis.status = 'failed'
            file_analysis.save()
            
        if os.path.exists(filepath):
            try:
                os.unlink(filepath)
            except:
                pass
        return {"status": "error", "message": str(e), "filename": original_filename}

def submit_bulk(files_data: list, platform: str, encrypt: bool, password: str, user_id: int = None, apply_signature: bool = True, apply_redaction: bool = True) -> str:
    """
    Submits all files as individual Celery tasks in a group.
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Store the total count in Redis
    try:
        from django.core.cache import cache
        cache.set(f"bulk_total_{job_id}", len(files_data), timeout=3600)
    except:
        pass

    job = group(process_file_task.s(data[0], data[1], platform, encrypt, password, user_id, job_id, apply_signature, apply_redaction) for data in files_data)
    result = job.apply_async()
    return job_id

def get_bulk_status(job_id: str) -> dict:
    """
    Returns the status of a bulk processing job by querying the database.
    """
    from main.models import FileAnalysis
    
    records = FileAnalysis.objects.filter(job_id=job_id)
    print(f"🔍 Status Check: Found {records.count()} records for Job {job_id}")
    
    if not records.exists():
        return {"status": "pending", "message": "Job initializing..."}
        
    from django.core.cache import cache
    total = cache.get(f"bulk_total_{job_id}")
    if total is None:
        total = records.count()
    
    completed = records.filter(status='cleaned').count()
    failed = records.filter(status='failed').count()
    results = []
    
    for rec in records:
        results.append({
            "analysis_id": str(rec.id),
            "filename": rec.original_filename,
            "status": rec.status,
            "risk_score": rec.risk_score,
            "download_url": f"/analyses/{rec.id}/download_clean/" if rec.status == 'cleaned' else None
        })
                
    # Determine overall status
    job_status = "processing"
    if completed + failed >= total:
        job_status = "completed"
                
    return {
        "job_id": job_id,
        "status": job_status,
        "total": total,
        "completed": completed,
        "failed": failed,
        "results": results
    }
