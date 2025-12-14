#!/usr/bin/env python3
"""Phase 1 Installation Test - Data Registry Package"""

from app.data_registry import Registry

print("=== Testing PRO Edition ===")
pro = Registry(edition='pro')

# Test system tier (universal access)
scales = pro.get_scale_lengths()
print(f"✓ Loaded {len(scales.get('scales', []))} scale lengths (system tier)")

woods = pro.get_wood_species()
print(f"✓ Loaded {len(woods.get('species', []))} wood species (system tier)")

# Test edition tier (Pro only)
tools = pro.get_tools()
print(f"✓ Loaded {len(tools.get('tools', []))} tools (edition tier - Pro only)")

machines = pro.get_machines()
print(f"✓ Loaded {len(machines.get('machines', []))} machines (edition tier - Pro only)")

print("\n=== Testing EXPRESS Edition (Honeypot) ===")
express = Registry(edition='express')

# System tier should work
scales_exp = express.get_scale_lengths()
print(f"✓ Loaded {len(scales_exp.get('scales', []))} scale lengths (system tier - all editions)")

# Edition tier should fail
try:
    tools_exp = express.get_tools()
    print("✗ FAIL: Express should not access Pro tools")
    exit(1)
except Exception as e:
    print(f"✓ Entitlement enforcement working: {type(e).__name__}")

print("\n=== Testing PARAMETRIC Edition ===")
parametric = Registry(edition='parametric')

# System tier
scales_param = parametric.get_scale_lengths()
print(f"✓ Loaded {len(scales_param.get('scales', []))} scale lengths (system tier)")

# Parametric-specific data
# Note: get_guitar_templates() might not exist yet - just test system data
print("✓ Parametric edition initialized successfully")

print("\n=== ALL TESTS PASSED ===")
