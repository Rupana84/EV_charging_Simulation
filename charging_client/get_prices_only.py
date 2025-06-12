# get_prices_only.py
from server_api import get_price_per_hour

def main():
    prices = get_price_per_hour()
    print("Hourly Electricity Prices (öre):")
    for hour, price in enumerate(prices):
        print(f"Hour {hour:02d}: {price:.2f} öre")

if __name__ == "__main__":
    main()