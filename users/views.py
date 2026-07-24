import json
import random

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .filters import filter_applications
from .models import JobApplication, PasswordResetCode, Resume, UserProfile


def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def serialize_application(application):
    return {
        'id': application.id,
        'title': application.title,
        'company': application.company,
        'status': application.status,
        'label_color': application.label_color,
        'date_applied': application.date_applied.isoformat() if application.date_applied else None,
        'job_link': application.job_link,
        'location': application.location,
        'salary': application.salary,
        'contact_name': application.contact_name,
        'notes': application.notes,
        'is_favorite': application.is_favorite,
        'resume_id': application.resume.id if application.resume else None,
        'resume_title': application.resume.title if application.resume else '',
        'resume_file_url': application.resume.file.url if application.resume and application.resume.file else '',
        'resume_file_name': application.resume.file.name.split('/')[-1] if application.resume and application.resume.file else '',
    }


def serialize_resume(resume):
    return {
        'id': resume.id,
        'title': resume.title,
        'notes': resume.notes,
        'file_name': resume.file.name.split('/')[-1] if resume.file else '',
        'file_url': resume.file.url if resume.file else '',
        'created_at': resume.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': resume.updated_at.strftime('%Y-%m-%d %H:%M'),
    }


def build_profile_payload(user):
    profile = get_or_create_profile(user)
    applications = JobApplication.objects.filter(user=user)
    resumes = Resume.objects.filter(user=user)

    applied_count = applications.filter(status=JobApplication.Status.APPLIED).count()
    interview_count = applications.filter(status=JobApplication.Status.INTERVIEW).count()
    offer_count = applications.filter(status=JobApplication.Status.OFFER).count()
    rejected_count = applications.filter(status=JobApplication.Status.REJECTED).count()
    closed_count = applications.filter(status=JobApplication.Status.CLOSED).count()

    return {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'profile': {
            'avatar_url': profile.avatar.url if profile.avatar else '',
        },
        'stats': {
            'total': applications.count(),
            'applied': applied_count,
            'interview': interview_count,
            'offer': offer_count,
            'rejected': rejected_count,
            'closed': closed_count,
        },
        'resumes': [serialize_resume(resume) for resume in resumes],
    }


def landing_page(request):
    return render(request, 'landing.html')


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def dashboard_page(request):
    return render(request, 'dashboard.html')


def applications_page(request):
    return render(request, 'applications.html')


def filters_page(request):
    return render(request, 'filters.html')


def profile_page(request):
    return render(request, 'profile.html')


def job_tracker_page(request):
    return render(request, 'job_tracker.html')


@csrf_exempt
@require_POST
def register_view(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username:
        return JsonResponse({"error": "Username is required"}, status=400)

    if not password:
        return JsonResponse({"error": "Password is required"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)

    if email and User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"error": "Email already exists"}, status=400)

    try:
        validate_password(password)
    except ValidationError as error:
        return JsonResponse({"error": " ".join(error.messages)}, status=400)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    get_or_create_profile(user)
    login(request, user)

    return JsonResponse({
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }, status=201)


@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    username = (body.get('username') or '').strip()
    password = body.get('password') or ''

    if not username or not password:
        return JsonResponse({'error': 'Username and password are required'}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({'error': 'Invalid username or password'}, status=401)

    get_or_create_profile(user)
    login(request, user)

    return JsonResponse({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
    })


@csrf_exempt
def logout_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    logout(request)

    return JsonResponse({
        'message': 'Logout successful'
    })


def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False}, status=200)

    return JsonResponse({
        'authenticated': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        }
    })


@csrf_exempt
def request_password_reset_code_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = (body.get('email') or '').strip().lower()

    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    user = User.objects.filter(email__iexact=email).first()

    if not user:
        return JsonResponse({'error': 'User with this email was not found'}, status=404)

    PasswordResetCode.objects.filter(user=user).delete()

    code = str(random.randint(100000, 999999))

    reset_code = PasswordResetCode.objects.create(
        user=user,
        email=user.email,
        code=code,
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )

    try:
        send_mail(
            subject='Your Job Tracker password reset code',
            message=f'Your verification code is: {reset_code.code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        return JsonResponse({'error': 'Failed to send email. Check email settings.'}, status=500)

    return JsonResponse({
        'message': 'Verification code sent successfully'
    })


@csrf_exempt
def verify_password_reset_code_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = (body.get('email') or '').strip().lower()
    code = (body.get('code') or '').strip()

    if not email or not code:
        return JsonResponse({'error': 'Email and code are required'}, status=400)

    reset_code = PasswordResetCode.objects.filter(
        email__iexact=email,
        code=code
    ).order_by('-created_at').first()

    if not reset_code:
        return JsonResponse({'error': 'Invalid verification code'}, status=400)

    if reset_code.is_expired():
        return JsonResponse({'error': 'Verification code has expired'}, status=400)

    reset_code.is_verified = True
    reset_code.save()

    return JsonResponse({
        'message': 'Code verified successfully'
    })


@csrf_exempt
def confirm_password_reset_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = (body.get('email') or '').strip().lower()
    code = (body.get('code') or '').strip()
    new_password = body.get('new_password') or ''

    if not email or not code or not new_password:
        return JsonResponse({'error': 'Email, code and new_password are required'}, status=400)

    reset_code = PasswordResetCode.objects.filter(
        email__iexact=email,
        code=code,
        is_verified=True
    ).order_by('-created_at').first()

    if not reset_code:
        return JsonResponse({'error': 'Verified code was not found'}, status=400)

    if reset_code.is_expired():
        return JsonResponse({'error': 'Verification code has expired'}, status=400)

    user = reset_code.user

    try:
        validate_password(new_password, user=user)
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=400)

    user.set_password(new_password)
    user.save()

    PasswordResetCode.objects.filter(user=user).delete()

    return JsonResponse({
        'message': 'Password updated successfully'
    })


@csrf_exempt
def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    user = request.user
    profile = get_or_create_profile(user)

    if request.method == 'GET':
        return JsonResponse(build_profile_payload(user))

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        username = body.get('username')
        email = body.get('email')

        if username is not None:
            username = username.strip()
            if not username:
                return JsonResponse({'error': 'Username cannot be empty'}, status=400)

            existing_user = User.objects.filter(username=username).exclude(id=user.id).first()
            if existing_user:
                return JsonResponse({'error': 'Username already exists'}, status=400)

            user.username = username

        if email is not None:
            email = email.strip()
            existing_email_user = User.objects.filter(email__iexact=email).exclude(id=user.id).first()
            if email and existing_email_user:
                return JsonResponse({'error': 'Email already exists'}, status=400)
            user.email = email

        user.save()

        payload = build_profile_payload(user)
        payload['message'] = 'Profile updated successfully'
        return JsonResponse(payload)

    if request.method == 'POST':
        avatar = request.FILES.get('avatar')
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')

        if avatar:
            profile.avatar = avatar
            profile.save()

        if new_password:
            if not current_password:
                return JsonResponse({'error': 'Current password is required'}, status=400)

            if not user.check_password(current_password):
                return JsonResponse({'error': 'Current password is incorrect'}, status=400)

            try:
                validate_password(new_password, user=user)
            except ValidationError as error:
                return JsonResponse({'error': ' '.join(error.messages)}, status=400)

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)

        payload = build_profile_payload(user)
        payload['message'] = 'Settings updated successfully'
        return JsonResponse(payload)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def resume_home(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'GET':
        resumes = Resume.objects.filter(user=request.user)
        return JsonResponse({'resumes': [serialize_resume(resume) for resume in resumes]})

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        notes = (request.POST.get('notes') or '').strip()
        resume_file = request.FILES.get('file')

        if not title:
            return JsonResponse({'error': 'Resume title is required'}, status=400)

        resume = Resume.objects.create(
            user=request.user,
            title=title,
            notes=notes,
            file=resume_file,
        )

        return JsonResponse(serialize_resume(resume), status=201)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def resume_detail(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        resume = Resume.objects.get(id=id, user=request.user)
    except Resume.DoesNotExist:
        return JsonResponse({'error': 'Resume not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_resume(resume))

    if request.method == 'PATCH':
        title = (request.POST.get('title') or '').strip()
        notes = (request.POST.get('notes') or '').strip()
        resume_file = request.FILES.get('file')

        if title:
            resume.title = title

        resume.notes = notes

        if resume_file:
            resume.file = resume_file

        resume.save()
        return JsonResponse(serialize_resume(resume))

    if request.method == 'DELETE':
        resume.delete()
        return HttpResponse(status=204)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def favorites_home(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'GET':
        applications = JobApplication.objects.filter(
            user=request.user,
            is_favorite=True
        )
        data = [serialize_application(application) for application in applications]
        return JsonResponse({'applications': data})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def favorite_detail(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        application = JobApplication.objects.get(id=id, user=request.user)
    except JobApplication.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'is_favorite' not in body:
            return JsonResponse({'error': 'is_favorite is required'}, status=400)

        application.is_favorite = bool(body['is_favorite'])
        application.save()

        return JsonResponse(serialize_application(application))

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def application_home(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'GET':
        applications = JobApplication.objects.filter(user=request.user)

        applications, error = filter_applications(applications, request.GET)

        if error:
            return JsonResponse({'error': error}, status=400)

        data = [serialize_application(application) for application in applications]
        return JsonResponse({'applications': data})

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        title = body.get('title')
        company = body.get('company')
        status_value = body.get('status')
        label_color_value = body.get('label_color', JobApplication.LabelColor.NONE)
        resume_id = body.get('resume_id')

        if not title or not company or not status_value:
            return JsonResponse({'error': 'title, company and status are required'}, status=400)

        allowed_statuses = [choice[0] for choice in JobApplication.Status.choices]
        if status_value not in allowed_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        allowed_colors = [choice[0] for choice in JobApplication.LabelColor.choices]
        if label_color_value not in allowed_colors:
            return JsonResponse({'error': 'Invalid label color'}, status=400)

        resume = None
        if resume_id:
            try:
                resume = Resume.objects.get(id=resume_id, user=request.user)
            except Resume.DoesNotExist:
                return JsonResponse({'error': 'Resume not found'}, status=404)

        application = JobApplication.objects.create(
            user=request.user,
            title=title,
            company=company,
            status=status_value,
            label_color=label_color_value,
            date_applied=body.get('date_applied') or None,
            job_link=body.get('job_link', ''),
            location=body.get('location', ''),
            salary=body.get('salary', ''),
            contact_name=body.get('contact_name', ''),
            notes=body.get('notes', ''),
            resume=resume,
        )

        return JsonResponse(serialize_application(application), status=201)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def application_detail(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        application = JobApplication.objects.get(id=id, user=request.user)
    except JobApplication.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_application(application))

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'title' in body:
            application.title = body['title']

        if 'company' in body:
            application.company = body['company']

        if 'status' in body:
            allowed_statuses = [choice[0] for choice in JobApplication.Status.choices]
            if body['status'] not in allowed_statuses:
                return JsonResponse({'error': 'Invalid status'}, status=400)
            application.status = body['status']

        if 'label_color' in body:
            allowed_colors = [choice[0] for choice in JobApplication.LabelColor.choices]
            if body['label_color'] not in allowed_colors:
                return JsonResponse({'error': 'Invalid label color'}, status=400)
            application.label_color = body['label_color']

        if 'date_applied' in body:
            application.date_applied = body['date_applied'] or None

        if 'job_link' in body:
            application.job_link = body['job_link']

        if 'location' in body:
            application.location = body['location']

        if 'salary' in body:
            application.salary = body['salary']

        if 'contact_name' in body:
            application.contact_name = body['contact_name']

        if 'notes' in body:
            application.notes = body['notes']

        if 'is_favorite' in body:
            application.is_favorite = bool(body['is_favorite'])

        if 'resume_id' in body:
            resume_id = body['resume_id']

            if resume_id:
                try:
                    application.resume = Resume.objects.get(id=resume_id, user=request.user)
                except Resume.DoesNotExist:
                    return JsonResponse({'error': 'Resume not found'}, status=404)
            else:
                application.resume = None

        application.save()

        return JsonResponse(serialize_application(application))

    if request.method == 'DELETE':
        application.delete()
        return HttpResponse(status=204)

    return JsonResponse({'error': 'Method not allowed'}, status=405)