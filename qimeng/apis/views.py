from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, HttpResponseBadRequest, HttpRequest, JsonResponse

from .models import DetectionRequest

# Create your views here.
def ping(request):
    return HttpResponse('pong')

def test(request):
    det_reqs = DetectionRequest.objects.all()
    return HttpResponse('\n'.join(([str(i) for i in det_reqs])))

def create_det_req(request: HttpRequest):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    if 'station_id' not in request.POST:
        return HttpResponseBadRequest()
    station_id = request.POST.get('station_id')
    search_key = request.POST.get('station_id', '') 
    order_id = request.POST.get('order_id', '')
    det_req = DetectionRequest(
        station_id=station_id,
        search_key=search_key,
        order_id=order_id
    )
    det_req.save()
    return JsonResponse({
        'detection_id': det_req.id
    })

def query_det_req(request, id):
    if request.method != 'GET':
        return HttpResponseBadRequest()
    det_req = DetectionRequest.objects.filter(id=id)
    if len(det_req) > 1:
        return HttpResponseServerError()
    if len(det_req) == 0:
        return HttpResponseNotFound()
    det_req = det_req[0]
    return JsonResponse({
        'detection_id': det_req.id,
        'status': det_req.status,
    })

def update_list(request):
    return ...