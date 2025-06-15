#!/usr/bin/env python3
"""
Deep analysis of RAGAS traces to understand available data for dashboard
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
from src.infrastructure.evaluation import RateLimitedEmbeddings
import config


def load_evaluation_data() -> Dataset:
    """Load evaluation data from JSON file"""
    with open("data/evaluation_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Convert to Hugging Face Dataset format
    return Dataset.from_list(data)


def analyze_traces_deep(result):
    """Deep analysis of traces for dashboard data extraction"""
    
    print("="*80)
    print("DEEP TRACES ANALYSIS FOR DASHBOARD")
    print("="*80)
    
    # Analyze individual traces
    if hasattr(result, 'traces') and result.traces:
        print(f"\n1. INDIVIDUAL TRACES STRUCTURE:")
        for i, trace in enumerate(result.traces):
            print(f"\n   Data Point {i+1} Trace:")
            print(f"      Keys: {list(trace.keys())}")
            
            for metric_name, metric_trace in trace.items():
                print(f"\n      {metric_name.upper()} TRACE:")
                print(f"         Type: {type(metric_trace)}")
                
                if isinstance(metric_trace, dict):
                    for step_name, step_data in metric_trace.items():
                        print(f"         Step '{step_name}':")
                        print(f"            Type: {type(step_data)}")
                        
                        if isinstance(step_data, dict):
                            for key, value in step_data.items():
                                print(f"               {key}: {type(value)}")
                                
                                # Show sample content for important fields
                                if key in ['input', 'output']:
                                    if hasattr(value, '__dict__'):
                                        print(f"                  Content: {value.__dict__}")
                                    else:
                                        print(f"                  Content: {str(value)[:200]}...")
                                elif key == 'output' and isinstance(value, str):
                                    print(f"                  Content: {value[:200]}...")
    
    # Analyze ragas_traces for execution details
    if hasattr(result, 'ragas_traces') and result.ragas_traces:
        print(f"\n2. RAGAS TRACES EXECUTION DETAILS:")
        
        execution_data = {}
        
        for trace_id, chain_run in result.ragas_traces.items():
            print(f"\n   Trace ID: {trace_id}")
            
            # Basic info
            trace_info = {
                'trace_id': trace_id,
                'type': str(type(chain_run)),
            }
            
            # Timing information
            if hasattr(chain_run, 'start_time') and chain_run.start_time:
                trace_info['start_time'] = chain_run.start_time.isoformat()
                print(f"      Start Time: {chain_run.start_time}")
            
            if hasattr(chain_run, 'end_time') and chain_run.end_time:
                trace_info['end_time'] = chain_run.end_time.isoformat()
                print(f"      End Time: {chain_run.end_time}")
                
                if hasattr(chain_run, 'start_time') and chain_run.start_time:
                    duration = (chain_run.end_time - chain_run.start_time).total_seconds()
                    trace_info['duration_seconds'] = duration
                    print(f"      Duration: {duration:.3f} seconds")
            
            # Input/Output information
            if hasattr(chain_run, 'inputs') and chain_run.inputs:
                trace_info['input_keys'] = list(chain_run.inputs.keys())
                print(f"      Input Keys: {list(chain_run.inputs.keys())}")
                
                # Show sample input content
                for key, value in chain_run.inputs.items():
                    print(f"         {key}: {type(value)} - {str(value)[:100]}...")
            
            if hasattr(chain_run, 'outputs') and chain_run.outputs:
                trace_info['output_keys'] = list(chain_run.outputs.keys())
                print(f"      Output Keys: {list(chain_run.outputs.keys())}")
                
                # Show sample output content
                for key, value in chain_run.outputs.items():
                    print(f"         {key}: {type(value)} - {str(value)[:100]}...")
            
            # Error information
            if hasattr(chain_run, 'error') and chain_run.error:
                trace_info['error'] = str(chain_run.error)
                print(f"      Error: {chain_run.error}")
            
            # Additional metadata
            if hasattr(chain_run, 'extra'):
                trace_info['extra'] = chain_run.extra
                print(f"      Extra: {chain_run.extra}")
            
            if hasattr(chain_run, 'tags') and chain_run.tags:
                trace_info['tags'] = chain_run.tags
                print(f"      Tags: {chain_run.tags}")
            
            execution_data[trace_id] = trace_info
        
        # Save execution data
        with open('execution_traces.json', 'w', encoding='utf-8') as f:
            json.dump(execution_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\nExecution traces saved to: execution_traces.json")
    
    # Analyze dataset for additional context
    if hasattr(result, 'dataset'):
        print(f"\n3. DATASET ANALYSIS:")
        dataset = result.dataset
        
        print(f"   Dataset Type: {type(dataset)}")
        print(f"   Dataset Length: {len(dataset)}")
        
        if hasattr(dataset, 'to_pandas'):
            df = dataset.to_pandas()
            print(f"   DataFrame Columns: {list(df.columns)}")
            
            # Analyze content for dashboard insights
            print(f"\n   Content Analysis:")
            for col in df.columns:
                print(f"      {col}:")
                sample_value = df[col].iloc[0]
                print(f"         Type: {type(sample_value)}")
                if isinstance(sample_value, list):
                    print(f"         List Length: {len(sample_value)}")
                    if sample_value:
                        print(f"         First Item: {str(sample_value[0])[:100]}...")
                else:
                    print(f"         Sample: {str(sample_value)[:100]}...")
    
    return result


def extract_dashboard_data_structure(result):
    """Extract structured data that would be useful for dashboard visualization"""
    
    dashboard_data = {
        'evaluation_metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_data_points': len(result.dataset) if hasattr(result, 'dataset') else 0,
            'metrics_evaluated': list(result._scores_dict.keys()) if hasattr(result, '_scores_dict') else [],
            'evaluation_time': None,  # Would need to be passed in
        },
        
        'aggregate_scores': result._repr_dict if hasattr(result, '_repr_dict') else {},
        
        'individual_scores': result.scores if hasattr(result, 'scores') else [],
        
        'score_distributions': {
            metric: {
                'values': scores,
                'mean': sum(scores) / len(scores) if scores else 0,
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0,
                'std': None,  # Would calculate if needed
            }
            for metric, scores in (result._scores_dict.items() if hasattr(result, '_scores_dict') else {}).items()
        },
        
        'data_points': [],
        
        'execution_traces': {
            'total_traces': len(result.ragas_traces) if hasattr(result, 'ragas_traces') else 0,
            'trace_ids': list(result.ragas_traces.keys()) if hasattr(result, 'ragas_traces') else [],
        },
        
        'performance_metrics': {
            'traces_with_timing': 0,
            'average_execution_time': None,
            'slowest_operation': None,
            'fastest_operation': None,
        }
    }
    
    # Extract individual data points with their context
    if hasattr(result, 'dataset'):
        df = result.dataset.to_pandas()
        for i, row in df.iterrows():
            data_point = {
                'index': i,
                'question': row.get('user_input', ''),
                'answer': row.get('response', ''),
                'contexts': row.get('retrieved_contexts', []),
                'ground_truth': row.get('reference', ''),
                'scores': {}
            }
            
            # Add individual scores
            if hasattr(result, 'scores') and i < len(result.scores):
                data_point['scores'] = result.scores[i]
            
            # Add context analysis
            if 'retrieved_contexts' in row:
                contexts = row['retrieved_contexts']
                data_point['context_analysis'] = {
                    'context_count': len(contexts) if contexts else 0,
                    'total_context_length': sum(len(ctx) for ctx in contexts) if contexts else 0,
                    'average_context_length': sum(len(ctx) for ctx in contexts) / len(contexts) if contexts else 0,
                }
            
            # Add text analysis
            data_point['text_analysis'] = {
                'question_length': len(row.get('user_input', '')),
                'answer_length': len(row.get('response', '')),
                'ground_truth_length': len(row.get('reference', '')),
            }
            
            dashboard_data['data_points'].append(data_point)
    
    # Analyze execution performance
    if hasattr(result, 'ragas_traces'):
        timing_data = []
        for trace_id, chain_run in result.ragas_traces.items():
            if hasattr(chain_run, 'start_time') and hasattr(chain_run, 'end_time') and chain_run.start_time and chain_run.end_time:
                duration = (chain_run.end_time - chain_run.start_time).total_seconds()
                timing_data.append({
                    'trace_id': trace_id,
                    'duration': duration,
                    'inputs': list(chain_run.inputs.keys()) if hasattr(chain_run, 'inputs') and chain_run.inputs else [],
                    'outputs': list(chain_run.outputs.keys()) if hasattr(chain_run, 'outputs') and chain_run.outputs else [],
                })
        
        if timing_data:
            dashboard_data['performance_metrics']['traces_with_timing'] = len(timing_data)
            durations = [t['duration'] for t in timing_data]
            dashboard_data['performance_metrics']['average_execution_time'] = sum(durations) / len(durations)
            dashboard_data['performance_metrics']['slowest_operation'] = max(timing_data, key=lambda x: x['duration'])
            dashboard_data['performance_metrics']['fastest_operation'] = min(timing_data, key=lambda x: x['duration'])
    
    return dashboard_data


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
    
    print("Starting RAGAS evaluation for deep trace analysis...")
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
    
    # Deep trace analysis
    analyze_traces_deep(result)
    
    # Extract dashboard data structure
    dashboard_data = extract_dashboard_data_structure(result)
    dashboard_data['evaluation_metadata']['evaluation_time'] = evaluation_time
    
    # Save dashboard data structure
    with open('dashboard_data_structure.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nDashboard data structure saved to: dashboard_data_structure.json")
    
    return result


if __name__ == "__main__":
    main()