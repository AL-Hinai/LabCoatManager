from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q, Sum
from django.db import IntegrityError
from .models import LabCoatInventory, LabCoatAddStock, LabCoatDistribution
import plotly.graph_objs as go
from plotly.offline import plot
from collections import defaultdict
from datetime import datetime
from itertools import product
import pandas as pd
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from django.db import IntegrityError
from .models import LabCoatDistribution




# Home View
@login_required
def home_view(request):
    return redirect('stock_view')

# login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('home_view'))  # Redirect to the home page after successful login
        else:
            # Invalid login
            return render(request, 'LabCoat/login.html', {'error_message': 'Invalid username or password'})
    else:
        return render(request, 'LabCoat/login.html')

# logout
def logout_view(request):
    logout(request)
    return redirect(reverse('login'))


# stock view
@login_required
def stock_view(request):
    # Fetch all stock additions and distributions
    stock_additions = LabCoatAddStock.objects.order_by('date')
    distributions = LabCoatDistribution.objects.order_by('date')

    # Get all unique sizes and dates
    sizes = set([addition.size for addition in stock_additions]) | set([distribution.size for distribution in distributions])
    dates = sorted(set([addition.date.date() for addition in stock_additions]) | set([distribution.date for distribution in distributions]))

    # Create a defaultdict to store the cumulative inventory for each size
    inventory = defaultdict(lambda: defaultdict(int))

    # Initialize inventory for each size and date
    for size, date in product(sizes, dates):
        inventory[size][date] = 0

    # Populate inventory with stock additions
    for addition in stock_additions:
        inventory[addition.size][addition.date.date()] += addition.quantity

    # Subtract distributions from inventory
    for distribution in distributions:
        inventory[distribution.size][distribution.date] -= distribution.quantity

    # Accumulate inventory changes
    for size in sizes:
        cumulative_quantity = 0
        for date in dates:
            cumulative_quantity += inventory[size][date]
            inventory[size][date] = cumulative_quantity

    # Prepare data for the graph
    graph_data = []
    for size in sizes:
        size_data = [inventory[size][date] for date in dates]
        graph_data.append(go.Scatter(x=dates, y=size_data, mode='lines+markers', name=size))

    # Create the layout for the graph
    layout = go.Layout(
        title='Lab Coat Inventory Over Time',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Total Quantity'),
        showlegend=True
    )

    # Create the figure with data and layout
    figure = go.Figure(data=graph_data, layout=layout)

    # Generate the HTML representation of the plot
    graph_div = plot(figure, output_type='div')

    # Fetch total inventory for each size from LabCoatInventory
    inventory_data = LabCoatInventory.objects.all()

    # Prepare the context with all necessary data
    context = {
        'graph_div': graph_div,
        'inventory_data': inventory_data,
        # Add any other context data needed for your template
    }

    return render(request, 'LabCoat/stock_view.html', context)





# Add Stock View
@login_required
def add_stock_view(request):
    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity'))
        LabCoatAddStock.objects.create(size=size, quantity=quantity)
        return HttpResponseRedirect('/')
    return render(request, 'LabCoat/add_stock.html', {'sizes': LabCoatInventory.SIZE_CHOICES})

# Main View for Distributing Lab Coats
def distribute_lab_coat(request):
    sizes = LabCoatInventory.objects.values('size').distinct()

    if request.method == 'POST':
        size = request.POST.get('size')
        recipient_type = request.POST.get('recipient_type')
        quantity = int(request.POST.get('quantity', 0))
        distribution_date = request.POST.get('distribution_date', datetime.today().strftime('%Y-%m-%d'))

        # Convert the distribution date from string to datetime.date object
        try:
            distribution_date = datetime.strptime(distribution_date, '%Y-%m-%d').date()
        except ValueError:
            distribution_date = datetime.today().date()

        user_id = request.POST.get('user_id', '')
        name = request.POST.get('name', '')

        LabCoatDistribution.objects.create(
            size=size,
            recipient_type=recipient_type,
            quantity=quantity,
            user_id=user_id,
            name=name,
            date=distribution_date  # Use the provided or default date
        )
        return HttpResponseRedirect('/')

    return render(request, 'LabCoat/distribute_lab_coat.html', {'sizes': sizes})

# View for Students Distribute
@login_required
def student_distributions_view(request):
    query = request.GET.get('search', '')
    distributions = LabCoatDistribution.objects.filter(recipient_type='student').filter(
        Q(user_id__icontains=query) | Q(name__icontains=query)
    )
    return render(request, 'LabCoat/student_distributions.html', {'distributions': distributions, 'query': query})

# View for Staff Distribute
@login_required
def staff_distributions_view(request):
    query = request.GET.get('search', '')
    distributions = LabCoatDistribution.objects.filter(recipient_type='staff').filter(
        Q(user_id__icontains=query) | Q(name__icontains=query)
    )
    return render(request, 'LabCoat/staff_distributions.html', {'distributions': distributions, 'query': query})

@login_required
def lab_coat_stock_chart(request):
    # Retrieve data from LabCoatAddStock and LabCoatDistribution models
    add_stock_data = LabCoatAddStock.objects.values('size').annotate(total_quantity=Sum('quantity'))
    distribution_data = LabCoatDistribution.objects.values('size').annotate(total_quantity=Sum('quantity'))

    # Prepare data for the line chart
    chart_data = {
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
    for size in chart_data['sizes']:
        # Retrieve total add stock quantity for the size
        add_stock_quantity = add_stock_data.filter(size=size).values('total_quantity').first()
        add_stock_quantity = add_stock_quantity['total_quantity'] if add_stock_quantity else 0

        # Retrieve total distribution quantity for the size
        distribution_quantity = distribution_data.filter(size=size).values('total_quantity').first()
        distribution_quantity = distribution_quantity['total_quantity'] if distribution_quantity else 0

        # Calculate total inventory quantity
        total_quantity = add_stock_quantity - distribution_quantity

        chart_data['data'][size].append(total_quantity)

    return render(request, 'LabCoat/lab_coat_stock_chart.html', {'chart_data': chart_data})



@login_required
@login_required
def upload_excel_distribution(request):
    if request.method == 'POST' and request.FILES:
        excel_file = request.FILES['excel_file']

        try:
            # Read the Excel file
            df = pd.read_excel(excel_file, engine='openpyxl')

            # Process each row
            for _, row in df.iterrows():
                user_id = row['user_id']
                name = row['name']
                size = row['size']
                recipient_type = row['recipient_type']
                quantity = int(row['quantity'])
                date = pd.to_datetime(row['date']).date()

                try:
                    # Attempt to get the LabCoatDistribution object using the unique criteria
                    distribution_obj, created = LabCoatDistribution.objects.get_or_create(
                        user_id=user_id,
                        size=size,
                        date=date,
                        defaults={
                            'name': name,
                            'recipient_type': recipient_type,
                            'quantity': quantity
                        }
                    )

                    # Check if the object was created or already existed
                    if created:
                        # Object was created, handle updates to inventory or other actions here
                        pass
                    else:
                        # Object already existed, handle any updates or other logic here
                        pass
                except IntegrityError as e:
                    # Handle any database integrity errors, such as duplicate entries
                    pass

            # If no error, return success message along with rendering the template
            success_message = "Excel file processed successfully"
            return render(request, 'LabCoat/upload_excel_distribution.html', {'success_message': success_message})
        
        except Exception as e:
            # If an error occurs during processing, return error message along with rendering the template
            error_message = f'Error: {e}'
            return render(request, 'LabCoat/upload_excel_distribution.html', {'error_message': error_message})

    # Render the template for GET requests
    return render(request, 'LabCoat/upload_excel_distribution.html')

