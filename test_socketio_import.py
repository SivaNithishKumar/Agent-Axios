#!/usr/bin/env python3
"""
Test script to find the correct way to import python-socketio Client
"""

print("Testing python-socketio imports...\n")

# Test 1: Direct import
print("Test 1: import socketio")
try:
    import socketio
    print(f"✅ Success! socketio module loaded")
    print(f"   Available attributes: {[attr for attr in dir(socketio) if not attr.startswith('_')][:10]}")
    
    # Check for Client
    if hasattr(socketio, 'Client'):
        print(f"   ✅ socketio.Client exists!")
    else:
        print(f"   ❌ socketio.Client does NOT exist")
        print(f"   Looking for Client-like classes...")
        client_attrs = [attr for attr in dir(socketio) if 'client' in attr.lower()]
        print(f"   Found: {client_attrs}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 2: SimpleClient
print("Test 2: from socketio import SimpleClient")
try:
    from socketio import SimpleClient
    print(f"✅ Success! SimpleClient imported")
    print(f"   SimpleClient type: {type(SimpleClient)}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Direct from simple_client module
print("Test 3: from socketio.simple_client import SimpleClient")
try:
    from socketio.simple_client import SimpleClient as SC
    print(f"✅ Success! SimpleClient imported directly")
    print(f"   SimpleClient type: {type(SC)}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 4: Check package structure
print("Test 4: Inspecting socketio package structure")
try:
    import socketio
    import os
    import socketio as sio_module
    
    package_path = os.path.dirname(sio_module.__file__)
    print(f"Package location: {package_path}")
    
    if os.path.exists(package_path):
        files = os.listdir(package_path)
        print(f"\nFiles in package:")
        for f in sorted(files):
            if f.endswith('.py'):
                print(f"   - {f}")
    
    # Check __init__.py content
    init_file = os.path.join(package_path, '__init__.py')
    if os.path.exists(init_file):
        print(f"\n__init__.py exists, checking content...")
        with open(init_file, 'r') as f:
            content = f.read()
            print(f"   Size: {len(content)} bytes")
            if 'Client' in content:
                print(f"   ✅ 'Client' found in __init__.py")
            else:
                print(f"   ❌ 'Client' NOT found in __init__.py")
    else:
        print(f"\n❌ __init__.py does NOT exist (namespace package)")
        
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 5: Try to instantiate a client
print("Test 5: Try to create a client instance")
try:
    from socketio.simple_client import SimpleClient
    client = SimpleClient(logger=False, engineio_logger=False)
    print(f"✅ Success! SimpleClient instance created")
    print(f"   Instance type: {type(client)}")
    print(f"   Has connect method: {hasattr(client, 'connect')}")
    print(f"   Has emit method: {hasattr(client, 'emit')}")
    print(f"   Has on method: {hasattr(client, 'on')}")
    
    # Clean up
    try:
        client.disconnect()
    except:
        pass
    
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
print("Testing complete!")
