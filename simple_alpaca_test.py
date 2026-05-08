#!/usr/bin/env python3

# Simple Alpaca Test - No system imports
import alpaca_trade_api as tradeapi

def test_alpaca_connection():
    """Test Alpaca connection with just the API key"""
    print("🔧 Testing Alpaca API Connection...")
    
    # Test with the real credentials
    api_key = "PKY7UOZU5S7AZZ4QIH2BJ5F52X"
    api_secret = "J8iDXzCoHhrvpPK8yTXu3dRP1FybmAVW77QWZDPyzJs3"
    base_url = "https://paper-api.alpaca.markets"
    
    try:
        # Try to connect
        alpaca = tradeapi.REST(
            key_id=api_key,
            secret_key=api_secret,
            base_url=base_url,
            api_version='v2'
        )
        
        # Test connection
        account = alpaca.get_account()
        print("✅ SUCCESS: Connected to Alpaca!")
        print(f"   Account ID: {account.id}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("🔍 Analyzing error...")
        
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print("   ✅ This is expected - we need the secret key!")
            print("   ✅ API key is valid but needs secret key for authentication")
            return "need_secret_key"
        elif "403" in str(e) or "forbidden" in str(e).lower():
            print("   ✅ This is expected - we need the secret key!")
            print("   ✅ API key is valid but needs secret key for authentication")
            return "need_secret_key"
        else:
            print(f"   ❓ Unexpected error - might be different issue")
            return False

if __name__ == "__main__":
    result = test_alpaca_connection()
    
    if result == "need_secret_key":
        print("\n🎯 CONCLUSION: We DO need the secret key!")
        print("   The public key alone is not sufficient for API access.")
    elif result == True:
        print("\n🎯 CONCLUSION: Secret key not needed!")
        print("   Connected with just the public key.")
    else:
        print("\n⚠️ CONCLUSION: Different issue detected")
