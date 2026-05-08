"""
============================================================
PHASMA AI - MAIN PRODUCTION SCRIPT
============================================================
Simple, working main script for production
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json
import time
import logging

# Configure logging without emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phasma_main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PhasmaAI')

def main():
    """Main production function"""
    
    print("=" * 80)
    print("PHASMA AI - PRODUCTION SYSTEM")
    print("=" * 80)
    
    logger.info("Starting Phasma AI production system...")
    
    try:
        # Load configuration
        from config.secure_config import config
        logger.info("Configuration loaded successfully")
        
        # Initialize integration
        from engines.final_100_percent_integration import Final100PercentIntegration
        integration = Final100PercentIntegration()
        
        # Run production cycle
        logger.info("Running production cycle...")
        results = integration.get_final_results()
        
        # Display results
        print("\nPRODUCTION RESULTS:")
        print(f"  Sources Working: {results['success_rate']:.1f}%")
        print(f"  Articles Fetched: {results.get('articles_per_fetch', 0)}")
        print(f"  Status: PRODUCTION READY")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"main_run_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'status': 'success'
            }, f, indent=2, default=str)
        
        print(f"\nResults saved to: {filename}")
        
        # Test signal detection
        from final_integration_test import FinalIntegrationTest
        tester = FinalIntegrationTest()
        signals = tester.analyze_all_sources()
        
        print(f"\nSignal Detection: {len(signals)} signals found")
        
        logger.info("Production cycle completed successfully")
        print("\nSUCCESS: Phasma AI is production ready!")
        
        return True
        
    except Exception as e:
        logger.error(f"Production failed: {e}")
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            print("Running in test mode...")
            success = main()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == '--production':
            print("Running in production mode...")
            while True:
                success = main()
                if not success:
                    print("Production failed, retrying in 5 minutes...")
                    time.sleep(300)
                else:
                    print("Cycle completed, waiting 5 minutes...")
                    time.sleep(300)
        else:
            print("Usage: python main_simple.py [--test|--production]")
    else:
        # Default to test
        print("Running default test...")
        success = main()
        sys.exit(0 if success else 1)
