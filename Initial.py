import random
from datetime import datetime
import calendar
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import unittest
from unittest.mock import patch
import io
import sys


class ReceiptGenerator:
    def __init__(self, min_bags: int = 8, max_bags: int = 24, orders_per_month: int = 2):
        """Initialize with configurable parameters for testing."""
        self.min_bags = min_bags
        self.max_bags = max_bags
        self.orders_per_month = orders_per_month
        self.business_name = "Receipt Randomiser"
        self.used_totals = defaultdict(int)
        self.previous_total: Optional[float] = None

    def get_product_details(self, min_total: float, input_func=input) -> List[Dict]:
        """Get multiple products with dynamic price validation."""
        products = []
        print("\nProduct Information")
        print("-------------------")

        num_products = 0
        while num_products < 1:
            try:
                num_products = int(input_func("How many different products are being supplied? "))
                if num_products < 1:
                    print("Must supply at least 1 product")
            except ValueError:
                print("Please enter a valid number!")

        for i in range(1, num_products + 1):
            print(f"\nProduct #{i}")
            name = input_func("Enter product name: ").strip()
            while not name:
                print("Product name cannot be empty!")
                name = input_func("Enter product name: ").strip()

            while True:
                try:
                    price = float(input_func(f"Enter price per unit of {name}: "))
                    min_sensible_price = max(10, min_total / (self.max_bags * self.orders_per_month * 3))

                    if price <= 0:
                        print("Price must be greater than 0!")
                    elif price < min_sensible_price:
                        print(f"Price too small - should be at least {min_sensible_price:.2f} based on your total range")
                    else:
                        products.append({'name': name, 'price': price})
                        break
                except ValueError:
                    print("Please enter a valid number!")

        return products

    def get_date_range(self, input_func=input) -> Tuple[datetime, datetime]:
        """Get start and end date from user input."""
        print("\nDate Range Selection")
        print("--------------------")
        while True:
            try:
                start_month = int(input_func("Enter start month (1-12): "))
                start_year = int(input_func("Enter start year (e.g., 2024): "))
                end_month = int(input_func("Enter end month (1-12): "))
                end_year = int(input_func("Enter end year (e.g., 2025): "))

                if not 1 <= start_month <= 12 or not 1 <= end_month <= 12:
                    raise ValueError("Month must be between 1 and 12")

                start_date = datetime(start_year, start_month, 1)
                end_date = datetime(end_year, end_month, calendar.monthrange(end_year, end_month)[1])

                if start_date > end_date:
                    raise ValueError("Start date must be before end date")

                return start_date, end_date

            except ValueError as e:
                print(f"Invalid input: {e}. Please try again.\n")

    def get_total_range(self, input_func=input) -> Tuple[float, float]:
        """Get the desired monthly total range from user."""
        print("\nMonthly Total Range")
        print("-------------------")
        while True:
            try:
                min_total = float(input_func("Enter minimum monthly total amount: "))
                max_total = float(input_func("Enter maximum monthly total amount: "))

                if min_total <= 0 or max_total <= 0:
                    print("Amounts must be positive!")
                elif min_total > max_total:
                    print("Minimum must be less than maximum!")
                else:
                    return min_total, max_total

            except ValueError:
                print("Please enter valid numbers!")

    def generate_quantities(self, products: List[Dict], min_total: float, max_total: float) -> Tuple[Dict, float]:
        """Generate quantities for multiple products with strict total enforcement."""
        max_attempts = 500
        constraints = [
            {'desc': "strict", 'allow_dup_totals': False, 'range_buffer': 0},
            {'desc': "relaxed duplicates", 'allow_dup_totals': True, 'range_buffer': 0}
        ]

        for constraint in constraints:
            for _ in range(max_attempts):
                quantities = {}
                monthly_total = 0.0

                # Generate quantities for each product
                for product in products:
                    qty1 = random.randint(1, self.max_bags)  # Start from 1 instead of min_bags
                    qty2 = random.randint(1, self.max_bags)
                    while qty2 * product['price'] == qty1 * product['price']:
                        qty2 = random.randint(1, self.max_bags)

                    quantities[product['name']] = [qty1, qty2]
                    monthly_total += (qty1 + qty2) * product['price']

                # Strictly enforce total range
                valid = (min_total <= monthly_total <= max_total)
                if not constraint['allow_dup_totals']:
                    valid = valid and (self.previous_total is None or monthly_total != self.previous_total)
                    valid = valid and (self.used_totals[monthly_total] < 2)

                if valid:
                    self.used_totals[monthly_total] += 1
                    self.previous_total = monthly_total
                    return quantities, monthly_total

        # Fallback - mathematical distribution with strict enforcement
        target_total = random.uniform(min_total, max_total)
        remaining_total = target_total
        quantities = {}

        # First pass - assign at least 1 bag per product per order
        for product in products:
            qty1 = 1
            qty2 = 1
            quantities[product['name']] = [qty1, qty2]
            remaining_total -= (qty1 + qty2) * product['price']

        # Second pass - distribute remaining amount with strict limits
        products_shuffled = random.sample(products, len(products))  # Randomize distribution order
        for product in products_shuffled:
            if remaining_total <= 0:
                break

            max_possible = (self.max_bags - quantities[product['name']][0]) * product['price']
            max_possible += (self.max_bags - quantities[product['name']][1]) * product['price']
            allocate = min(remaining_total, max_possible)
            additional_bags = int(allocate // product['price'])

            if additional_bags > 0:
                max_qty1_add = self.max_bags - quantities[product['name']][0]
                qty1_add = random.randint(0, min(additional_bags, max_qty1_add))
                qty2_add = min(additional_bags - qty1_add, self.max_bags - quantities[product['name']][1])

                quantities[product['name']][0] += qty1_add
                quantities[product['name']][1] += qty2_add
                remaining_total -= (qty1_add + qty2_add) * product['price']

        # Ensure no identical order amounts
        for product in products:
            if quantities[product['name']][0] * product['price'] == quantities[product['name']][1] * product['price']:
                if quantities[product['name']][0] > 1:
                    quantities[product['name']][0] -= 1
                    quantities[product['name']][1] += 1
                else:
                    quantities[product['name']][0] += 1
                    quantities[product['name']][1] -= 1

        monthly_total = target_total - remaining_total
        self.used_totals[monthly_total] += 1
        self.previous_total = monthly_total
        return quantities, monthly_total

    def generate_dates_for_month(self, year: int, month: int) -> List[int]:
        """Generate random dates for a given month, avoiding weekends."""
        last_day = calendar.monthrange(year, month)[1]
        dates = []

        for i in range(self.orders_per_month):
            segment_start = 1 + i * (last_day // self.orders_per_month)
            segment_end = (i + 1) * (last_day // self.orders_per_month) if i != self.orders_per_month - 1 else last_day

            for _ in range(100):
                day = random.randint(segment_start, segment_end)
                if datetime(year, month, day).weekday() < 5:
                    dates.append(day)
                    break
            else:
                dates.append(random.randint(segment_start, segment_end))

        return sorted(dates)

    def generate_receipts(self, products: List[Dict], start_date: datetime, 
                         end_date: datetime, min_total: float, max_total: float) -> str:
        """Generate receipts for multiple products."""
        current_date = start_date
        output = []

        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            month_name = current_date.strftime("%B").upper()

            dates = self.generate_dates_for_month(year, month)
            quantities, monthly_total = self.generate_quantities(products, min_total, max_total)

            output.append(f"------------------------------------------------------------------------\n")
            output.append(f"**{month_name} {year}**\n\n")

            for i in range(self.orders_per_month):
                output.append(f"Date Issued: {dates[i]:02d}/{month:02d}/{year}\n")
                for product in products:
                    qty = quantities[product['name']][i]
                    amount = qty * product['price']
                    output.append(f"{product['name']}: {qty} bags @ {product['price']:,.0f} = KES {amount:,.0f}\n")
                output.append("\n")

            output.append(f"**Total for {month_name} {year}: KES {monthly_total:,.0f}**\n\n")

            if month == 12:
                current_date = datetime(year + 1, 1, 1)
            else:
                current_date = datetime(year, month + 1, 1)

        return "".join(output)

    def save_to_file(self, content: str, start_date: datetime, end_date: datetime, 
                    product_names: str, filename: Optional[str] = None) -> str:
        """Save generated receipts to a file."""
        if not filename:
            filename = (f"Receipt_orders_{self.business_name}_{product_names}_"
                        f"{start_date.month}_{start_date.year}_to_"
                        f"{end_date.month}_{end_date.year}.txt")

        with open(filename, 'w') as f:
            f.write(content)
        return filename

    def run(self, input_func=input):
        """Main program flow for multiple products."""
        print(f"\n{self.business_name} Receipt Order Generator")
        print("-----------------------------------\n")

        # Get constraints first
        start_date, end_date = self.get_date_range(input_func)
        min_total, max_total = self.get_total_range(input_func)

        # Get product details with proper min_total
        products = self.get_product_details(min_total, input_func)

        # Generate receipts
        receipts = self.generate_receipts(products, start_date, end_date, min_total, max_total)

        # Display and save results
        print("\nGenerated Receipts (first month):\n")
        print(receipts.split("------------------------------------------------------------------------")[1])

        if input_func("\nSave all results to file? (y/n): ").lower() == 'y':
            product_names = "_".join(p['name'] for p in products)
            filename = self.save_to_file(receipts, start_date, end_date, product_names)
            print(f"\nReceipts saved to '{filename}'")
            print("Generation complete!")


if __name__ == "__main__":
    # Run the tests if executed with 'test' argument
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        unittest.main(argv=['first-arg-is-ignored'])
    else:
        generator = ReceiptGenerator()
        generator.run()