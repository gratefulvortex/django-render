
from django.shortcuts import render, redirect
from .forms import LeadForm
from .models import Lead
import pandas as pd

def index(request):
    success_message = None
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = 'Data added successfully!'
            form = LeadForm()  
    else:
        form = LeadForm()

    return render(request, 'index.html', {'form': form, 'success_message': success_message})


def leads_data(request):
    excel_path = r'C:\Users\windows\OneDrive\Desktop\minproject\Data\Demo_data_interns.xlsx'
    
    # Load the Excel file using pandas
    excel_data_df = pd.read_excel(excel_path)
    
    # Convert NaT values to empty strings or some other safe representation
    for col in excel_data_df.select_dtypes(include=['datetime']).columns:
        excel_data_df[col] = excel_data_df[col].fillna('').astype(str)
    
    # Convert the DataFrame to a list of dictionaries
    excel_data = excel_data_df.to_dict(orient='records')
    
    # Get leads data from the database
    leads = Lead.objects.all()
    
    # Pass both the database leads and Excel data to the template
    return render(request, 'leads_data.html', {'leads': leads, 'excel_data': excel_data})