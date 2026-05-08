#!/usr/bin/env python3
"""
Test script for Thesis Manager - demonstrates long-term trade reasoning system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.thesis_manager import ThesisManager


def main():
    print("=" * 80)
    print("THESIS MANAGER TEST - Long-term Trade Reasoning System")
    print("=" * 80)
    
    # Initialize the thesis manager
    tm = ThesisManager()
    
    # Test with PLUG (the example from update.txt)
    print("\n\n" + "=" * 80)
    print("TESTING PLUG POWER (PLUG) - Optionality/Venture Case Study")
    print("=" * 80)
    
    # Run the Master Decision Loop
    decision = tm.master_decision_loop("PLUG")
    
    print("\n\nDECISION SUMMARY:")
    for key, value in decision.items():
        print(f"   {key}: {value}")
    
    # If decision is to establish thesis, do it
    if decision.get("action") == "establish_thesis":
        print("\n\nESTABLISHING THESIS...")
        tm.establish_thesis("PLUG", decision)
        
        # Generate comprehensive report
        print("\n\n" + tm.generate_thesis_report("PLUG"))
    
    # Test with a different type of stock (Infrastructure)
    print("\n\n" + "=" * 80)
    print("TESTING UTILITY STOCK (DUK) - Infrastructure/Cash-flow Case")
    print("=" * 80)
    
    decision_duk = tm.master_decision_loop("DUK")
    
    print("\n\nDECISION SUMMARY:")
    for key, value in decision_duk.items():
        print(f"   {key}: {value}")
    
    # Test with a growth stock
    print("\n\n" + "=" * 80)
    print("TESTING AI STOCK (NVDA) - Growth/Execution Case")
    print("=" * 80)
    
    decision_nvda = tm.master_decision_loop("NVDA")
    
    print("\n\nDECISION SUMMARY:")
    for key, value in decision_nvda.items():
        print(f"   {key}: {value}")
    
    # Show all active theses
    print("\n\n" + "=" * 80)
    print("ALL ACTIVE THESES")
    print("=" * 80)
    
    active_theses = tm.get_active_theses()
    for thesis in active_theses:
        print(f"\n{thesis['ticker']}:")
        print(f"   Type: {thesis['thesis_type']}")
        print(f"   Confidence: {thesis['current_confidence']}/100")
        print(f"   Max Size: {thesis['max_position_size']}%")
    
    # Demonstrate confidence events
    print("\n\n" + "=" * 80)
    print("SIMULATING CONFIDENCE EVENTS FOR PLUG")
    print("=" * 80)
    
    # Positive event: Hydrogen cost breakthrough
    tm.record_confidence_event(
        "PLUG",
        "positive",
        10,
        "Hydrogen production costs drop below $2/kg - major milestone"
    )
    
    # Negative event: Dilution
    tm.record_confidence_event(
        "PLUG",
        "negative",
        -15,
        "Company announces $300M convertible notes - significant dilution risk"
    )
    
    # Apply time decay (simulate 2 years passing)
    print("\n\nSimulating 2 years of time decay...")
    tm.apply_confidence_decay()
    
    # Show final PLUG report
    print("\n\n" + tm.generate_thesis_report("PLUG"))
    
    print("\n\n" + "=" * 80)
    print("THESIS MANAGER TEST COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("✓ Master Decision Loop classification system")
    print("✓ Survival & dilution risk analysis")
    print("✓ Confidence decay with time-based triggers")
    print("✓ Optionality scoring (5-factor system)")
    print("✓ Position sizing by regret tolerance")
    print("✓ Automatic downgrade/exit logic")
    print("\nThe system is ready to integrate with insider_monitor.py!")


if __name__ == "__main__":
    main()
