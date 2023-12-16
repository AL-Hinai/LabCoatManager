from django.shortcuts import render
from .models import LabCoatInventory, LabCoatAddStock, LabCoatDistribution, InventoryUpdate
from django.http import HttpResponseRedirect
import pytesseract
from django.http import JsonResponse
from django.shortcuts import render
from PIL import Image
import plotly.graph_objs as go
from django.db.models import Q
import re

# Home View
def home_view(request):
    return render(request, 'LabCoat/home.html')

# Stock View
def stock_view(request):
    # Query the LabCoatInventory model to get the current inventory data
    inventory_data = LabCoatInventory.objects.all()

    # Prepare data for the line chart
    chart_data = {
        'timestamps': [],  # Add your timestamps here from Inventoryupdate
        'sizes': ['Small', 'Medium', 'Large', 'Extra Large', 'Extra Extra Large'],
        'data': {
            'Small': [],
            'Medium': [],
            'Large': [],
            'Extra Large': [],
            'Extra Extra Large': [],
        },
    }

    # Fill chart_data with inventory update data
    inventory_updates = InventoryUpdate.objects.all()
    for item in inventory_updates:
        chart_data['timestamps'].append(item.timestamp)
        chart_data['data'][item.get_size_display()].append(item.quantity_update)

    # Create the Plotly line chart
    chart = go.Figure()

    for size in chart_data['sizes']:
        chart.add_trace(go.Scatter(
            x=chart_data['timestamps'],
            y=chart_data['data'][size],
            mode='lines+markers',
            name=size
        ))

    chart.update_layout(
        title='Lab Coat Inventory Over Time',
        xaxis_title='Date',
        yaxis_title='Total Count'
    )

    chart_div = chart.to_html(full_html=False)

    return render(request, 'LabCoat/stock_view.html', {'inventory_data': inventory_data, 'chart_div': chart_div})



# Add Stock View
def add_stock_view(request):
    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity'))
        LabCoatAddStock.objects.create(size=size, quantity=quantity)
        return HttpResponseRedirect('/')
    return render(request, 'LabCoat/add_stock.html', {'sizes': LabCoatInventory.SIZE_CHOICES})





# OCR Helper Functions
def extract_user_id(ocr_text):
    user_id_match = re.search(r'ID:\s*?([\w-]+)', ocr_text)
    return user_id_match.group(1) if user_id_match else None

def extract_name(ocr_text):
    name_match = re.search(r'NAME:\s*?([\w\s-]+)\s*?CLASS', ocr_text)
    return name_match.group(1) if name_match else None

def extract_email(ocr_text):
    user_id = extract_user_id(ocr_text)
    if user_id:
        return f"{user_id}@utas.edu.om"
    else:
        return 'error: email not found'

# OCR Processing API View
def ocr_process_view(request):
    if request.method == 'POST' and request.FILES.get('imageCapture', None):
        image = Image.open(request.FILES['imageCapture'])
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        try:
            ocr_result = pytesseract.image_to_string(image, lang='eng')
        except Exception as e:
            return JsonResponse({'error': 'OCR processing failed', 'details': str(e)}, status=500)



        user_id_pattern = r'ID:\s*?([\w-]+)'
        name_pattern = r'NAME:\s*?([\w\s-]+)\s*?CLASS'

        user_id = re.search(user_id_pattern, ocr_result)
        name = re.search(name_pattern, ocr_result)

        # Construct the email from the user_id
        email = f"{user_id.group(1)}@utas.edu.om" if user_id else 'error: email not found'

        response_data = {
            'ocr_result': ocr_result,
            'user_id': user_id.group(1) if user_id else 'error: user ID not found',
            'name': name.group(1) if name else 'error: name not found',
            'email': email
        }
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)

# Main View for Distributing Lab Coats
def distribute_lab_coat(request):
    sizes = LabCoatInventory.objects.values('size').distinct()

    if request.method == 'POST':
        size = request.POST.get('size')
        recipient_type = request.POST.get('recipient_type')
        quantity = int(request.POST.get('quantity'))

        if request.FILES.get('imageCapture'):
            img = Image.open(request.FILES['imageCapture'])
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            ocr_result = pytesseract.image_to_string(img, lang='eng')

            user_id = extract_user_id(ocr_result)
            name = extract_name(ocr_result)
            email = extract_email(ocr_result)
        else:
            user_id = request.POST.get('user_id')
            name = request.POST.get('name')
            email = request.POST.get('email')

        LabCoatDistribution.objects.create(size=size, recipient_type=recipient_type, quantity=quantity, user_id=user_id, name=name, email=email)
        return HttpResponseRedirect('/')

    return render(request, 'LabCoat/distribute_lab_coat.html', {'sizes': sizes})









# View for Students Distribute
def student_distributions_view(request):
    query = request.GET.get('search', '')
    distributions = LabCoatDistribution.objects.filter(recipient_type='student').filter(
        Q(user_id__icontains=query) | Q(name__icontains=query)
    )
    return render(request, 'LabCoat/student_distributions.html', {'distributions': distributions, 'query': query})

# View for Staff Distribute
def staff_distributions_view(request):
    query = request.GET.get('search', '')
    distributions = LabCoatDistribution.objects.filter(recipient_type='staff').filter(
        Q(user_id__icontains=query) | Q(name__icontains=query)
    )
    return render(request, 'LabCoat/staff_distributions.html', {'distributions': distributions, 'query': query})

def lab_coat_stock_chart(request):
    # Retrieve data from LabCoatInventory model
    inventory_data = LabCoatInventory.objects.all()
    
    # Prepare data for the line chart
    chart_data = {
        'timestamps': [],  # Add your timestamps here
        'sizes': ['Small', 'Medium', 'Large', 'Extra Large', 'Extra Extra Large'],
        'data': {
            'Small': [],
            'Medium': [],
            'Large': [],
            'Extra Large': [],
            'Extra Extra Large': [],
        },
    }
    
    # Fill chart_data with inventory data
    for item in inventory_data:
        chart_data['timestamps'].append(item.date)  # Add your timestamp field
        chart_data['data'][item.get_size_display()].append(item.total)
    
    return render(request, 'labcoat/lab_coat_stock_chart.html', {'chart_data': chart_data})