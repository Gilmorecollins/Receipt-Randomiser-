import random
from datetime import datetime
import calendar
from collections import defaultdict


class ReceiptGenerator:
    def __init__(self):
        self.min_bags = 8
        self.max_bags = 24
        self.orders_per_month = 2
        self.business_name = "Baba Sandra"
        self.used_totals = defaultdict(int)
        self.previous_total = None

    def get_product_details(self, min_total):
        """Get multiple products with dynamic price validation."""
        products = []
        print("\nProduct Information")
        print("-------------------")

        num_products = 0
        while num_products < 1:
            try:
                num_products = int(input("How many different products are being supplied? "))
                if num_products < 1:
                    print("Must supply at least 1 product")
            except ValueError:
                print("Please enter a valid number!")

        for i in range(1, num_products + 1):
            print(f"\nProduct #{i}")
            name = input("Enter product name: ").strip()
            while not name:
                print("Product name cannot be empty!")
                name = input("Enter product name: ").strip()

            while True:
                try:
                    price = float(input(f"Enter price per unit of {name}: "))
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

    def get_date_range(self):
        """Get start and end date from user input."""
        print("\nDate Range Selection")
        print("--------------------")
        while True:
            try:
                start_month = int(input("Enter start month (1-12): "))
                start_year = int(input("Enter start year (e.g., 2024): "))
                end_month = int(input("Enter end month (1-12): "))
                end_year = int(input("Enter end year (e.g., 2025): "))

                if not 1 <= start_month <= 12 or not 1 <= end_month <= 12:
                    raise ValueError("Month must be between 1 and 12")

                start_date = datetime(start_year, start_month, 1)
                end_date = datetime(end_year, end_month, calendar.monthrange(end_year, end_month)[1])

                if start_date > end_date:
                    raise ValueError("Start date must be before end date")

                return start_date, end_date

            except ValueError as e:
                print(f"Invalid input: {e}. Please try again.\n")

    def get_total_range(self):
        """Get the desired monthly total range from user."""
        print("\nMonthly Total Range")
        print("-------------------")
        while True:
            try:
                min_total = float(input("Enter minimum monthly total amount: "))
                max_total = float(input("Enter maximum monthly total amount: "))

                if min_total <= 0 or max_total <= 0:
                    print("Amounts must be positive!")
                elif min_total > max_total:
                    print("Minimum must be less than maximum!")
                else:
                    return min_total, max_total

            except ValueError:
                print("Please enter valid numbers!")

    def generate_quantities(self, products, min_total, max_total):
        """Generate quantities for multiple products with tiered fallback."""
        max_attempts = 500
        constraints = [
            {'desc': "strict", 'allow_dup_totals': False, 'range_buffer': 0},
            {'desc': "relaxed duplicates", 'allow_dup_totals': True, 'range_buffer': 0},
            {'desc': "extended range", 'allow_dup_totals': True, 'range_buffer': 5000}
        ]

        for constraint in constraints:
            for _ in range(max_attempts):
                quantities = {}
                monthly_total = 0

                # Generate quantities for each product
                for product in products:
                    qty1 = random.randint(self.min_bags, self.max_bags)
                    qty2 = random.randint(self.min_bags, self.max_bags)
                    while qty2 * product['price'] == qty1 * product['price']:
                        qty2 = random.randint(self.min_bags, self.max_bags)

                    quantities[product['name']] = [qty1, qty2]
                    monthly_total += (qty1 + qty2) * product['price']

                # Check conditions
                valid = (min_total <= monthly_total <= max_total + constraint['range_buffer'])
                if not constraint['allow_dup_totals']:
                    valid = valid and (self.previous_total is None or monthly_total != self.previous_total)
                    valid = valid and (self.used_totals[monthly_total] < 2)

                if valid:
                    self.used_totals[monthly_total] += 1
                    self.previous_total = monthly_total
                    return quantities, monthly_total

        # Fallback - mathematical distribution
        target_total = random.randint(int(min_total), int(max_total))
        remaining_total = target_total
        quantities = {}

        # First pass - assign minimum quantities
        for product in products:
            qty1 = self.min_bags
            qty2 = self.min_bags
            quantities[product['name']] = [qty1, qty2]
            remaining_total -= (qty1 + qty2) * product['price']

        # Second pass - distribute remaining amount
        for product in products:
            if remaining_total <= 0:
                break

            max_possible = (self.max_bags - self.min_bags) * 2 * product['price']
            allocate = min(remaining_total, max_possible)
            additional_bags = int(allocate // product['price'])

            if additional_bags > 0:
                qty1_add = random.randint(0, min(additional_bags, self.max_bags - self.min_bags))
                qty2_add = additional_bags - qty1_add

                quantities[product['name']][0] += qty1_add
                quantities[product['name']][1] += qty2_add
                remaining_total -= (qty1_add + qty2_add) * product['price']

        # Ensure no identical order amounts
        for product in products:
            if quantities[product['name']][0] * product['price'] == quantities[product['name']][1] * product['price']:
                if quantities[product['name']][0] > self.min_bags:
                    quantities[product['name']][0] -= 1
                    quantities[product['name']][1] += 1
                else:
                    quantities[product['name']][0] += 1
                    quantities[product['name']][1] -= 1

        monthly_total = target_total - remaining_total
        self.used_totals[monthly_total] += 1
        self.previous_total = monthly_total
        return quantities, monthly_total

    def generate_dates_for_month(self, year, month):
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

    def generate_receipts(self, products, start_date, end_date, min_total, max_total):
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

    def save_to_file(self, content, start_date, end_date, product_names):
        """Save generated receipts to a file."""
        filename = (f"Receipt_orders_{self.business_name}_{product_names}_"
                    f"{start_date.month}_{start_date.year}_to_"
                    f"{end_date.month}_{end_date.year}.txt")

        with open(filename, 'w') as f:
            f.write(content)
        print(f"\nReceipts saved to '{filename}'")

    def run(self):
        """Main program flow for multiple products."""
        print(f"\n{self.business_name} Receipt Order Generator")
        print("-----------------------------------\n")

        # Get constraints first
        start_date, end_date = self.get_date_range()
        min_total, max_total = self.get_total_range()

        # Get product details with proper min_total
        products = self.get_product_details(min_total)

        # Generate receipts
        receipts = self.generate_receipts(products, start_date, end_date, min_total, max_total)

        # Display and save results
        print("\nGenerated Receipts (first month):\n")
        print(receipts.split("------------------------------------------------------------------------")[1])

        if input("\nSave all results to file? (y/n): ").lower() == 'y':
            product_names = "_".join(p['name'] for p in products)
            self.save_to_file(receipts, start_date, end_date, product_names)
            print("\nGeneration complete!")


if __name__ == "__main__":
    generator = ReceiptGenerator()
    generator.run()
