from parlpy.mps.mp_fetcher import MPOverview
import json


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=2)
    print(text)


mp = MPOverview()
# mp.get_active_MPs(verbose=True)
mp.get_all_members(params={"IsCurrentMember": True, "House": "Commons", "skip": 620}, verbose=True)

print(mp.mp_overview_data)
