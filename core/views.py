import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .supabase_client import supabase
from otp_app.models import OTP

# ============================================
# INDEX PAGE
# ============================================

def index(request):
    return render(request, 'index.html')


# ============================================
# ADMIN LOGIN (Supabase se verify - All Users)
# ============================================

def admin_login(request):
    # Agar already logged in hai toh dashboard pe bhejo
    if request.session.get('logged_in'):
        role = request.session.get('user_role')
        if role == 'admin':
            return redirect('admin_dashboard')
        # elif role == 'tpo':
        #     return redirect('tpo_dashboard')
        # elif role == 'faculty':
        #     return redirect('faculty_dashboard')
        # elif role == 'student':
        #     return redirect('student_dashboard')
        # elif role == 'hod':
        #     return redirect('hod_dashboard')
        # elif role == 'parent':
        #     return redirect('parent_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Supabase se user fetch karo
            response = supabase.table('user_account')\
                .select('*')\
                .eq('username', username)\
                .execute()
            
            if response.data:
                user = response.data[0]
                
                # Check if user is active
                if not user.get('is_active', True):
                    messages.error(request, '❌ Your account is inactive. Contact admin.')
                    return render(request, 'admin_login.html')
                
                # Get role
                role = user.get('role_id')
                password_hash = user.get('password_hash', '')
                
                # 🔑 Password verify karo (bcrypt support)
                password_match = False
                try:
                    if password_hash.startswith('$2b$'):
                        password_match = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
                    else:
                        password_match = (password == password_hash)
                except:
                    password_match = (password == password_hash)
                
                if password_match:
                    # Session mein store karo
                    request.session['logged_in'] = True
                    request.session['user_id'] = user.get('user_id')
                    request.session['username'] = user.get('username')
                    request.session['user_role'] = role
                    
                    messages.success(request, f'Welcome {username}! 🎉')
                    
                    # Redirect based on role
                    if role == 1:  # Admin
                        return redirect('admin_dashboard')
                    # elif role == 2:  # TPO
                    #     return redirect('tpo_dashboard')
                    # elif role == 3:  # Faculty
                    #     return redirect('faculty_dashboard')
                    # elif role == 4:  # Student
                    #     return redirect('student_dashboard')
                    # elif role == 5:  # HOD
                    #     return redirect('hod_dashboard')
                    # elif role == 6:  # Parent
                    #     return redirect('parent_dashboard')
                    else:
                        messages.info(request, 'Role-based dashboard coming soon!')
                        return redirect('admin_dashboard')
                else:
                    messages.error(request, '❌ Invalid Password!')
            else:
                messages.error(request, '❌ User not found!')
                
        except Exception as e:
            messages.error(request, f'❌ Database Error: {e}')
            print(f"Error: {e}")
    
    return render(request, 'admin_login.html')


# ============================================
# ADMIN DASHBOARD
# ============================================

def admin_dashboard(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'user_id': request.session.get('user_id'),
        'role': request.session.get('user_role'),
    }
    return render(request, 'admin_dashboard.html', context)


# ============================================
# ADMIN LOGOUT
# ============================================

def admin_logout(request):
    request.session.flush()
    messages.success(request, '✅ Logged out successfully!')
    return redirect('admin_login')

# ============================================
# GENERATE OTP
# ============================================

def generate_otp():
    return str(random.randint(100000, 999999))


# ============================================
# STUDENT LOGIN — STEP 1: Send OTP
# ============================================

def student_login(request):
    # Agar already logged in hai toh dashboard pe bhejo
    if request.session.get('student_logged_in'):
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        whatsapp_no = request.POST.get('whatsapp_no')
        
        if not whatsapp_no:
            messages.error(request, '❌ Please enter your WhatsApp number!')
            return render(request, 'student_login.html')
        
        try:
            # Check if student exists in Supabase
            response = supabase.table('student')\
                .select('*')\
                .eq('whatsapp_no', whatsapp_no)\
                .execute()
            
            if response.data:
                student = response.data[0]
                
                # Generate OTP
                otp_code = generate_otp()
                
                # Delete old OTPs for this number
                OTP.objects.filter(phone_number=whatsapp_no, is_verified=False).delete()
                
                # Save new OTP
                OTP.objects.create(
                    phone_number=whatsapp_no,
                    otp_code=otp_code,
                    expires_at=timezone.now() + timedelta(minutes=5)
                )
                
                # ✅ Console pe OTP print karo
                print(f"📱 OTP for {student['full_name']} ({whatsapp_no}): {otp_code}")
                
                # Store in session
                request.session['student_whatsapp'] = whatsapp_no
                request.session['student_name'] = student['full_name']
                request.session['student_id'] = student['student_id']
                
                messages.success(request, f'✅ OTP sent to {whatsapp_no}! Check console.')
                return redirect('student_verify_otp')
            else:
                messages.error(request, '❌ WhatsApp number not registered!')
                
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"Error: {e}")
    
    return render(request, 'student_login.html')


# ============================================
# STUDENT LOGIN — STEP 2: Verify OTP
# ============================================

def student_verify_otp(request):
    # Check if OTP was sent
    if not request.session.get('student_whatsapp'):
        messages.error(request, '❌ Please request OTP first!')
        return redirect('student_login')
    
    whatsapp_no = request.session.get('student_whatsapp')
    student_name = request.session.get('student_name', 'Student')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        if not otp_code:
            messages.error(request, '❌ Please enter OTP!')
            return render(request, 'student_verify_otp.html', {
                'whatsapp_no': whatsapp_no,
                'student_name': student_name
            })
        
        try:
            # Verify OTP
            otp_record = OTP.objects.filter(
                phone_number=whatsapp_no,
                otp_code=otp_code,
                is_verified=False
            ).latest('created_at')
            
            if otp_record.is_expired():
                messages.error(request, '❌ OTP has expired! Please request again.')
                return redirect('student_login')
            
            # Mark as verified
            otp_record.is_verified = True
            otp_record.save()
            
            # Set session
            request.session['student_logged_in'] = True
            request.session['student_whatsapp'] = whatsapp_no
            request.session['student_name'] = student_name
            
            messages.success(request, f'🎉 Welcome {student_name}!')
            return redirect('student_dashboard')
            
        except OTP.DoesNotExist:
            messages.error(request, '❌ Invalid OTP! Please try again.')
    
    return render(request, 'student_verify_otp.html', {
        'whatsapp_no': whatsapp_no,
        'student_name': student_name
    })


# ============================================
# STUDENT DASHBOARD
# ============================================

def student_dashboard(request):
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    context = {
        'student_name': request.session.get('student_name', 'Student'),
        'student_id': request.session.get('student_id'),
        'whatsapp_no': request.session.get('student_whatsapp'),
    }
    
    return render(request, 'student_dashboard.html', context)


# ============================================
# STUDENT LOGOUT
# ============================================

def student_logout(request):
    request.session.flush()
    messages.success(request, '✅ Logged out successfully!')
    return redirect('student_login')

from django.shortcuts import render, redirect
from django.contrib import messages
from .supabase_client import supabase

# ============================================
# TPO LOGIN
# ============================================

def tpo_login(request):
    # Agar already logged in hai toh dashboard pe bhejo
    if request.session.get('tpo_logged_in'):
        return redirect('tpo_dashboard')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')
        
        if not user_id or not password:
            messages.error(request, '❌ Please enter both User ID and Password!')
            return render(request, 'tpo_login.html')
        
        try:
            # Supabase se TPO fetch karo
            response = supabase.table('tpo')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data:
                tpo = response.data[0]
                
                # Check if active
                if not tpo.get('is_active', True):
                    messages.error(request, '❌ Your account is inactive. Contact admin.')
                    return render(request, 'tpo_login.html')
                
                # 🔑 Password verify (abhi simple comparison)
                if tpo.get('password_hash') == password:
                    # Session mein store karo
                    request.session['tpo_logged_in'] = True
                    request.session['tpo_id'] = tpo.get('tpo_id')
                    request.session['tpo_user_id'] = tpo.get('user_id')
                    request.session['tpo_name'] = tpo.get('full_name')
                    request.session['tpo_department'] = tpo.get('department')
                    
                    messages.success(request, f'🎉 Welcome {tpo["full_name"]}!')
                    return redirect('tpo_dashboard')
                else:
                    messages.error(request, '❌ Invalid Password!')
            else:
                messages.error(request, '❌ User ID not found!')
                
        except Exception as e:
            messages.error(request, f'❌ Database Error: {e}')
            print(f"Error: {e}")
    
    return render(request, 'tpo_login.html')


# ============================================
# TPO DASHBOARD
# ============================================

def tpo_dashboard(request):
    if not request.session.get('tpo_logged_in'):
        return redirect('tpo_login')
    
    context = {
        'tpo_name': request.session.get('tpo_name', 'TPO'),
        'tpo_user_id': request.session.get('tpo_user_id'),
        'tpo_department': request.session.get('tpo_department', 'All'),
    }
    
    return render(request, 'tpo_dashboard.html', context)


# ============================================
# TPO LOGOUT
# ============================================

def tpo_logout(request):
    request.session.flush()
    messages.success(request, '✅ Logged out successfully!')
    return redirect('tpo_login')