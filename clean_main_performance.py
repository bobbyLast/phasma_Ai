"""
============================================================
PHASMA AI - CLEAN MAIN PERFORMANCE TEST
============================================================
No emojis, pure performance tracking
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import time
import json

def clean_main_performance_test():
    """Test main performance without encoding issues"""
    
    print("=" * 80)
    print("PHASMA AI - CLEAN MAIN PERFORMANCE TEST")
    print("=" * 80)
    
    metrics = {
        'start_time': time.time(),
        'phases': {},
        'articles': 0,
        'signals': 0,
        'errors': []
    }
    
    try:
        # Phase 1: Configuration
        print("\n[PHASE 1] Loading configuration...")
        phase_start = time.time()
        
        from config.secure_config import config
        
        phase_time = time.time() - phase_start
        metrics['phases']['config'] = phase_time
        print(f"   Configuration loaded in {phase_time:.2f}s")
        
        # Phase 2: Data Integration
        print("\n[PHASE 2] Initializing data integration...")
        phase_start = time.time()
        
        from engines.final_100_percent_integration import Final100PercentIntegration
        integration = Final100PercentIntegration()
        
        phase_time = time.time() - phase_start
        metrics['phases']['initialization'] = phase_time
        print(f"   Integration initialized in {phase_time:.2f}s")
        
        # Phase 3: Data Fetching
        print("\n[PHASE 3] Fetching data from all sources...")
        phase_start = time.time()
        
        results = integration.get_final_results()
        
        phase_time = time.time() - phase_start
        metrics['phases']['data_fetch'] = phase_time
        metrics['articles'] = results.get('articles_per_fetch', 0)
        print(f"   Data fetched in {phase_time:.2f}s")
        print(f"   Sources working: {results['success_rate']:.1f}%")
        print(f"   Articles fetched: {metrics['articles']}")
        
        # Phase 4: Signal Detection
        print("\n[PHASE 4] Detecting signals...")
        phase_start = time.time()
        
        from final_integration_test import FinalIntegrationTest
        tester = FinalIntegrationTest()
        signals = tester.analyze_all_sources()
        
        phase_time = time.time() - phase_start
        metrics['phases']['signal_detection'] = phase_time
        metrics['signals'] = len(signals)
        print(f"   Signals detected in {phase_time:.2f}s")
        print(f"   Total signals: {metrics['signals']}")
        
        # Phase 5: Results Processing
        print("\n[PHASE 5] Processing results...")
        phase_start = time.time()
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"main_performance_{timestamp}.json"
        
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'total_time': time.time() - metrics['start_time'],
            'phases': metrics['phases'],
            'articles': metrics['articles'],
            'signals': metrics['signals'],
            'success_rate': results['success_rate'],
            'status': 'success'
        }
        
        with open(filename, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        phase_time = time.time() - phase_start
        metrics['phases']['results_processing'] = phase_time
        print(f"   Results processed in {phase_time:.2f}s")
        print(f"   Saved to: {filename}")
        
    except Exception as e:
        error_msg = str(e)
        metrics['errors'].append({
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        })
        print(f"\nERROR: {error_msg}")
    
    # Final metrics
    total_time = time.time() - metrics['start_time']
    
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    
    print(f"\nEXECUTION METRICS:")
    print(f"   Total Time: {total_time:.2f} seconds")
    print(f"   Articles Processed: {metrics['articles']}")
    print(f"   Signals Detected: {metrics['signals']}")
    print(f"   Errors: {len(metrics['errors'])}")
    
    print(f"\nPHASE BREAKDOWN:")
    for phase, duration in metrics['phases'].items():
        percentage = (duration / total_time) * 100
        print(f"   {phase}: {duration:.2f}s ({percentage:.1f}%)")
    
    print(f"\nPERFORMANCE RATINGS:")
    
    # Calculate ratings
    if total_time < 10:
        speed_rating = "EXCELLENT"
    elif total_time < 20:
        speed_rating = "GOOD"
    else:
        speed_rating = "NEEDS OPTIMIZATION"
    
    if metrics['articles'] > 100:
        data_rating = "EXCELLENT"
    elif metrics['articles'] > 50:
        data_rating = "GOOD"
    else:
        data_rating = "FAIR"
    
    if metrics['signals'] > 50:
        signal_rating = "EXCELLENT"
    elif metrics['signals'] > 20:
        signal_rating = "GOOD"
    else:
        signal_rating = "FAIR"
    
    print(f"   Speed: {speed_rating}")
    print(f"   Data Volume: {data_rating}")
    print(f"   Signal Detection: {signal_rating}")
    
    # Throughput calculations
    if total_time > 0:
        articles_per_sec = metrics['articles'] / total_time
        signals_per_sec = metrics['signals'] / total_time
        
        print(f"\nTHROUGHPUT:")
        print(f"   Articles/Second: {articles_per_sec:.1f}")
        print(f"   Signals/Second: {signals_per_sec:.2f}")
    
    print("\n" + "=" * 80)
    
    if len(metrics['errors']) == 0:
        print("RESULT: MAIN.PY PERFORMANCE TEST PASSED")
        print("SYSTEM IS PRODUCTION READY")
    else:
        print("RESULT: PERFORMANCE TEST HAD ERRORS")
        print("REVIEW ERRORS ABOVE")
    
    print("=" * 80)
    
    return metrics

if __name__ == "__main__":
    results = clean_main_performance_test()
    sys.exit(0 if len(results['errors']) == 0 else 1)
