import os

CORE_FILE = "app/engine/core.py"

SAFE_OVERRIDE_FUNC = """
def apply_simulation_overrides(scenario, overrides):
    if not overrides: return
    
    # Pre-fetch maps to avoid iteration overhead
    strategy_map = {s.id: s for s in scenario.decumulation_strategies}
    account_map = {a.id: a for a in scenario.accounts}
    
    for o in overrides:
        try:
            # Value casting safety
            val = o.value
            
            if o.type == 'decumulation_strategy':
                if o.id in strategy_map:
                    strat = strategy_map[o.id]
                    if hasattr(strat, o.field):
                        # Explicitly cast boolean for 'enabled'
                        if o.field == 'enabled':
                            val = bool(val)
                        setattr(strat, o.field, val)
                        
            elif o.type == 'account':
                if o.id in account_map:
                    acc = account_map[o.id]
                    if hasattr(acc, o.field):
                        setattr(acc, o.field, val)
                        
            elif o.type == 'income' or o.type == 'income_source':
                # Search owners (less efficient but fine for overrides)
                found = False
                for owner in scenario.owners:
                    for inc in owner.income_sources:
                        if inc.id == o.id:
                            if hasattr(inc, o.field):
                                setattr(inc, o.field, val)
                            found = True
                            break
                    if found: break
        except Exception as e:
            print(f"Override Error: {e}")
"""

with open(CORE_FILE, 'r') as f:
    content = f.read()

# Replace the old function or append the new one
if "def apply_simulation_overrides" in content:
    # We will do a somewhat dirty replace by finding the start and assuming structure, 
    # OR simpler: just overwrite the file with known good content if we had it.
    # Since we don't, let's append the SAFE version as 'apply_safe_overrides' 
    # and update the call site.
    
    content += "\n" + SAFE_OVERRIDE_FUNC.replace("apply_simulation_overrides", "apply_safe_overrides")
    content = content.replace("apply_simulation_overrides(scenario, context.overrides)", "apply_safe_overrides(scenario, context.overrides)")
else:
    # Does not exist? append and add call
    content += "\n" + SAFE_OVERRIDE_FUNC
    if "context = ProjectionContext" in content:
        content = content.replace("context = ProjectionContext(scenario, months)", "context = ProjectionContext(scenario, months)\n    apply_simulation_overrides(scenario, context.overrides)")

with open(CORE_FILE, 'w') as f:
    f.write(content)

print("Engine Core patched.")
