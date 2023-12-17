from django.shortcuts import render
import requests
from .models import LabCoatInventory, LabCoatAddStock, LabCoatDistribution, InventoryUpdate
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from PIL import Image
import plotly.graph_objs as go
from django.db.models import Q
import re
from plotly.offline import plot
from collections import defaultdict



# Home View
def home_view(request):
    return render(request, 'LabCoat/home.html')

# Stock View
def stock_view(request):
    # Prepare data for the graph
    updates_data = defaultdict(list)

    # Get all inventory updates ordered by timestamp
    inventory_updates = InventoryUpdate.objects.all().order_by('timestamp')

    for update in inventory_updates:
        # Append the update quantity and timestamp to updates_data
        updates_data[update.size].append((update.timestamp, update.quantity_update))

    # Create traces for the graph, one for each size
    graph_data = []
    for size, updates in updates_data.items():
        timestamps, quantities = zip(*updates) if updates else ([], [])
        size_display = dict(InventoryUpdate.SIZE_CHOICES)[size]
        graph_data.append(go.Scatter(
            x=timestamps,
            y=quantities,
            mode='lines+markers',
            name=size_display
        ))

    # Create the layout for the graph
    layout = go.Layout(
        title='Lab Coat Inventory Updates Over Time',
        xaxis=dict(title='Timestamp'),
        yaxis=dict(title='Quantity Updated'),
        showlegend=True
    )

    # Create the figure with data and layout
    figure = go.Figure(data=graph_data, layout=layout)

    # Generate the HTML representation of the plot
    graph_div = plot(figure, output_type='div')

    # Initialize current stock from LabCoatInventory
    current_stock = {}
    for inventory in LabCoatInventory.objects.all():
        size_display = inventory.get_size_display()  # Get the human-readable size name
        current_stock[size_display] = inventory.total

    # Pass both the graph and current stock data to the template
    return render(request, 'LabCoat/stock_view.html', {
        'graph_div': graph_div,
        'current_stock': current_stock
    })


# Add Stock View
def add_stock_view(request):
    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity'))
        LabCoatAddStock.objects.create(size=size, quantity=quantity)
        return HttpResponseRedirect('/')
    return render(request, 'LabCoat/add_stock.html', {'sizes': LabCoatInventory.SIZE_CHOICES})





# Replace with your OCR.space API key
OCR_SPACE_API_KEY = "K89352752688957"

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
        image = request.FILES['imageCapture']

        # Set up the OCR.space API endpoint URL
        ocr_space_url = "https://api.ocr.space/parse/image"

        # Define OCR.space API parameters
        payload = {
            "apikey": OCR_SPACE_API_KEY,
            "language": "eng",  # Language code for English
            "isOverlayRequired": False,  # Disable overlay
        }

        # Send a POST request to OCR.space API with the image
        try:
            response = requests.post(ocr_space_url, files={"image": image}, data=payload)
            response_data = response.json()
        except Exception as e:
            return JsonResponse({'error': 'OCR processing failed', 'details': str(e)}, status=500)

        # Check if OCR processing was successful
        if response_data.get("OCRExitCode") == 1:
            ocr_result = response_data.get("ParsedResults")[0].get("ParsedText")

            # Extract user_id, name, and email using your existing functions
            user_id = extract_user_id(ocr_result)
            name = extract_name(ocr_result)
            email = extract_email(ocr_result)

            response_data = {
                'ocr_result': ocr_result,
                'user_id': user_id if user_id else 'error: user ID not found',
                'name': name if name else 'error: name not found',
                'email': email
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'OCR processing failed'}, status=500)

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

            # Send the image to OCR.space API (same code as in ocr_process_view)
            ocr_space_url = "https://api.ocr.space/parse/image"
            payload = {
                "apikey": OCR_SPACE_API_KEY,
                "language": "eng",
                "isOverlayRequired": False,
            }
            try:
                response = requests.post(ocr_space_url, files={"image": img}, data=payload)
                response_data = response.json()
            except Exception as e:
                return JsonResponse({'error': 'OCR processing failed', 'details': str(e)}, status=500)

            if response_data.get("OCRExitCode") == 1:
                ocr_result = response_data.get("ParsedResults")[0].get("ParsedText")

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