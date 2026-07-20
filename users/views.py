import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import UserProfile, JobApplication
from .filters import filter_applications
from django.shortcuts import render


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

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

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
        return JsonResponse(
            {'error': 'Method not allowed'},
            status=405,
        )

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON'},
            status=400,
        )

    username = body.get('username', '').strip()
    password = body.get('password', '').strip()

    if not username or not password:
        return JsonResponse(
            {'error': 'username and password are required'},
            status=400,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return JsonResponse(
            {'error': 'Invalid username or password'},
            status=401,
        )

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
        return JsonResponse(
            {'error': 'Method not allowed'},
            status=405,
        )

    logout(request)

    return JsonResponse({
        'message': 'Logout successful'
    })


def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'authenticated': False},
            status=200,
        )

    return JsonResponse({
        'authenticated': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        }
    })


@csrf_exempt
def user_home(request):
    if request.method == 'GET':
        users = UserProfile.objects.all()

        data = []
        for user in users:
            data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
            })
        return JsonResponse({'users': data})

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON'},
                status=400,
            )

        name = body.get('name')
        email = body.get('email')

        if not name or not email:
            return JsonResponse(
                {'error': 'name and email are required'},
                status=400,
            )

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

    return JsonResponse(
        {'error': 'Method not allowed'},
        status=405,
    )


@csrf_exempt
def user_detail(request, id):
    try:
        user = UserProfile.objects.get(id=id)
    except UserProfile.DoesNotExist:
        return JsonResponse(
            {'error': 'User not found'},
            status=404,
        )

    if request.method == 'GET':
        data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        }
        return JsonResponse(data)

    if request.method == 'PATCH':
        body = json.loads(request.body)

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
        return JsonResponse(
            {},
            status=204,
        )

    return JsonResponse(
        {'error': 'Method not allowed'},
        status=405,
    )


@csrf_exempt
def application_home(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Authentication required'},
            status=401,
        )

    if request.method == 'GET':
        applications = JobApplication.objects.filter(user=request.user)

        applications, error = filter_applications(applications, request.GET)

        if error:
            return JsonResponse(
                {'error': error},
                status=400,
            )

        data = []
        for application in applications:
            data.append({
                'id': application.id,
                'title': application.title,
                'company': application.company,
                'status': application.status,
                'date_applied': application.date_applied,
                'job_link': application.job_link,
                'location': application.location,
                'salary': application.salary,
                'contact_name': application.contact_name,
                'notes': application.notes,
            })

        return JsonResponse({'applications': data})

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON'},
                status=400,
            )

        title = body.get('title')
        company = body.get('company')
        status_value = body.get('status')

        if not title or not company or not status_value:
            return JsonResponse(
                {'error': 'title, company and status are required'},
                status=400,
            )

        allowed_status = [choice[0] for choice in JobApplication.Status.choices]
        if status_value not in allowed_status:
            return JsonResponse(
                {'error': 'Invalid status'},
                status=400,
            )

        application = JobApplication.objects.create(
            user=request.user,
            title=title,
            company=company,
            status=status_value,
            date_applied=body.get('date_applied') or None,
            job_link=body.get('job_link', ''),
            location=body.get('location', ''),
            salary=body.get('salary', ''),
            contact_name=body.get('contact_name', ''),
            notes=body.get('notes', ''),
        )

        return JsonResponse(
            {
                'id': application.id,
                'title': application.title,
                'company': application.company,
                'status': application.status,
                'date_applied': application.date_applied,
                'job_link': application.job_link,
                'location': application.location,
                'salary': application.salary,
                'contact_name': application.contact_name,
                'notes': application.notes,
            },
            status=201,
        )

    return JsonResponse(
        {'error': 'Method not allowed'},
        status=405,
    )


@csrf_exempt
def application_detail(request, id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Authentication required'},
            status=401,
        )

    try:
        application = JobApplication.objects.get(id=id, user=request.user)
    except JobApplication.DoesNotExist:
        return JsonResponse(
            {'error': 'Application not found'},
            status=404,
        )

    if request.method == 'GET':
        data = {
            'id': application.id,
            'title': application.title,
            'company': application.company,
            'status': application.status,
            'date_applied': application.date_applied,
            'job_link': application.job_link,
            'location': application.location,
            'salary': application.salary,
            'contact_name': application.contact_name,
            'notes': application.notes,
        }
        return JsonResponse(data)

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON'},
                status=400,
            )

        if 'title' in body:
            application.title = body['title']

        if 'company' in body:
            application.company = body['company']

        if 'status' in body:
            allowed_statuses = [choice[0] for choice in JobApplication.Status.choices]

            if body['status'] not in allowed_statuses:
                return JsonResponse(
                    {'error': 'Invalid status'},
                    status=400,
                )

            application.status = body['status']

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

        application.save()

        return JsonResponse(
            {
                'id': application.id,
                'title': application.title,
                'company': application.company,
                'status': application.status,
                'date_applied': application.date_applied,
                'job_link': application.job_link,
                'location': application.location,
                'salary': application.salary,
                'contact_name': application.contact_name,
                'notes': application.notes,
            }
        )

    if request.method == 'DELETE':
        application.delete()
        return HttpResponse(status=204)

    return JsonResponse(
        {'error': 'Method not allowed'},
        status=405,
    )

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