import os
import pandas as pd

def main():
    url = "https://raw.githubusercontent.com/cbergmeir/numerical_time_series_data/master/data/NormalDistribution.txt"
    output_path = "data/raw/series.csv"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Downloading data from {url}...")
    try:
        # Read the raw text file, likely whitespace-separated
        # header=None ensures we don't treat the first row as header
        df = pd.read_csv(url, sep=r'\s+', header=None)
        df.to_csv(output_path, index=False, header=False)
        print(f"Data saved to {output_path}")
        print(f"Shape: {df.shape}")
    except Exception as e:
        print(f"Error downloading: {e}")
        raise

if __name__ == "__main__":
    main()
