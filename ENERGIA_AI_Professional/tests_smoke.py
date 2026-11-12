from engine import analyse_building, diagnose_building, build_recommendations, estimate_savings, estimate_carbon

x = analyse_building(1200, 85000, 42000, 0, 21000,
                     building_type="bureaux", heating_type="gaz",
                     cooling_type="split", ventilation_type="double_flux",
                     lighting_type="LED", dhw_type="gaz", has_cooling=True,
                     has_ventilation=True, has_lighting=True, has_dhw=True,
                     meter_separation=True)
d = diagnose_building(x)
r = build_recommendations(x)
s = estimate_savings(x, r)
c = estimate_carbon(x)
assert x["total_kwh"] == 127000
assert d["modules"]["heating"]
assert c["total_kg"] > 0
print("OK", len(r), round(x["intensity"], 2), round(c["total_tonnes"], 2))
