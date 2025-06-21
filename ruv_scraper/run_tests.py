import os
import subprocess
import shutil
import sys

# Define the location of the main scraper script
SCRAPER_SCRIPT = os.path.join(os.path.dirname(__file__), 'ruv_improved_scraper.py')
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_downloads')

# Define the test cases
TEST_CASES = [
    {
        "url": "https://www.ruv.is/sjonvarp/spila/bubbi-byggir/37750/b80cbg",
        "series_title": "Bubbi byggir",
        "expected_episodes": {"Moki álfur.mkv", "Ofur-Skófli.mkv"},
        "limit": 2
    },
    {
        "url": "https://www.ruv.is/sjonvarp/spila/sammi-brunavordur-x/37768/b85s4f",
        "series_title": "Sammi brunavörður X",
        "expected_episodes": {"Spýtubjörn.mkv", "Lestin utan úr geimnum.mkv"},
        "limit": 2
    }
]

def run_test(test_case):
    """Runs a single test case for the scraper."""
    print(f"--- Running Test for: {test_case['series_title']} ---")
    
    # Construct the command to run the scraper
    command = [
        sys.executable,
        SCRAPER_SCRIPT,
        test_case['url'],
        '--limit', str(test_case['limit']),
        '--output-dir', TEST_OUTPUT_DIR
    ]
    
    # Run the scraper
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        print(f"FAIL: Scraper script exited with error code {result.returncode}.")
        print(result.stdout)
        print(result.stderr)
        return False
        
    # --- Validation ---
    series_dir = os.path.join(TEST_OUTPUT_DIR, test_case['series_title'])
    
    # 1. Check if the series directory was created
    if not os.path.isdir(series_dir):
        print(f"FAIL: Series directory was not created at '{series_dir}'")
        return False
    print(f"PASS: Series directory created.")

    # 2. Check for the info file
    info_file_path = os.path.join(series_dir, 'info.nfo')
    if not os.path.isfile(info_file_path):
        print("FAIL: info.nfo file was not created.")
        return False
    print("PASS: info.nfo file created.")
        
    # 3. Check for the correct episode files
    actual_files = {f for f in os.listdir(series_dir) if f.endswith('.mkv')}
    
    if actual_files == test_case['expected_episodes']:
        print(f"PASS: Found expected episodes: {', '.join(actual_files)}")
    else:
        print(f"FAIL: Episode mismatch.")
        print(f"  Expected: {test_case['expected_episodes']}")
        print(f"  Actual:   {actual_files}")
        return False
        
    print(f"--- Test for {test_case['series_title']} Successful ---\n")
    return True

def main():
    """Main test function."""
    print("Starting scraper tests...")
    
    # Clean up previous test runs
    if os.path.isdir(TEST_OUTPUT_DIR):
        print(f"Removing existing test directory: {TEST_OUTPUT_DIR}")
        shutil.rmtree(TEST_OUTPUT_DIR)
        
    os.makedirs(TEST_OUTPUT_DIR)
    print(f"Created fresh test directory: {TEST_OUTPUT_DIR}\n")
    
    passed_tests = 0
    failed_tests = 0
    
    for test in TEST_CASES:
        if run_test(test):
            passed_tests += 1
        else:
            failed_tests += 1
            
    # --- Summary ---
    print("="*30)
    print("      TEST SUMMARY")
    print("="*30)
    print(f"Tests Passed: {passed_tests}")
    print(f"Tests Failed: {failed_tests}")
    print("="*30)
    
    if failed_tests > 0:
        sys.exit(1)

if __name__ == '__main__':
    main() 