#!/usr/bin/env python3
"""
Parallel download script for RÚV series
Downloads both Bubbi byggir and Sammi brunavörður X in parallel
"""

import subprocess
import multiprocessing
import time
import os
from test_series import get_all_test_series

def download_series(series_name, series_config):
    """Download a single series"""
    print(f"Starting download of {series_config['series_title']}...")
    
    cmd = [
        'python', 'ruv_improved_scraper.py',
        series_config['url'],
        '--test-folder'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Successfully completed {series_config['series_title']}")
            return True
        else:
            print(f"❌ Failed to download {series_config['series_title']}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error downloading {series_config['series_title']}: {e}")
        return False

def main():
    print("🚀 Starting parallel download of both series...")
    print("=" * 60)
    
    # Get test series configurations
    test_series = get_all_test_series()
    
    # Create processes for each series
    processes = []
    results = {}
    
    for series_name, series_config in test_series.items():
        print(f"📺 Queueing: {series_config['series_title']}")
        process = multiprocessing.Process(
            target=download_series,
            args=(series_name, series_config)
        )
        processes.append((series_name, process))
    
    # Start all processes
    start_time = time.time()
    for series_name, process in processes:
        process.start()
        print(f"▶️  Started: {series_name}")
    
    # Wait for all processes to complete
    for series_name, process in processes:
        process.join()
        if process.exitcode == 0:
            results[series_name] = "✅ Success"
        else:
            results[series_name] = "❌ Failed"
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 DOWNLOAD RESULTS")
    print("=" * 60)
    for series_name, result in results.items():
        series_title = test_series[series_name]['series_title']
        print(f"{series_title}: {result}")
    
    print(f"\n⏱️  Total time: {duration:.1f} seconds")
    print(f"📁 Files saved to: test_downloads/")
    
    # Check final results
    success_count = sum(1 for result in results.values() if "✅" in result)
    print(f"\n🎯 Successfully downloaded: {success_count}/{len(results)} series")

if __name__ == "__main__":
    main() 