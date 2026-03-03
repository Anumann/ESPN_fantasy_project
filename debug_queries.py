import sys
import os

# Add the directory to sys.path so we can import queries
sys.path.append(os.path.join(os.getcwd(), 'espn-fantasy-project/dashboard'))

try:
    import queries
except ImportError:
    # Try alternate path if running from inside espn-fantasy-project
    sys.path.append(os.path.join(os.getcwd(), 'dashboard'))
    import queries

owners = queries.get_all_owners()
print(f"Found {len(owners)} owners.")

for owner in owners:
    print(f"Testing profile for: {owner}")
    try:
        profile = queries.get_owner_profile(owner)
        if profile is None:
            print(f"  -> Profile is None")
            continue
            
        rivalries = profile['rivalries']
        print(f"  -> Rivalries shape: {rivalries.shape}")
        if not rivalries.empty:
            # Try accessing the column to ensure it exists
            print(f"  -> Top rival: {rivalries.iloc[0]['opponent']} ({rivalries.iloc[0]['win_pct']:.3f})")
            
    except Exception as e:
        print(f"  -> CRASH: {e}")
        import traceback
        traceback.print_exc()
