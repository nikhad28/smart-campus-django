import base64
import requests
import os
import uuid
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from supabase import create_client

# ============================================
# SUPABASE CONNECTION
# ============================================

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)


# ============================================
# IMAGE UPLOAD — MULTIPLE METHODS
# ============================================

def upload_image(image_file):
    """Try multiple methods: Cloudinary → ImgBB → Local Storage"""
    
    # ===== Method 1: Cloudinary =====
    try:
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            secure=True
        )
        
        result = cloudinary.uploader.upload(
            image_file, 
            folder="infrastructure_issues",
            transformation=[{'quality': 'auto', 'width': 800, 'crop': 'limit'}]
        )
        url = result.get('secure_url', '')
        if url:
            print(f"✅ Uploaded to Cloudinary: {url}")
            return url
    except Exception as e:
        print(f"⚠️ Cloudinary failed: {e}")
    
    # ===== Method 2: ImgBB =====
    api_key = os.getenv('IMGBB_API_KEY')
    if api_key:
        try:
            url = "https://api.imgbb.com/1/upload"
            image_file.seek(0)
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            payload = {
                'key': api_key,
                'image': image_data,
            }
            
            response = requests.post(url, data=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                url = data.get('data', {}).get('url', '')
                if url:
                    print(f"✅ Uploaded to ImgBB: {url}")
                    return url
        except Exception as e:
            print(f"⚠️ ImgBB failed: {e}")
    
    # ===== Method 3: Local Storage (Fallback) =====
    try:
        ext = image_file.name.split('.')[-1]
        filename = f"infrastructure_issues/{uuid.uuid4()}.{ext}"
        image_file.seek(0)
        path = default_storage.save(filename, ContentFile(image_file.read()))
        url = default_storage.url(path)
        print(f"✅ Uploaded to Local: {url}")
        return url
    except Exception as e:
        print(f"❌ All upload methods failed: {e}")
        return ''


# ============================================
# REPORT ISSUE — Student/Faculty/TPO
# ============================================

def report_issue(request):
    if not (request.session.get('student_logged_in') or 
            request.session.get('tpo_logged_in') or 
            request.session.get('faculty_logged_in')):
        messages.error(request, '❌ Please login to report an issue.')
        return redirect('admin_login')
    
    if request.method == 'POST':
        reported_by = request.POST.get('reported_by')
        reported_by_email = request.POST.get('reported_by_email')
        reported_by_phone = request.POST.get('reported_by_phone', '')
        category = request.POST.get('category')
        description = request.POST.get('description')
        location = request.POST.get('location')
        
        image_url = ''
        if request.FILES.get('image'):
            image_file = request.FILES['image']
            image_url = upload_image(image_file)
            print(f"📸 Final Image URL: {image_url}")
        
        data = {
            'reported_by': reported_by,
            'reported_by_email': reported_by_email,
            'reported_by_phone': reported_by_phone,
            'category': category,
            'description': description,
            'location': location,
            'image_url': image_url,
            'status': 'pending'
        }
        
        try:
            supabase.table('infrastructure_issues').insert(data).execute()
            messages.success(request, '✅ Issue reported successfully!')
            return redirect('report_issue')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"❌ Supabase Insert Error: {e}")
    
    return render(request, 'report_issue.html')


# ============================================
# ISSUES DASHBOARD — Admin / TPO
# ============================================

def issues_dashboard(request):
    if not (request.session.get('logged_in') or request.session.get('tpo_logged_in')):
        messages.error(request, '❌ Access denied! Only Admin and TPO can view this page.')
        return redirect('admin_login')
    
    try:
        response = supabase.table('infrastructure_issues')\
            .select('*')\
            .order('created_at', desc=True)\
            .execute()
        issues = response.data if hasattr(response, 'data') else []
    except Exception as e:
        issues = []
        print(f"Error: {e}")
    
    context = {
        'issues': issues,
        'pending_count': len([i for i in issues if i.get('status') == 'pending']),
        'in_progress_count': len([i for i in issues if i.get('status') == 'in_progress']),
        'resolved_count': len([i for i in issues if i.get('status') == 'resolved']),
        'is_admin': request.session.get('logged_in') and request.session.get('user_role') == 1,
        'is_tpo': request.session.get('tpo_logged_in', False),
    }
    return render(request, 'issues_dashboard.html', context)


# ============================================
# UPDATE STATUS — Admin / TPO
# ============================================

@csrf_exempt
def update_issue_status(request, issue_id):
    if not (request.session.get('logged_in') or request.session.get('tpo_logged_in')):
        messages.error(request, '❌ Access denied!')
        return redirect('admin_login')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        try:
            supabase.table('infrastructure_issues')\
                .update({'status': status, 'updated_at': datetime.now().isoformat()})\
                .eq('id', issue_id)\
                .execute()
            messages.success(request, f'✅ Status updated to "{status}"!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
        
        return redirect('issues_dashboard')


# ============================================
# DELETE ISSUE — ONLY ADMIN
# ============================================

@csrf_exempt
def delete_issue(request, issue_id):
    if not (request.session.get('logged_in') and request.session.get('user_role') == 1):
        messages.error(request, '❌ Access denied! Only Admin can delete issues.')
        return redirect('issues_dashboard')
    
    if request.method == 'POST':
        try:
            supabase.table('infrastructure_issues').delete().eq('id', issue_id).execute()
            messages.success(request, '✅ Issue deleted successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
        
        return redirect('issues_dashboard')