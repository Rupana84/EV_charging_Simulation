# get_baseload_only.py
from server_api import get_baseload

def main():
    loads = get_baseload()
    print("Hourly Base Load (kW):")
    for hour, load in enumerate(loads):
        print(f"Hour {hour:02d}: {load:.2f} kW")

if __name__ == "__main__":
    main()