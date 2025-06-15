#!/usr/bin/env python3
"""
Script to analyze the detailed RAGAS evaluation data structure
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from langchain_google_genai import GoogleGenerativeAI
from src.infrastructure.ragas_eval import RateLimitedEmbeddings
import config


def load_evaluation_data() -> Dataset:
    """Load evaluation data from JSON file"""
    with open("data/evaluation_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Convert to Hugging Face Dataset format
    return Dataset.from_list(data)


def analyze_evaluation_result(result):
    """Comprehensive analysis of RAGAS evaluation result object"""
    
    print("="*80)
    print("DETAILED RAGAS EVALUATION RESULT ANALYSIS")
    print("="*80)
    
    # 1. Basic Object Information
    print(f"\n1. BASIC OBJECT INFO:")
    print(f"   Type: {type(result)}")
    print(f"   Module: {result.__class__.__module__}")
    
    # 2. All attributes
    print(f"\n2. ALL ATTRIBUTES:")
    for attr in dir(result):
        if not attr.startswith('__'):
            try:
                value = getattr(result, attr)
                value_type = type(value)
                print(f"   {attr}: {value_type}")
                
                # Show value for small items
                if attr in ['run_id', 'binary_columns', 'cost_cb']:
                    print(f"      Value: {value}")
            except Exception as e:
                print(f"   {attr}: ERROR - {e}")
    
    # 3. Core Data Structures
    print(f"\n3. CORE DATA STRUCTURES:")
    
    # Scores (individual data points)
    if hasattr(result, 'scores'):
        print(f"   scores (individual results):")
        print(f"      Type: {type(result.scores)}")
        print(f"      Length: {len(result.scores) if result.scores else 'None'}")
        if result.scores:
            print(f"      First item: {result.scores[0]}")
            print(f"      Keys: {list(result.scores[0].keys())}")
    
    # Scores dict (aggregated by metric)
    if hasattr(result, '_scores_dict'):
        print(f"   _scores_dict (by metric):")
        print(f"      Type: {type(result._scores_dict)}")
        print(f"      Keys: {list(result._scores_dict.keys())}")
        for metric, values in result._scores_dict.items():
            print(f"      {metric}: {values} (type: {type(values)}, len: {len(values)})")
    
    # Repr dict (mean values)
    if hasattr(result, '_repr_dict'):
        print(f"   _repr_dict (mean values):")
        for metric, value in result._repr_dict.items():
            print(f"      {metric}: {value} (type: {type(value)})")
    
    # 4. Dataset Information
    print(f"\n4. DATASET INFO:")
    if hasattr(result, 'dataset'):
        dataset = result.dataset
        print(f"   Type: {type(dataset)}")
        if hasattr(dataset, 'features'):
            print(f"   Features: {dataset.features}")
        if hasattr(dataset, '__len__'):
            print(f"   Length: {len(dataset)}")
        
        # Show first few rows
        if hasattr(dataset, 'to_pandas'):
            try:
                df = dataset.to_pandas()
                print(f"   Columns: {list(df.columns)}")
                print(f"   First row:")
                for col in df.columns:
                    print(f"      {col}: {df[col].iloc[0]}")
            except Exception as e:
                print(f"   Could not convert to pandas: {e}")
    
    # 5. Traces and Execution Details
    print(f"\n5. TRACES & EXECUTION:")
    
    if hasattr(result, 'traces'):
        print(f"   traces:")
        print(f"      Type: {type(result.traces)}")
        print(f"      Length: {len(result.traces) if result.traces else 'None'}")
        if result.traces:
            print(f"      First trace keys: {list(result.traces[0].keys()) if result.traces[0] else 'None'}")
            # Show detailed trace structure
            trace = result.traces[0]
            for key, value in trace.items():
                print(f"         {key}: {type(value)} - {str(value)[:100]}...")
    
    if hasattr(result, 'ragas_traces'):
        print(f"   ragas_traces:")
        print(f"      Type: {type(result.ragas_traces)}")
        print(f"      Keys: {list(result.ragas_traces.keys()) if result.ragas_traces else 'None'}")
        if result.ragas_traces:
            for key, value in result.ragas_traces.items():
                print(f"         {key}: {type(value)}")
                # Show ChainRun details
                if hasattr(value, 'start_time'):
                    print(f"            start_time: {value.start_time}")
                if hasattr(value, 'end_time'):
                    print(f"            end_time: {value.end_time}")
                if hasattr(value, 'inputs'):
                    print(f"            inputs: {list(value.inputs.keys()) if value.inputs else 'None'}")
                if hasattr(value, 'outputs'):
                    print(f"            outputs: {list(value.outputs.keys()) if value.outputs else 'None'}")
    
    # 6. Cost Information
    print(f"\n6. COST INFORMATION:")
    if hasattr(result, 'cost_cb') and result.cost_cb:
        print(f"   cost_cb type: {type(result.cost_cb)}")
        # Try to get cost details
        try:
            total_cost = result.total_cost()
            print(f"   total_cost(): {total_cost}")
        except Exception as e:
            print(f"   total_cost() error: {e}")
        
        try:
            total_tokens = result.total_tokens()
            print(f"   total_tokens(): {total_tokens}")
        except Exception as e:
            print(f"   total_tokens() error: {e}")
    else:
        print(f"   No cost callback available")
    
    # 7. Methods Available
    print(f"\n7. AVAILABLE METHODS:")
    methods = [method for method in dir(result) if callable(getattr(result, method)) and not method.startswith('__')]
    for method in methods:
        print(f"   {method}()")
    
    # 8. Try to_pandas()
    print(f"\n8. PANDAS CONVERSION:")
    try:
        df = result.to_pandas()
        print(f"   DataFrame shape: {df.shape}")
        print(f"   DataFrame columns: {list(df.columns)}")
        print(f"   DataFrame dtypes:")
        for col, dtype in df.dtypes.items():
            print(f"      {col}: {dtype}")
        
        print(f"   Sample data:")
        print(df.head())
        
    except Exception as e:
        print(f"   to_pandas() error: {e}")
    
    print("="*80)
    return result


def main():
    """Main analysis function"""
    
    # Load data
    dataset = load_evaluation_data()
    print(f"Loaded dataset with {len(dataset)} examples")
    
    # Setup LLM and embeddings
    llm = GoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0,
    )
    
    embeddings = RateLimitedEmbeddings(
        model="models/gemini-embedding-exp-03-07",
        google_api_key=config.GEMINI_API_KEY,
        requests_per_minute=10,
    )
    
    # Define metrics
    metrics = [
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    ]
    
    print("Starting RAGAS evaluation...")
    start_time = time.time()
    
    # Run evaluation
    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False,
    )
    
    end_time = time.time()
    evaluation_time = end_time - start_time
    
    print(f"Evaluation completed in {evaluation_time:.2f} seconds")
    
    # Detailed analysis
    analyze_evaluation_result(result)
    
    # Save detailed results to JSON for further analysis
    detailed_results = {
        'timestamp': datetime.now().isoformat(),
        'evaluation_time_seconds': evaluation_time,
        'basic_info': {
            'type': str(type(result)),
            'module': result.__class__.__module__,
        },
        'scores_dict': result._scores_dict if hasattr(result, '_scores_dict') else None,
        'repr_dict': result._repr_dict if hasattr(result, '_repr_dict') else None,
        'individual_scores': result.scores if hasattr(result, 'scores') else None,
        'run_id': str(result.run_id) if hasattr(result, 'run_id') and result.run_id else None,
        'binary_columns': result.binary_columns if hasattr(result, 'binary_columns') else None,
        'traces_count': len(result.traces) if hasattr(result, 'traces') and result.traces else 0,
        'ragas_traces_keys': list(result.ragas_traces.keys()) if hasattr(result, 'ragas_traces') and result.ragas_traces else [],
    }
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_numpy_types(obj):
        if hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(v) for v in obj]
        else:
            return obj
    
    detailed_results = convert_numpy_types(detailed_results)
    
    with open('detailed_evaluation_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed analysis saved to: detailed_evaluation_analysis.json")
    
    return result


if __name__ == "__main__":
    main()