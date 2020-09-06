from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import FileUploadParser

from app.models import DataStore
from django.db import IntegrityError

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings

from threading import Thread
from app.upload_worker import UploadTask
from app.download_worker import DownloadTask

import os

global upload_task
global download_task

STATE_RESPONSES = {
    0: 'Uploading/Downloading...',
    1: 'Ready to Start!',
    2: 'Paused!',
    3: 'Stopped!'
}


class FileUploadView(APIView):
    """
        Accept file input
    """
    permission_classes = (IsAuthenticated,)
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        file_obj = request.FILES['file']
        dataStore = DataStore(owner=request.user)
        try:
            dataStore.csv = file_obj
            dataStore.save()
        except IntegrityError as e:
            return Response({'error': 'File already exists!'}, status=400)
        
        
        return Response({'message': f'{file_obj.name} successfully uploaded!', 'file_id': f'{dataStore.id}'}, status=201)


class StartUploadTask(APIView):
    """
        Endpoint to Start long running translation process of inserting csv row into database
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        f = get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global upload_task
        upload_task = UploadTask(request.user, f.id)

        thread = Thread(upload_task.csv_to_db())
        thread.start()

        return Response({'message': STATE_RESPONSES[upload_task.get_state()]}, status=200)


class UploadTaskState(APIView):
    """
        Check the state of long running process long with progress (0-100%)
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global upload_task

        return Response(
            {
                'message': STATE_RESPONSES[upload_task.get_state()],
                'progress': upload_task.get_progress()
            }, status=200)


class PauseUploadTask(APIView):
    """
        Pauses the execution of csv to database long running process
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global upload_task
        upload_task.pause()

        return Response({'message': STATE_RESPONSES[upload_task.get_state()]}, status=200)


class ResumeUploadTask(APIView):
    """
        Resume the execution of csv to database long running process from it's last state
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global upload_task
        upload_task.resume()
        
        return Response({'message': STATE_RESPONSES[upload_task.get_state()]}, status=200)


class StopUploadTask(APIView):
    """
        Terminate the execution of csv to database long running process. Note: All insertions which were not commited will be rolled back
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global upload_task
        upload_task.stop()
        
        return Response({'message': STATE_RESPONSES[upload_task.get_state()]}, status=200)


class StartDownloadTask(APIView):
    """
        Endpoint to Start long running translation process of converting database record to csv file. Query parameters are optional! Note: export.csv file will be downloaded containing data only if all the records were processed
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        file_id = request.GET.get("id")
        from_year = request.GET.get("from_year")

        file_id = toInt(file_id)
        from_year = toInt(from_year)

        global download_task
        download_task = DownloadTask(request.user, file_id, from_year)
        
        thread = Thread(download_task.db_to_csv())
        thread.start()

        if download_task.get_progress() == 100:
            try:
                data = open(f'{settings.BASE_DIR}{settings.MEDIA_URL}{request.user.username}_export_game_sale.csv','r').read()
            except FileNotFoundError:
                return Response({'error': 'Something went wrong!'}, status=500)        
            
            # force download.
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment;filename=export.csv'
            return response
        
        else:
            return Response({'message': STATE_RESPONSES[download_task.get_state()]}, status=200)


class DownloadTaskState(APIView):
    """
        Check the state of long running process long with progress (0-100%)
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        global download_task

        return Response(
            {
                'message': STATE_RESPONSES[download_task.get_state()],
                'progress': download_task.get_progress()
            }, status=200)


class PauseDownloadTask(APIView):
    """
    Pauses the execution of database to csv long running process
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        global download_task
        download_task.pause()

        return Response({'message': STATE_RESPONSES[download_task.get_state()]}, status=200)


class ResumeDownloadTask(APIView):
    """
        Resume the execution of database to csv long running process from it's last state. Note: export.csv file will be downloaded containing data only if all the records were processed.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        global download_task
        download_task.resume()
        
        if download_task.get_progress() == 100:
            try:
                data = open(f'{settings.BASE_DIR}{settings.MEDIA_URL}{request.user.username}_export_game_sale.csv','r').read()
            except FileNotFoundError:
                return Response({'error': 'Something went wrong!'}, status=500)
            
            # force download.
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment;filename=export.csv'
            return response
        
        else:
            return Response({'message': STATE_RESPONSES[download_task.get_state()]}, status=200)


class StopDownloadTask(APIView):
    """
        Terminate the execution of database to csv long running process. Note: export.csv file will be downloaded containing records that were processed.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            data = open(f'{settings.BASE_DIR}{settings.MEDIA_URL}{request.user.username}_export_game_sale.csv','r').read()
        except FileNotFoundError:
            return Response({'error': 'Something went wrong!'}, status=500)
        
        global download_task
        download_task.stop()

        # force download.
        response = HttpResponse(data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment;filename=export.csv'
        return response


def toInt(value):
    """
        Helper method to convert type to int
    """
    try:
        value = int(value)
        return value
    except (ValueError, TypeError):
        return None
