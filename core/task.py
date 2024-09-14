# your_app/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import *

@shared_task
def delete_old_orders():
    seven_days_ago = timezone.now() - timedelta(days=7)

    old_orders = Order.objects.filter(
        is_shipped=True, order_date__lte=seven_days_ago
    ) | Order.objects.filter(
        is_cancel=True, order_date__lte=seven_days_ago
    )

    count, _ = old_orders.delete()
    return f"{count} orders deleted."


@shared_task
def delete_info():
    company = Company.objects.first()  # Assuming there's only one company

    if company:
            # Add the current month's profit to the total profit
        company.total_profit += company.profit

            # Reset profit, cost, and waste
        company.profit = 0
        company.cost = 0
        company.waste = 0

            # Save the company data
        company.save()


        # Reset vendor (Profile) profits
    vendors = Profile.objects.filter(role='vendor')

    for vendor in vendors:
            # Add the current month's profit to the total_profit
        vendor.total_profit += vendor.profit

            # Reset the vendor's monthly profit
        vendor.profit = 0

            # Save the vendor data
        vendor.save()

