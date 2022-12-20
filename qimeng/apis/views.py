from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, HttpResponseBadRequest, HttpRequest, JsonResponse
from django.views import View
import json
import django_rq as rq
import logging

from .models import DetectionRequest
from ctrl.on_submit import on_submit


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
    search_key = request.POST.get('search_key', None)
    order_list = request.POST.get('order_list', None)
    if order_list is not None:
        try:
            assert type(json.loads(order_list)) == list
        except:
            return HttpResponseBadRequest()
    det_req = DetectionRequest(station_id=station_id, search_key=search_key, order_list=order_list)
    det_req.save()
    rq.enqueue(on_submit, det_req)
    return JsonResponse({'detection_id': det_req.id})


def query_det_req(request, id):
    if request.method != 'GET':
        return HttpResponseBadRequest()
    det_req = DetectionRequest.objects.filter(id=id)
    if len(det_req) > 1:
        return HttpResponseServerError()
    if len(det_req) == 0:
        return HttpResponseNotFound()
    det_req = det_req[0]
    return JsonResponse({'detection_id': det_req.id, 'status': det_req.status, 'result': det_req.result})


def clear(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    DetectionRequest.objects.all().delete()
    return HttpResponse('success')


def update_list(request):
    return ...
