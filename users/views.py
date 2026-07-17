import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile

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