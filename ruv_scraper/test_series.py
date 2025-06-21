#!/usr/bin/env python3
"""
Test configuration for RÚV series downloads
Contains URLs and expected filenames for validation
"""

# Test series configurations
TEST_SERIES = {
    "bubbi_byggir": {
        "url": "https://www.ruv.is/sjonvarp/spila/bubbi-byggir/37750/b80cbg",
        "series_title": "Bubbi byggir",
        "expected_episodes": [
            "Moki álfur.mkv",
            "Ofur-Skófli.mkv", 
            "Ískalt ráðhús.mkv",
            "Komum Selmu á óvart!.mkv",
            "Húsflutningur.mkv",
            "Filip, hinn mikilvægi.mkv",
            "Moki fílar fíl.mkv",
            "Moki stekkur.mkv",
            "Brjálað brúðkaup.mkv",
            "Bandið hans Bubba.mkv",
            "Hvar er Snotra?.mkv",
            "Bílalúguklandur.mkv",
            "Flotrusl og sjóhroði.mkv",
            "Draugur í ráðhósinu.mkv",
            "Filip fær að gista.mkv",
            "Pýramídagátan.mkv"
        ],
        "expected_info_file": "info.nfo"
    },
    "sammi_brunavordur": {
        "url": "https://www.ruv.is/sjonvarp/spila/sammi-brunavordur-x/37768/b85s4e",
        "series_title": "Sammi brunavörður X",
        "expected_episodes": [
            "Spýtubjörn.mkv",
            "Lestin utan úr geimnum.mkv",
            "Í fínu formi.mkv",
            "Týnd í hellunum.mkv",
            "Fótboltaleikurinn.mkv",
            "Ósættið.mkv",
            "Refur á flótta.mkv",
            "Njósnaleikir.mkv",
            "Strætóvandræði.mkv",
            "Hundafár.mkv",
            "Pizzu vandræðin.mkv",
            "Konungar og kastalar.mkv",
            "Afmælið hans Samma.mkv",
            "Hestur á flótta.mkv"
        ],
        "expected_info_file": "info.nfo"
    }
}

def get_test_series(series_name):
    """Get test configuration for a specific series"""
    return TEST_SERIES.get(series_name)

def get_all_test_series():
    """Get all test series configurations"""
    return TEST_SERIES

def validate_download(series_name, output_dir):
    """Validate that downloaded files match expected filenames"""
    import os
    
    if series_name not in TEST_SERIES:
        return False, f"Unknown series: {series_name}"
    
    test_config = TEST_SERIES[series_name]
    series_dir = os.path.join(output_dir, test_config["series_title"])
    
    if not os.path.exists(series_dir):
        return False, f"Series directory not found: {series_dir}"
    
    # Check for info file
    info_file = os.path.join(series_dir, test_config["expected_info_file"])
    if not os.path.exists(info_file):
        return False, f"Info file not found: {info_file}"
    
    # Check for episode files
    missing_files = []
    extra_files = []
    
    for expected_file in test_config["expected_episodes"]:
        file_path = os.path.join(series_dir, expected_file)
        if not os.path.exists(file_path):
            missing_files.append(expected_file)
    
    # Check for extra files (should only be .mkv and .nfo)
    for file in os.listdir(series_dir):
        if not file.endswith(('.mkv', '.nfo')):
            extra_files.append(file)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    if extra_files:
        return False, f"Extra files found: {extra_files}"
    
    return True, f"All {len(test_config['expected_episodes'])} episodes downloaded correctly"

if __name__ == "__main__":
    print("RÚV Series Test Configuration")
    print("=" * 40)
    for name, config in TEST_SERIES.items():
        print(f"\n{config['series_title']}:")
        print(f"  URL: {config['url']}")
        print(f"  Episodes: {len(config['expected_episodes'])}")
        print(f"  Expected files: {config['expected_episodes'][:3]}...") 