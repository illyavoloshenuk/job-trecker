import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .filters import filter_applications
from .models import JobApplication, UserProfile


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
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not username:
        return JsonResponse({'error': 'Username is required'}, status=400)

    if not password:
        return JsonResponse({'error': 'Password is required'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already exists'}, status=400)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    login(request, user)

    return JsonResponse(
        {
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
        },
        status=201,
    )


@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    username = body.get('username', '').strip()
    password = body.get('password', '').strip()

    if not username or not password:
        return JsonResponse({'error': 'username and password are required'}, status=400)

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return JsonResponse({'error': 'Invalid username or password'}, status=401)

    login(request, user)

    return JsonResponse(
        {
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
        }
    )


@csrf_exempt
def logout_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    logout(request)

    return JsonResponse({'message': 'Logout successful'})


def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False}, status=200)

    return JsonResponse(
        {
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
            },
        }
    )


@csrf_exempt
def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    user = request.user
    applications = JobApplication.objects.filter(user=user)

    if request.method == 'GET':
        applied_count = applications.filter(status=JobApplication.Status.APPLIED).count()
        interview_count = applications.filter(status=JobApplication.Status.INTERVIEW).count()
        offer_count = applications.filter(status=JobApplication.Status.OFFER).count()
        rejected_count = applications.filter(status=JobApplication.Status.REJECTED).count()
        closed_count = applications.filter(status=JobApplication.Status.CLOSED).count()

        return JsonResponse(
            {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'stats': {
                    'total': applications.count(),
                    'applied': applied_count,
                    'interview': interview_count,
                    'offer': offer_count,
                    'rejected': rejected_count,
                    'closed': closed_count,
                },
            }
        )

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
            user.email = email.strip()

        user.save()

        applied_count = applications.filter(status=JobApplication.Status.APPLIED).count()
        interview_count = applications.filter(status=JobApplication.Status.INTERVIEW).count()
        offer_count = applications.filter(status=JobApplication.Status.OFFER).count()
        rejected_count = applications.filter(status=JobApplication.Status.REJECTED).count()
        closed_count = applications.filter(status=JobApplication.Status.CLOSED).count()

        return JsonResponse(
            {
                'message': 'Profile updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'stats': {
                    'total': applications.count(),
                    'applied': applied_count,
                    'interview': interview_count,
                    'offer': offer_count,
                    'rejected': rejected_count,
                    'closed': closed_count,
                },
            }
        )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def application_home(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'GET':
        applications = JobApplication.objects.filter(user=request.user).order_by('-id')

        applications, error = filter_applications(applications, request.GET)

        if error:
            return JsonResponse({'error': error}, status=400)

        data = []
        for application in applications:
            data.append(
                {
                    'id': application.id,
                    'title': application.title,
                    'company': application.company,
                    'status': application.status,
                    'label_color': application.label_color,
                    'date_applied': application.date_applied.isoformat() if application.date_applied else '',
                    'job_link': application.job_link,
                    'location': application.location,
                    'salary': application.salary,
                    'contact_name': application.contact_name,
                    'notes': application.notes,
                    'is_favorite': application.is_favorite,
                }
            )

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

        if not title or not company or not status_value:
            return JsonResponse({'error': 'title, company and status are required'}, status=400)

        allowed_statuses = [choice[0] for choice in JobApplication.Status.choices]
        if status_value not in allowed_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        allowed_colors = [choice[0] for choice in JobApplication.LabelColor.choices]
        if label_color_value not in allowed_colors:
            return JsonResponse({'error': 'Invalid label color'}, status=400)

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
            is_favorite=bool(body.get('is_favorite', False)),
        )

        return JsonResponse(
            {
                'id': application.id,
                'title': application.title,
                'company': application.company,
                'status': application.status,
                'label_color': application.label_color,
                'date_applied': application.date_applied.isoformat() if application.date_applied else '',
                'job_link': application.job_link,
                'location': application.location,
                'salary': application.salary,
                'contact_name': application.contact_name,
                'notes': application.notes,
                'is_favorite': application.is_favorite,
            },
            status=201,
        )

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
        return JsonResponse(
            {
                'id': application.id,
                'title': application.title,
                'company': application.company,
                'status': application.status,
                'label_color': application.label_color,
                'date_applied': application.date_applied.isoformat() if application.date_applied else '',
                'job_link': application.job_link,
                'location': application.location,
                'salary': application.salary,
                'contact_name': application.contact_name,
                'notes': application.notes,
                'is_favorite': application.is_favorite,
            }
        )

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

        application.save()

        return JsonResponse(
            {
                'id': application.id,
                'title': application.title,
                'company': application.company,
                'status': application.status,
                'label_color': application.label_color,
                'date_applied': application.date_applied.isoformat() if application.date_applied else '',
                'job_link': application.job_link,
                'location': application.location,
                'salary': application.salary,
                'contact_name': application.contact_name,
                'notes': application.notes,
                'is_favorite': application.is_favorite,
            }
        )

    if request.method == 'DELETE':
        application.delete()
        return HttpResponse(status=204)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@require_http_methods(['PATCH'])
def favorite_toggle_view(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        application = JobApplication.objects.get(id=id, user=request.user)
    except JobApplication.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    application.is_favorite = bool(body.get('is_favorite', False))
    application.save()

    return JsonResponse(
        {
            'id': application.id,
            'is_favorite': application.is_favorite,
        }
    )


@csrf_exempt
def favorites_list_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    applications = JobApplication.objects.filter(
        user=request.user,
        is_favorite=True,
    ).order_by('-id')

    data = []
    for application in applications:
        data.append(
            {
                'id': application.id,
                'title': application.title,
                'company': application.company,
                'status': application.status,
                'label_color': application.label_color,
                'date_applied': application.date_applied.isoformat() if application.date_applied else '',
                'job_link': application.job_link,
                'location': application.location,
                'salary': application.salary,
                'contact_name': application.contact_name,
                'notes': application.notes,
                'is_favorite': application.is_favorite,
            }
        )

    return JsonResponse({'applications': data})


@csrf_exempt
def user_home(request):
    if request.method == 'GET':
        users = UserProfile.objects.all()

        data = []
        for user in users:
            data.append(
                {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                }
            )
        return JsonResponse({'users': data})

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        name = body.get('name')
        email = body.get('email')

        if not name or not email:
            return JsonResponse({'error': 'name and email are required'}, status=400)

        user = UserProfile.objects.create(
            name=name,
            email=email,
        )
        return JsonResponse(
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            status=201,
        )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def user_detail(request, id):
    try:
        user = UserProfile.objects.get(id=id)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            }
        )

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'name' in body:
            user.name = body['name']

        if 'email' in body:
            user.email = body['email']

        user.save()

        return JsonResponse(
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            }
        )

    if request.method == 'DELETE':
        user.delete()
        return JsonResponse({}, status=204)

    return JsonResponse({'error': 'Method not allowed'}, status=405)