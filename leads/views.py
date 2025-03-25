from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Lead
from .forms import LeadForm, UserLoginForm
import pandas as pd
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
from django.utils import timezone
from datetime import datetime
from django.contrib import messages
import pytz
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

# User login view
def login_view(request):
    form = UserLoginForm(data=request.POST or None)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('master_dashboard' if user.is_superuser else 'index')
    return render(request, 'login.html', {'form': form})

# View to manage leads data
def index(request):
    success_message = None
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = 'Data added successfully!'

            excel_path = os.path.join(settings.MEDIA_ROOT, 'excel_files', 'Demo_data_interns.xlsx')
            try:
                excel_data_df = pd.read_excel(excel_path)
            except FileNotFoundError:
                excel_data_df = pd.DataFrame()

            new_data = pd.DataFrame([{
                'Name': form.cleaned_data['name'],
                'Number': form.cleaned_data['number'],
                'Database': form.cleaned_data['database'],
                'demo lecture attended?': form.cleaned_data['demo_lecture_attended'],
                'interested in': form.cleaned_data['interested_in'],
                'last Whatsapp blast': form.cleaned_data['last_whatsapp_blast'].replace(tzinfo=None) if form.cleaned_data['last_whatsapp_blast'] else None,
                'response to whatsappblast': form.cleaned_data['response_to_whatsapp_blast'],
                'last call date': form.cleaned_data['last_call_date'],
                'Followup of last call': form.cleaned_data['followup_of_last_call'],
                'Close Reason': form.cleaned_data['close_reason'],
            }])

            updated_data = pd.concat([excel_data_df, new_data], ignore_index=True)
            updated_data.to_excel(excel_path, index=False)
            form = LeadForm()
    else:
        form = LeadForm()

    return render(request, 'index.html', {'form': form, 'success_message': success_message})

# Show the leads data, with filtering and pagination
def leads_data(request):
    local_tz = pytz.timezone('Asia/Kolkata')
    current_time = timezone.now()
    local_time = current_time.astimezone(local_tz)
    today = local_time.date()

    if request.method == 'POST' and 'complete_call' in request.POST:
        lead_id = request.POST.get('lead_id')
        try:
            lead = Lead.objects.get(id=lead_id)
            lead.call_made = True
            lead.last_call_date = today
            lead.followup_of_last_call = today + timezone.timedelta(days=7)
            lead.save()
            print(f"Lead {lead_id} marked as completed.")
        except Lead.DoesNotExist:
            print(f"Lead {lead_id} does not exist.")
        return redirect('leads_data')

    leads_due_today = Lead.objects.filter(followup_of_last_call=today, call_made=False)
    completed_calls_today = Lead.objects.filter(last_call_date=today, call_made=True)

    print(f"Today's Date: {today}")
    print(f"Leads Due Today: {leads_due_today.count()} leads")
    print(f"Completed Calls Today: {completed_calls_today.count()} leads")

    query = request.GET.get('q', '')
    if query:
        all_leads = Lead.objects.filter(
            Q(name__icontains=query) |
            Q(number__icontains=query) |
            Q(interested_in__icontains=query) |
            Q(last_call_date__icontains=query) |
            Q(database=query) |
            Q(followup_of_last_call__icontains=query)
        )
    else:
        all_leads = Lead.objects.all()

    paginator = Paginator(all_leads, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'leads_data.html', {
        'leads_due_today': leads_due_today,
        'completed_calls_today': completed_calls_today,
        'page_obj': page_obj,
        'query': query,
    })

# Master dashboard with employee list
@login_required
def master_dashboard(request):
    employees = User.objects.filter(is_superuser=False)
    return render(request, 'master_dashboard.html', {'employees': employees})

# Updated Excel data view with upload, display, and delete
def excel_data(request):
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'excel_files')
    os.makedirs(upload_dir, exist_ok=True)

    # Handle file upload
    if request.method == 'POST' and 'upload' in request.POST:
        uploaded_file = request.FILES.get('excel_file')
        if uploaded_file:
            fs = FileSystemStorage(location=upload_dir)
            for old_file in os.listdir(upload_dir):
                os.remove(os.path.join(upload_dir, old_file))
            filename = fs.save(uploaded_file.name, uploaded_file)
            messages.success(request, 'Excel file uploaded successfully!')
        else:
            messages.error(request, 'No file selected. Please choose an Excel file to upload.')

    # Handle file deletion
    if request.method == 'POST' and 'delete' in request.POST:
        excel_files = [f for f in os.listdir(upload_dir) if f.endswith(('.xlsx', '.xls'))]
        if excel_files:
            for file in excel_files:
                os.remove(os.path.join(upload_dir, file))
            messages.success(request, 'Excel file deleted successfully!')
        else:
            messages.error(request, 'No Excel file to delete.')

    # Read the latest Excel file
    excel_files = [f for f in os.listdir(upload_dir) if f.endswith(('.xlsx', '.xls'))]
    excel_data_df = pd.DataFrame()
    if excel_files:
        latest_file_path = os.path.join(upload_dir, excel_files[0])
        try:
            excel_data_df = pd.read_excel(latest_file_path, engine='openpyxl')
            excel_data_df.fillna('N/A', inplace=True)
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {str(e)}")

    # Search functionality
    query = request.GET.get('q', '')
    if query and not excel_data_df.empty:
        excel_data_df = excel_data_df[excel_data_df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]

    excel_data = excel_data_df.to_dict(orient='records')
    paginator = Paginator(excel_data, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'excel_data.html', context)

# Toggle interest status for a lead
def toggle_interest(request, lead_id):
    if request.method == 'POST':
        lead = get_object_or_404(Lead, id=lead_id)
        lead.interested = not lead.interested
        lead.save()
        return JsonResponse({'interested': lead.interested})

@login_required
def alerts_view(request):
    today = datetime.now().date()
    alerts = Lead.objects.filter(last_call_date=today)
    return render(request, 'alerts.html', {'alerts': alerts})

# View for managing call alerts and reminders
def alert_leads(request):
    today = datetime.now().date()
    leads_due_for_call = Lead.objects.filter(followup_of_last_call=today)
    calls_made = leads_due_for_call.filter(call_made=True)
    calls_pending = leads_due_for_call.filter(call_made=False)

    if request.method == 'POST':
        lead_id = request.POST.get('lead_id')
        lead = Lead.objects.get(id=lead_id)
        lead.call_made = True
        lead.save()
        return redirect('alerts')

    return render(request, 'alerts.html', {
        'calls_made': calls_made,
        'calls_pending': calls_pending,
        'total_calls': leads_due_for_call.count(),
        'calls_completed': calls_made.count(),
        'calls_remaining': calls_pending.count(),
    })