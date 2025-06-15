#!/usr/bin/env python3
"""Test script to verify data loading functionality"""

import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the function we want to test
from presentation.web.components.detailed_analysis import load_actual_qa_data_from_dataset

def test_data_loading():
    """Test the data loading function"""
    print("Testing data loading functionality...")
    print("=" * 50)
    
    # Test 1: Load evaluation_data.json
    print("\n[TEST 1] Loading evaluation_data.json with 3 items")
    result = load_actual_qa_data_from_dataset("evaluation_data.json", 3)
    if result:
        print(f"SUCCESS: Loaded {len(result)} items")
        print(f"First question: {result[0].get('question', 'N/A')[:50]}...")
    else:
        print("FAILED: Could not load data")
    
    # Test 2: Load evaluation_data_variant1.json
    print("\n[TEST 2] Loading evaluation_data_variant1.json with 2 items")
    result = load_actual_qa_data_from_dataset("evaluation_data_variant1.json", 2)
    if result:
        print(f"SUCCESS: Loaded {len(result)} items")
        print(f"First question: {result[0].get('question', 'N/A')[:50]}...")
    else:
        print("FAILED: Could not load data")
    
    # Test 3: Test with non-existent file
    print("\n[TEST 3] Testing with non-existent file")
    result = load_actual_qa_data_from_dataset("non_existent.json", 5)
    if result is None:
        print("SUCCESS: Correctly returned None for non-existent file")
    else:
        print("FAILED: Should have returned None")
    
    # Test 4: Direct path check
    print("\n[TEST 4] Direct path verification")
    data_path = Path("/Users/isle/PycharmProjects/ragas-test/data/evaluation_data.json")
    print(f"Path exists: {data_path.exists()}")
    print(f"Is file: {data_path.is_file()}")
    print(f"Is readable: {data_path.exists() and data_path.stat().st_mode & 0o444}")
    
    if data_path.exists():
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
                print(f"Direct load SUCCESS: {len(data)} items in file")
        except Exception as e:
            print(f"Direct load FAILED: {e}")

if __name__ == "__main__":
    test_data_loading()