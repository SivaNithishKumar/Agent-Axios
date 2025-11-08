#!/usr/bin/env python3
"""
Test the correct import method for python-socketio
"""

print("Testing correct socketio.Client import...\n")

try:
    import socketio
    
    # This should work because __getattr__ will lazily import it
    print("Attempting: socketio.Client")
    Client = socketio.Client
    print(f"✅ Success! Got Client: {Client}")
    
    # Try to create an instance
    print("\nCreating client instance...")
    client = Client(logger=False, engineio_logger=False)
    print(f"✅ Success! Client instance created: {type(client)}")
    print(f"   Has connect: {hasattr(client, 'connect')}")
    print(f"   Has emit: {hasattr(client, 'emit')}")
    print(f"   Has on: {hasattr(client, 'on')}")
    print(f"   Has disconnect: {hasattr(client, 'disconnect')}")
    
    print("\n✅✅✅ SOLUTION FOUND: Use 'import socketio' then 'socketio.Client()' ✅✅✅")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
