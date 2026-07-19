import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile, JobApplication
from .filters import filter_applications

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
                status = 400,
            )
        name = body.get('name')
        email = body.get('email')

        if not name or not email:
            return JsonResponse(
                {'error': 'name and email are required'},
                status = 400,
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
        data ={
            'id': user.id,
            'name': user.name,
            'email':user.email,
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
    if request.method == 'GET':
        applications = JobApplication.objects.all()

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
                status = 400,
            )


        title = body.get('title')
        company = body.get('company')
        status_value = body.get('status')

        if not title or not company or not status_value:
            return JsonResponse(
                {'error': 'title, company and status are required'},
                status = 400,
            )

        allowed_status = [choice[0] for choice in JobApplication.Status.choices]
        if status_value not in allowed_status:
            return JsonResponse(
                {'error': 'Invalid status'},
                status = 400,
            )

        application = JobApplication.objects.create(
            title=title,
            company=company,
            status=status_value,
            date_applied = body.get('date_applied'),
            job_link = body.get('job_link', ''),
            location = body.get('location', ''),
            salary = body.get('salary', ''),
            contact_name = body.get('contact_name', ''),
            notes = body.get('notes', ''),
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
    try:
        application = JobApplication.objects.get(id=id)

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
                status = 400,
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
                    status = 400,
                )

            application.status = body['status']

        if 'date_applied' in body:
            application.date_applied = body['date_applied']

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