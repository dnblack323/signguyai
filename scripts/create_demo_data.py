#!/usr/bin/env python3
"""
Comprehensive demo data creation script for SignGuy AI
Creates: customers, orders, job tickets, invoices, appointments, employees, webstores
"""
import requests
import json
import uuid
from datetime import datetime, timezone, timedelta

API_URL = "https://sign-shop-checkout.preview.emergentagent.com"
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"

results = {
    "customers": [],
    "orders": [],
    "job_tickets": [],
    "invoices": [],
    "appointments": [],
    "employees": [],
    "webstores": [],
    "pricing_captured": [],
    "errors": []
}

def login():
    r = requests.post(f"{API_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    return r.json()["access_token"]

def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def tomorrow_str():
    return (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

def this_week_str():
    return (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")

def overdue_str():
    return (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")

def get_price(token, payload):
    """Call pricing API and return selling price"""
    try:
        r = requests.post(f"{API_URL}/api/pricing/calculate", headers=headers(token), json=payload, timeout=15)
        if r.status_code == 200:
            d = r.json()
            return float(d.get("selling_price", d.get("final_price", 0)) or 0)
    except Exception as e:
        print(f"  Pricing error: {e}")
    return 0.0

def create_customer(token, name, company, email, phone, city, state, notes=""):
    payload = {
        "name": name,
        "company": company,
        "email": email,
        "phone": phone,
        "city": city,
        "state": state,
        "notes": notes,
        "demo_data": True
    }
    r = requests.post(f"{API_URL}/api/customers", headers=headers(token), json=payload)
    if r.status_code == 200:
        d = r.json()
        results["customers"].append({"name": name, "id": d.get("id"), "email": email})
        print(f"  [OK] Customer: {name} -> {d.get('id','?')[:8]}")
        return d
    else:
        err = f"Customer {name}: {r.status_code} {r.text[:100]}"
        results["errors"].append(err)
        print(f"  [ERR] {err}")
        return None

def create_order(token, customer, title, status="new_intake", due_date=None, notes=""):
    cust_id = customer.get("id") if customer else None
    cust_name = customer.get("name", "Unknown") if customer else "Unknown"
    email = customer.get("email", "") if customer else ""
    payload = {
        "customer_id": cust_id,
        "customer_name": cust_name,
        "email": email,
        "order_title": title,
        "status": "new_intake",  # always start as new_intake per API rule
        "requested_due_date": due_date or this_week_str(),
        "internal_notes": notes,
        "pickup_delivery_method": "pickup",
        "demo_data": True
    }
    r = requests.post(f"{API_URL}/api/orders", headers=headers(token), json=payload)
    if r.status_code == 200:
        d = r.json()
        order_id = d.get("id")
        # Now update to target status if different from new_intake
        if status and status != "new_intake":
            r2 = requests.put(f"{API_URL}/api/orders/{order_id}", headers=headers(token), json={"status": status})
            if r2.status_code == 200:
                d = r2.json()
        results["orders"].append({"order_number": d.get("order_number"), "title": title, "id": d.get("id"), "customer": cust_name})
        print(f"  [OK] Order: {d.get('order_number')} - {title} ({d.get('status')}) -> {d.get('id','?')[:8]}")
        return d
    else:
        err = f"Order {title}: {r.status_code} {r.text[:200]}"
        results["errors"].append(err)
        print(f"  [ERR] {err}")
        return None

def create_ticket(token, order, item_name, category, quantity, specs, price_override=None, due_date=None, notes="", production_flow=True):
    order_id = order.get("id")
    payload = {
        "order_id": order_id,
        "item_name": item_name,
        "item_category": category,
        "quantity": quantity,
        "specs": specs,
        "estimated_price": price_override or 0,
        "due_date": due_date or this_week_str(),
        "special_instructions": notes,
        "production_flow_enabled": production_flow,
        "proof_required": True,
        "demo_data": True
    }
    r = requests.post(f"{API_URL}/api/job-tickets", headers=headers(token), json=payload)
    if r.status_code == 200:
        d = r.json()
        results["job_tickets"].append({"id": d.get("id"), "item": item_name, "price": price_override or 0})
        print(f"    [OK] Ticket: {item_name} @ ${price_override or 0:.2f} -> {d.get('id','?')[:8]}")
        return d
    else:
        err = f"Ticket {item_name}: {r.status_code} {r.text[:200]}"
        results["errors"].append(err)
        print(f"    [ERR] {err}")
        return None

def generate_invoice(token, order_id):
    r = requests.post(f"{API_URL}/api/orders/{order_id}/generate-invoice", headers=headers(token))
    if r.status_code == 200:
        return r.json()
    return None

def update_invoice(token, invoice_id, updates):
    r = requests.put(f"{API_URL}/api/invoices/{invoice_id}", headers=headers(token), json=updates)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"    [WARN] Invoice update {invoice_id[:8]}: {r.status_code} {r.text[:100]}")
        return None

def create_appointment(token, customer, title, appt_type, date_str, time_str, notes="", employee_id=None):
    cust_id = customer.get("id") if customer else None
    cust_name = customer.get("name", "Customer") if customer else "Customer"
    payload = {
        "customer_id": cust_id,
        "customer_name": cust_name,
        "title": title,
        "appointment_type": appt_type,
        "date": date_str,
        "time": time_str,
        "duration_minutes": 60,
        "notes": notes,
        "status": "confirmed",
        "demo_data": True
    }
    if employee_id:
        payload["employee_id"] = employee_id
    r = requests.post(f"{API_URL}/api/appointments", headers=headers(token), json=payload)
    if r.status_code == 200:
        d = r.json()
        results["appointments"].append({"id": d.get("id"), "title": title, "date": date_str})
        print(f"  [OK] Appointment: {title} on {date_str} {time_str}")
        return d
    else:
        err = f"Appointment {title}: {r.status_code} {r.text[:100]}"
        results["errors"].append(err)
        print(f"  [ERR] {err}")
        return None

def create_employee(token, name, title, role, hourly_rate, pin):
    payload = {
        "name": name,
        "title": title,
        "role": role,
        "hourly_rate": hourly_rate,
        "overtime_rate": round(hourly_rate * 1.5, 2),
        "pin": pin,
        "is_active": True,
        "demo_data": True
    }
    r = requests.post(f"{API_URL}/api/employees", headers=headers(token), json=payload)
    if r.status_code == 200:
        d = r.json()
        results["employees"].append({"id": d.get("id"), "name": name, "role": role})
        print(f"  [OK] Employee: {name} ({role}) -> {d.get('id','?')[:8]}")
        return d
    else:
        err = f"Employee {name}: {r.status_code} {r.text[:100]}"
        results["errors"].append(err)
        print(f"  [ERR] {err}")
        return None

def create_timeclock_entry(token, employee_id, clock_in_minutes_ago, clock_out_minutes_ago=None):
    now = datetime.now(timezone.utc)
    clock_in = (now - timedelta(minutes=clock_in_minutes_ago)).isoformat()
    clock_out = (now - timedelta(minutes=clock_out_minutes_ago)).isoformat() if clock_out_minutes_ago else None
    
    r = requests.post(f"{API_URL}/api/timeclock/admin-entry", 
        headers=headers(token),
        json={"employee_id": employee_id, "clock_in": clock_in, "clock_out": clock_out, "demo_data": True})
    if r.status_code == 200:
        print(f"  [OK] Timeclock entry for {employee_id[:8]}")
        return r.json()
    else:
        # Try alternate endpoint
        r2 = requests.post(f"{API_URL}/api/employees/{employee_id}/timeclock/punch",
            headers=headers(token),
            json={"action": "clock_in", "demo_data": True})
        if r2.status_code == 200:
            print(f"  [OK] Clocked in {employee_id[:8]}")
            return r2.json()
        print(f"  [WARN] Timeclock {employee_id[:8]}: {r.status_code}")
    return None

def create_webstore(token, name, store_type, description, owner_email=None, owner_name=None, extra_fields=None):
    payload = {
        "name": name,
        "store_type": store_type,
        "description": description,
        "status": "active",
        "owner_name": owner_name or "DEMO Store Owner",
        "owner_email": owner_email or "",
        "demo_data": True
    }
    if extra_fields:
        payload.update(extra_fields)
    
    r = requests.post(f"{API_URL}/api/webstores/v2", headers=headers(token), json=payload)
    if r.status_code == 200:
        d = r.json()
        results["webstores"].append({"id": d.get("id"), "name": name, "type": store_type})
        print(f"  [OK] Webstore: {name} ({store_type}) -> {d.get('id','?')[:8]}")
        return d
    else:
        err = f"Webstore {name}: {r.status_code} {r.text[:200]}"
        results["errors"].append(err)
        print(f"  [ERR] {err}")
        return None

def main():
    print("\n=== SIGNGUY AI - DEMO DATA CREATION ===\n")
    token = login()
    print(f"[OK] Logged in as {ADMIN_EMAIL}\n")

    # =========================================================
    # STEP 1: CREATE CUSTOMERS
    # =========================================================
    print("--- CREATING DEMO CUSTOMERS ---")
    customers = {}

    customers["champion_bakery"] = create_customer(token,
        "DEMO - Champion Bakery", "Champion Bakery",
        "champion@champbakery.example", "724-555-0101", "Connellsville", "PA",
        "Local bakery, frequent sign orders. Seasonal banners and window graphics.")

    customers["miller_plumbing"] = create_customer(token,
        "DEMO - Miller Plumbing", "Miller Plumbing & HVAC",
        "office@millerplumbing.example", "724-555-0202", "Uniontown", "PA",
        "Fleet vehicle graphics. 3 service vans. Repeat customer.")

    customers["lh_racing"] = create_customer(token,
        "DEMO - Laurel Highlands Racing", "Laurel Highlands Motorsports",
        "team@lhracing.example", "724-555-0303", "Farmington", "PA",
        "Race team. Trailer wraps, helmet graphics, pit crew apparel.")

    customers["cyf"] = create_customer(token,
        "DEMO - Connellsville Youth Football", "Connellsville Youth Football Assoc.",
        "director@cyfootball.example", "724-555-0404", "Connellsville", "PA",
        "Youth football league. Yard signs, banners, and spirit wear every season.")

    customers["abc_mfg"] = create_customer(token,
        "DEMO - ABC Manufacturing", "ABC Manufacturing Inc.",
        "marketing@abcmfg.example", "724-555-0505", "Brownsville", "PA",
        "Industrial signage, safety signs, door plaques.")

    customers["johnson_dinner"] = create_customer(token,
        "DEMO - Johnson Benefit Dinner", "Johnson Family Foundation",
        "event@johnsonfoundation.example", "724-555-0606", "Uniontown", "PA",
        "Annual benefit dinner fundraiser. Needs event signage and table banners.")

    customers["mountain_church"] = create_customer(token,
        "DEMO - Mountain View Church", "Mountain View Community Church",
        "office@mountainviewchurch.example", "724-555-0707", "Hopwood", "PA",
        "Church. Yard signs, banners, event shirts, webstore for congregation.")

    customers["rr_landscape"] = create_customer(token,
        "DEMO - R&R Landscaping", "R&R Landscaping Services",
        "info@rrlandscaping.example", "724-555-0808", "Normalville", "PA",
        "Landscaping company. Truck decals, yard signs, and business cards.")

    customers["smith_reunion"] = create_customer(token,
        "DEMO - Smith Family Reunion", "Smith Family Reunion Committee",
        "committee@smithreunion.example", "724-555-0909", "Connellsville", "PA",
        "Annual family reunion. Yard signs, t-shirts, and custom items.")

    customers["patriot_auto"] = create_customer(token,
        "DEMO - Patriot Auto Sales", "Patriot Auto Sales LLC",
        "sales@patriotauto.example", "724-555-1010", "Connellsville", "PA",
        "Used car dealership. Window lettering, price stickers, lot signage.")

    print(f"\n[DONE] Created {len(results['customers'])} customers\n")

    # =========================================================
    # STEP 2: PRICING CALCULATIONS
    # =========================================================
    print("--- CALCULATING PRICES ---")

    # Yard Signs: 18x24, qty 50
    price_yard_signs = get_price(token, {
        "category": "rigid_signs",
        "width_inches": 18, "length_inches": 24,
        "quantity": 50,
        "substrate_type_key": "coroplast_4mm",
        "graphic_method": "direct_print",
        "hardware_included": True,
        "hardware_type": "hw-h-stake"
    })
    if price_yard_signs == 0: price_yard_signs = 375.00
    results["pricing_captured"].append({"item": "50x Yard Signs 18x24", "price": price_yard_signs})
    print(f"  Yard Signs (50x 18x24): ${price_yard_signs:.2f}")

    # Banner: 4x8 (48x96), 13oz
    price_banner = get_price(token, {
        "category": "banners",
        "width_inches": 96, "length_inches": 48,
        "quantity": 1,
        "banner_material_key": "banner_13oz",
        "banner_hems": "standard",
        "banner_grommets": "corners"
    })
    if price_banner == 0: price_banner = 87.50
    results["pricing_captured"].append({"item": "4x8 Banner 13oz", "price": price_banner})
    print(f"  4x8 Banner 13oz w/ hems+grommets: ${price_banner:.2f}")

    # Rigid Sign: 4x8 ACM
    price_rigid = get_price(token, {
        "category": "rigid_signs",
        "width_inches": 48, "length_inches": 96,
        "quantity": 1,
        "substrate_type_key": "acm_dibond_3mm",
        "graphic_method": "direct_print"
    })
    if price_rigid == 0: price_rigid = 320.00
    results["pricing_captured"].append({"item": "4x8 ACM Rigid Sign", "price": price_rigid})
    print(f"  4x8 ACM Rigid Sign: ${price_rigid:.2f}")

    # Digital Print: 24x36 adhesive vinyl decals x4
    price_digital = get_price(token, {
        "category": "digital_print",
        "width_inches": 24, "length_inches": 36,
        "quantity": 4,
        "print_media_key": "printable_adhesive_vinyl",
        "use_type": "outdoor",
        "laminate": True
    })
    if price_digital == 0: price_digital = 180.00
    results["pricing_captured"].append({"item": "Digital Print Decals 24x36 x4", "price": price_digital})
    print(f"  Digital Print Decals 24x36 x4: ${price_digital:.2f}")

    # Cut Vinyl: 36x72 storefront lettering
    price_vinyl = get_price(token, {
        "category": "cut_vinyl",
        "width_inches": 72, "length_inches": 36,
        "quantity": 1,
        "vinyl_type_key": "oracal_651",
        "use_type": "glass_window",
        "num_colors": 2,
        "masking_required": True
    })
    if price_vinyl == 0: price_vinyl = 145.00
    results["pricing_captured"].append({"item": "Cut Vinyl Storefront Lettering 36x72", "price": price_vinyl})
    print(f"  Cut Vinyl Storefront Lettering: ${price_vinyl:.2f}")

    # Vehicle Graphics: Van door decals
    price_vehicle = get_price(token, {
        "category": "vehicle_graphics",
        "vehicle_type": "van_cargo",
        "coverage_type": "spot",
        "quantity": 1
    })
    if price_vehicle == 0: price_vehicle = 480.00
    results["pricing_captured"].append({"item": "Van Door Decals (partial)", "price": price_vehicle})
    print(f"  Vehicle Graphics Van Door Decals: ${price_vehicle:.2f}")

    # Apparel: 24 shirts HTV
    price_apparel = get_price(token, {
        "category": "apparel",
        "quantity": 24,
        "apparel_product_type": "short_sleeve_tee",
        "apparel_decoration_method": "htv",
        "apparel_placement_set": "front",
        "apparel_num_colors": 2,
        "size_s": 4, "size_m": 8, "size_l": 8, "size_xl": 4
    })
    if price_apparel == 0: price_apparel = 528.00
    results["pricing_captured"].append({"item": "24x Church T-Shirts HTV", "price": price_apparel})
    print(f"  Apparel 24x Shirts: ${price_apparel:.2f}")

    # Wrap: Race trailer (full wrap)
    price_wrap = get_price(token, {
        "category": "vehicle_graphics",
        "vehicle_type": "trailer",
        "coverage_type": "full",
        "quantity": 1,
        "wrap_laminate_required": True
    })
    if price_wrap == 0: price_wrap = 3200.00
    results["pricing_captured"].append({"item": "Race Trailer Full Wrap", "price": price_wrap})
    print(f"  Race Trailer Full Wrap: ${price_wrap:.2f}")

    # Quick: 10 yard signs
    price_quick_signs = get_price(token, {
        "category": "rigid_signs",
        "width_inches": 18, "length_inches": 24,
        "quantity": 10,
        "substrate_type_key": "coroplast_4mm",
        "hardware_included": True, "hardware_type": "hw-h-stake"
    })
    if price_quick_signs == 0: price_quick_signs = 95.00
    results["pricing_captured"].append({"item": "10x Yard Signs 18x24 Quick", "price": price_quick_signs})
    print(f"  Quick 10x Yard Signs: ${price_quick_signs:.2f}")

    # Quick: 3x6 banner
    price_quick_banner = get_price(token, {
        "category": "banners",
        "width_inches": 72, "length_inches": 36,
        "quantity": 1,
        "banner_material_key": "banner_13oz",
        "banner_hems": "standard",
        "banner_grommets": "corners"
    })
    if price_quick_banner == 0: price_quick_banner = 65.00
    results["pricing_captured"].append({"item": "3x6 Banner 13oz Quick", "price": price_quick_banner})
    print(f"  Quick 3x6 Banner: ${price_quick_banner:.2f}")

    print()

    # =========================================================
    # STEP 3: CREATE ORDERS + JOB TICKETS
    # =========================================================
    print("--- CREATING DEMO ORDERS ---")
    order_ids_for_invoices = []

    # ORDER 1: Yard Signs - Connellsville Youth Football
    print("\n[1] Yard Signs - Connellsville Youth Football")
    if customers.get("cyf"):
        ord1 = create_order(token, customers["cyf"],
            "50 Yard Signs - CYF Season 2026",
            status="in_progress",
            due_date=this_week_str(),
            notes="50 yard signs for football season. 18x24 with H-stakes. Print ready artwork.")
        if ord1:
            t1 = create_ticket(token, ord1,
                "18x24 Yard Signs with H-Stakes",
                "rigid_signs", 50,
                {
                    "width": 18, "height": 24, "unit_of_measure": "inches",
                    "substrate_type_key": "coroplast_4mm", "thickness": "4mm",
                    "graphic_method": "direct_print",
                    "hardware_included": True, "hardware_type": "hw-h-stake",
                    "artwork_ready": True, "design_complexity": "simple",
                    "rush_order": False
                },
                price_override=price_yard_signs,
                due_date=this_week_str(),
                notes="50 standard CYF yard signs. H-stakes included. Customer providing artwork file."
            )
            order_ids_for_invoices.append({"order_id": ord1["id"], "purpose": "overdue_invoice", "customer_name": "DEMO - Connellsville Youth Football"})

    # ORDER 2: Banner - Champion Bakery
    print("\n[2] 4x8 Banner - Champion Bakery")
    if customers.get("champion_bakery"):
        ord2 = create_order(token, customers["champion_bakery"],
            "4x8 Grand Opening Banner",
            status="awaiting_approval",
            due_date=tomorrow_str(),
            notes="Grand opening banner for new location. 13oz outdoor vinyl, hems and grommets.")
        if ord2:
            t2 = create_ticket(token, ord2,
                "4x8 13oz Outdoor Banner - Hems & Grommets",
                "banners", 1,
                {
                    "width": 8, "height": 4, "unit_of_measure": "feet",
                    "banner_material_key": "banner_13oz",
                    "banner_use_type": "outdoor",
                    "banner_hems": "standard",
                    "banner_grommets": "corners",
                    "banner_double_sided": "no",
                    "artwork_ready": False, "artwork_needed": True,
                    "design_complexity": "simple",
                    "rush_order": False
                },
                price_override=price_banner,
                due_date=tomorrow_str(),
                notes="Grand Opening - Champion Bakery. Logo + address on banner. Design proof required."
            )
            order_ids_for_invoices.append({"order_id": ord2["id"], "purpose": "pending_invoice", "customer_name": "DEMO - Champion Bakery"})

    # ORDER 3: Rigid Sign - ABC Manufacturing
    print("\n[3] Rigid Sign - ABC Manufacturing")
    if customers.get("abc_mfg"):
        ord3 = create_order(token, customers["abc_mfg"],
            "4x8 ACM Entrance Sign",
            status="in_production",
            due_date=this_week_str(),
            notes="Main entrance sign. 4x8 aluminum composite, direct print.")
        if ord3:
            t3 = create_ticket(token, ord3,
                "4x8 ACM/Dibond Directional Sign",
                "rigid_signs", 1,
                {
                    "width": 48, "height": 96, "unit_of_measure": "inches",
                    "substrate_type_key": "acm_dibond_3mm",
                    "graphic_method": "direct_print",
                    "protective_finish": True,
                    "protective_finish_type": "rigid_finish_standard",
                    "shape_type": "rectangle",
                    "finish_quality": "standard",
                    "hardware_included": True, "hardware_type": "hw-standoff",
                    "drill_prep_required": True,
                    "artwork_ready": True, "design_complexity": "medium"
                },
                price_override=price_rigid,
                due_date=this_week_str()
            )
            order_ids_for_invoices.append({"order_id": ord3["id"], "purpose": "paid_invoice", "customer_name": "DEMO - ABC Manufacturing"})

    # ORDER 4: Digital Print - R&R Landscaping
    print("\n[4] Digital Print Decals - R&R Landscaping")
    if customers.get("rr_landscape"):
        ord4 = create_order(token, customers["rr_landscape"],
            "Truck Door Decals - 4 vehicles",
            status="awaiting_approval",
            due_date=this_week_str(),
            notes="4 sets of truck door decals for service fleet. 24x36 per door.")
        if ord4:
            t4 = create_ticket(token, ord4,
                "24x36 Truck Door Decals - Laminated",
                "digital_print", 4,
                {
                    "width": 24, "height": 36, "unit_of_measure": "inches",
                    "print_media_key": "printable_adhesive_vinyl",
                    "use_type": "outdoor",
                    "print_quality_mode": "high",
                    "ink_coverage_percent": 60,
                    "laminate": True,
                    "laminate_material_key": "laminate_gloss",
                    "contour_cut_type": "none",
                    "artwork_ready": False, "artwork_needed": True,
                    "design_complexity": "medium"
                },
                price_override=price_digital,
                due_date=this_week_str(),
                notes="R&R Landscaping logo + phone number on door decals. Customer supplying logo."
            )
            order_ids_for_invoices.append({"order_id": ord4["id"], "purpose": "pending_invoice", "customer_name": "DEMO - R&R Landscaping"})

    # ORDER 5: Cut Vinyl - Patriot Auto Sales
    print("\n[5] Cut Vinyl - Patriot Auto Sales")
    if customers.get("patriot_auto"):
        ord5 = create_order(token, customers["patriot_auto"],
            "Showroom Window Lettering",
            status="awaiting_quote",
            due_date=this_week_str(),
            notes="Front window lettering: name, phone, hours. Oracal 651 white vinyl.")
        if ord5:
            t5 = create_ticket(token, ord5,
                "Showroom Window Lettering - Oracal 651",
                "cut_vinyl", 1,
                {
                    "width": 72, "height": 36, "unit_of_measure": "inches",
                    "vinyl_type_key": "oracal_651",
                    "num_colors": 2,
                    "weeding_complexity": "medium",
                    "masking_required": True,
                    "use_type": "glass_window",
                    "surface_type": "glass_window",
                    "artwork_needed": True, "design_complexity": "simple",
                    "install_required": True, "install_complexity": "easy"
                },
                price_override=price_vinyl,
                due_date=this_week_str(),
                notes="White vinyl lettering - hours, name, phone. Install included."
            )
            order_ids_for_invoices.append({"order_id": ord5["id"], "purpose": "overdue_invoice", "customer_name": "DEMO - Patriot Auto Sales"})

    # ORDER 6: Vehicle Graphics - Miller Plumbing
    print("\n[6] Vehicle Graphics - Miller Plumbing")
    if customers.get("miller_plumbing"):
        ord6 = create_order(token, customers["miller_plumbing"],
            "Service Van Door Graphics - 2026",
            status="in_progress",
            due_date=this_week_str(),
            notes="Full spot graphics for cargo van doors. Vehicle drops off today.")
        if ord6:
            t6 = create_ticket(token, ord6,
                "Cargo Van Door Decals - Spot Graphics",
                "vehicle_wrap", 1,
                {
                    "vehicle_type": "van_cargo",
                    "coverage_type": "spot",
                    "coverage_percent": 25,
                    "wrap_material_key": "oracal_751",
                    "wrap_laminate_required": False,
                    "surface_prep_level": "basic",
                    "install_difficulty_level": "easy",
                    "artwork_ready": False, "artwork_needed": True,
                    "design_complexity": "medium"
                },
                price_override=price_vehicle,
                due_date=this_week_str(),
                notes="Miller Plumbing van door graphics. Logo + phone number + tagline. Vehicle drop-off today."
            )
            order_ids_for_invoices.append({"order_id": ord6["id"], "purpose": "pending_invoice", "customer_name": "DEMO - Miller Plumbing"})

    # ORDER 7: Apparel - Mountain View Church
    print("\n[7] Apparel - Mountain View Church")
    if customers.get("mountain_church"):
        ord7 = create_order(token, customers["mountain_church"],
            "24 Spirit Shirts - Mountain View Church",
            status="awaiting_approval",
            due_date=this_week_str(),
            notes="24 church spirit shirts. White HTV on black shirts. 2 color front print.")
        if ord7:
            t7 = create_ticket(token, ord7,
                "24x Church Spirit Shirts - HTV 2-Color",
                "apparel", 24,
                {
                    "apparel_product_type": "short_sleeve_tee",
                    "apparel_garment_color": "Black",
                    "apparel_decoration_method": "htv",
                    "apparel_placement_set": "front",
                    "apparel_num_colors": 2,
                    "size_s": 4, "size_m": 8, "size_l": 8, "size_xl": 4,
                    "artwork_needed": True, "design_complexity": "simple",
                    "rush_order": False
                },
                price_override=price_apparel,
                due_date=this_week_str(),
                notes="Church logo on front. Adult sizes S-XL. Customer approving design first."
            )
            order_ids_for_invoices.append({"order_id": ord7["id"], "purpose": "paid_invoice", "customer_name": "DEMO - Mountain View Church"})

    # ORDER 8: Wrap/Vehicle - Laurel Highlands Racing
    print("\n[8] Race Trailer Wrap - Laurel Highlands Racing")
    if customers.get("lh_racing"):
        ord8 = create_order(token, customers["lh_racing"],
            "Race Trailer Full Wrap - 2026 Season",
            status="in_progress",
            due_date=this_week_str(),
            notes="Full wrap on race trailer. Sponsor graphics, team colors, number board. Wrap Command Center job.")
        if ord8:
            t8 = create_ticket(token, ord8,
                "Race Trailer Full Wrap - Sponsor Graphics",
                "vehicle_wrap", 1,
                {
                    "vehicle_type": "trailer",
                    "coverage_type": "full",
                    "coverage_percent": 100,
                    "wrap_material_key": "oracal_951",
                    "wrap_laminate_required": True,
                    "wrap_laminate_type_key": "laminate_matte",
                    "surface_prep_level": "basic",
                    "install_difficulty_level": "medium",
                    "second_installer_required": True,
                    "artwork_ready": False, "artwork_needed": True,
                    "design_complexity": "complex"
                },
                price_override=price_wrap,
                due_date=this_week_str(),
                notes="2026 season race trailer wrap. Full wrap with sponsor logos, team name, car number. Matte laminate."
            )
            order_ids_for_invoices.append({"order_id": ord8["id"], "purpose": "pending_invoice", "customer_name": "DEMO - Laurel Highlands Racing"})

    # ORDER 9: Event Order - Johnson Benefit Dinner
    print("\n[9] Event Signage - Johnson Benefit Dinner")
    if customers.get("johnson_dinner"):
        ord9 = create_order(token, customers["johnson_dinner"],
            "Annual Benefit Dinner Signage Package",
            status="awaiting_quote",
            due_date=this_week_str(),
            notes="Event signage package for annual benefit dinner. Multiple items.")
        if ord9:
            # Table tent signs
            price_event_signs = get_price(token, {
                "category": "rigid_signs",
                "width_inches": 11, "length_inches": 17,
                "quantity": 20,
                "substrate_type_key": "foamboard_3_16",
                "graphic_method": "direct_print"
            }) or 220.00
            
            t9a = create_ticket(token, ord9,
                "Table Tent Signs - 11x17 Foamboard",
                "rigid_signs", 20,
                {
                    "width": 11, "height": 17, "unit_of_measure": "inches",
                    "substrate_type_key": "foamboard_3_16",
                    "graphic_method": "direct_print",
                    "shape_type": "rectangle",
                    "artwork_needed": True, "design_complexity": "simple"
                },
                price_override=price_event_signs,
                notes="20 table tent signs for benefit dinner tables."
            )
            
            # Event banner
            price_event_banner = get_price(token, {
                "category": "banners",
                "width_inches": 96, "length_inches": 48,
                "quantity": 1,
                "banner_material_key": "banner_13oz",
                "banner_event_premium": True
            }) or 110.00
            
            t9b = create_ticket(token, ord9,
                "4x8 Welcome Banner - Event Premium",
                "banners", 1,
                {
                    "width": 8, "height": 4, "unit_of_measure": "feet",
                    "banner_material_key": "banner_13oz",
                    "banner_hems": "standard",
                    "banner_grommets": "corners",
                    "banner_event_premium": True,
                    "artwork_needed": True
                },
                price_override=price_event_banner,
                notes="Welcome banner for event entrance."
            )
            results["pricing_captured"].append({"item": "Event Signage Package (20 table signs + banner)", "price": price_event_signs + price_event_banner})
            order_ids_for_invoices.append({"order_id": ord9["id"], "purpose": "pending_invoice", "customer_name": "DEMO - Johnson Benefit Dinner"})

    # ORDER 10: QUICK - 10 Yard Signs for Smith Family Reunion
    print("\n[10] QUICK - 10 Yard Signs - Smith Family Reunion")
    if customers.get("smith_reunion"):
        ord10 = create_order(token, customers["smith_reunion"],
            "10 Yard Signs - Smith Reunion 2026",
            status="new_intake",
            due_date=this_week_str(),
            notes="Quick order: 10 yard signs for family reunion directional signage.")
        if ord10:
            t10 = create_ticket(token, ord10,
                "18x24 Yard Signs - Reunion Directional",
                "rigid_signs", 10,
                {
                    "width": 18, "height": 24, "unit_of_measure": "inches",
                    "substrate_type_key": "coroplast_4mm",
                    "hardware_included": True, "hardware_type": "hw-h-stake",
                    "artwork_needed": True, "design_complexity": "simple"
                },
                price_override=price_quick_signs
            )
            order_ids_for_invoices.append({"order_id": ord10["id"], "purpose": "no_invoice", "customer_name": "DEMO - Smith Family Reunion"})

    # ORDER 11: QUICK - 3x6 Banner for Champion Bakery (2nd order)
    print("\n[11] QUICK - 3x6 Banner - Champion Bakery (2nd)")
    if customers.get("champion_bakery"):
        ord11 = create_order(token, customers["champion_bakery"],
            "3x6 Daily Specials Banner",
            status="new_intake",
            due_date=tomorrow_str(),
            notes="Quick: 3x6 banner for daily specials board in window.")
        if ord11:
            t11 = create_ticket(token, ord11,
                "3x6 Indoor Banner - Daily Specials",
                "banners", 1,
                {
                    "width": 6, "height": 3, "unit_of_measure": "feet",
                    "banner_material_key": "banner_13oz",
                    "banner_use_type": "indoor",
                    "banner_hems": "standard",
                    "banner_grommets": "none",
                    "artwork_needed": True, "design_complexity": "simple"
                },
                price_override=price_quick_banner
            )
            order_ids_for_invoices.append({"order_id": ord11["id"], "purpose": "no_invoice", "customer_name": "DEMO - Champion Bakery (Banner 2)"})

    print(f"\n[DONE] Created {len(results['orders'])} orders, {len(results['job_tickets'])} tickets\n")

    # =========================================================
    # STEP 4: CREATE INVOICES
    # =========================================================
    print("--- CREATING DEMO INVOICES ---")

    inv_count = {"pending": 0, "overdue": 0, "paid": 0, "deposit": 0}
    invoice_purposes = {
        "pending_invoice": [],
        "overdue_invoice": [],
        "paid_invoice": [],
    }

    for item in order_ids_for_invoices:
        purpose = item.get("purpose")
        if purpose == "no_invoice":
            continue
        order_id = item["order_id"]
        
        inv = generate_invoice(token, order_id)
        if not inv:
            print(f"  [WARN] Could not generate invoice for order {order_id[:8]}")
            continue
        
        inv_id = inv.get("id")
        cust_name = item["customer_name"]
        
        if purpose == "paid_invoice" and inv_count["paid"] < 2:
            # Mark as paid today
            update_invoice(token, inv_id, {
                "status": "paid",
                "amount_paid": inv.get("grand_total", 0),
                "payment_date": today_str(),
                "payment_method": "card"
            })
            inv_count["paid"] += 1
            print(f"  [OK] PAID invoice for {cust_name}: ${inv.get('grand_total', 0):.2f}")
            results["invoices"].append({"id": inv_id, "status": "paid", "customer": cust_name, "total": inv.get("grand_total", 0)})
            
        elif purpose == "overdue_invoice" and inv_count["overdue"] < 2:
            update_invoice(token, inv_id, {
                "status": "overdue",
                "due_date": overdue_str()
            })
            inv_count["overdue"] += 1
            print(f"  [OK] OVERDUE invoice for {cust_name}: ${inv.get('grand_total', 0):.2f}")
            results["invoices"].append({"id": inv_id, "status": "overdue", "customer": cust_name, "total": inv.get("grand_total", 0)})
            
        elif purpose == "pending_invoice" and inv_count["pending"] < 3:
            update_invoice(token, inv_id, {
                "status": "sent",
                "due_date": this_week_str()
            })
            inv_count["pending"] += 1
            print(f"  [OK] PENDING/SENT invoice for {cust_name}: ${inv.get('grand_total', 0):.2f}")
            results["invoices"].append({"id": inv_id, "status": "sent", "customer": cust_name, "total": inv.get("grand_total", 0)})
        else:
            # Remainder as drafts
            results["invoices"].append({"id": inv_id, "status": "draft", "customer": cust_name, "total": inv.get("grand_total", 0)})

    # Create a partial/deposit invoice manually
    if customers.get("lh_racing"):
        inv_deposit = generate_invoice(token, order_ids_for_invoices[7]["order_id"] if len(order_ids_for_invoices) > 7 else "")
        if inv_deposit:
            wrap_total = inv_deposit.get("grand_total", 3200)
            update_invoice(token, inv_deposit["id"], {
                "status": "partial",
                "amount_paid": round(wrap_total * 0.5, 2),
                "deposit_required": True,
                "deposit_percent": 50,
                "due_date": this_week_str()
            })
            inv_count["deposit"] += 1
            print(f"  [OK] PARTIAL/DEPOSIT invoice for Laurel Highlands Racing: 50% of ${wrap_total:.2f}")
            results["invoices"].append({"id": inv_deposit["id"], "status": "partial", "customer": "DEMO - Laurel Highlands Racing", "total": wrap_total})

    print(f"\n[DONE] Invoices: {inv_count['paid']} paid, {inv_count['overdue']} overdue, {inv_count['pending']} pending, {inv_count['deposit']} deposit\n")

    # =========================================================
    # STEP 5: CREATE APPOINTMENTS (TODAY)
    # =========================================================
    print("--- CREATING DEMO APPOINTMENTS (TODAY) ---")
    
    if customers.get("miller_plumbing"):
        create_appointment(token, customers["miller_plumbing"],
            "Miller Plumbing Van Drop-Off",
            "drop_off", today_str(), "09:00",
            "Vehicle drop-off for van door decal installation. Check paint condition.")

    if customers.get("champion_bakery"):
        create_appointment(token, customers["champion_bakery"],
            "Champion Bakery Banner Production Review",
            "production", today_str(), "10:00",
            "Review banner proof and confirm sizes before printing.")

    if customers.get("cyf"):
        create_appointment(token, customers["cyf"],
            "CYF Yard Sign Printing - Production",
            "production", today_str(), "11:00",
            "Print run for 50 yard signs. Materials staged.")

    if customers.get("abc_mfg"):
        create_appointment(token, customers["abc_mfg"],
            "ABC Mfg Sign Installation",
            "install", today_str(), "13:00",
            "Install 4x8 entrance sign at ABC Manufacturing facility. Bring ladder + hardware.")

    if customers.get("patriot_auto"):
        create_appointment(token, customers["patriot_auto"],
            "Patriot Auto - Customer Pickup",
            "pickup", today_str(), "14:00",
            "Customer picking up window lettering order.")

    if customers.get("rr_landscape"):
        create_appointment(token, customers["rr_landscape"],
            "R&R Landscaping Design Review",
            "design_review", today_str(), "15:30",
            "Review truck decal designs with customer before going to print.")

    print(f"\n[DONE] Created {len(results['appointments'])} appointments\n")

    # =========================================================
    # STEP 6: CREATE DEMO EMPLOYEES
    # =========================================================
    print("--- CREATING DEMO EMPLOYEES ---")

    emp_nicole = create_employee(token, "DEMO - Nicole Manager", "Shop Manager", "manager", 22.00, "1001")
    emp_gabe = create_employee(token, "DEMO - Gabe Production", "Production Specialist", "staff", 18.00, "1002")
    emp_keith = create_employee(token, "DEMO - Keith Installer", "Installer", "staff", 20.00, "1003")
    emp_bill = create_employee(token, "DEMO - Bill Owner", "Owner / Operations", "owner", 35.00, "1004")

    # Try to clock in Gabe (production, currently working)
    if emp_gabe:
        create_timeclock_entry(token, emp_gabe["id"], clock_in_minutes_ago=90)
        print(f"  [OK] Gabe clocked in 90 minutes ago")

    print(f"\n[DONE] Created {len(results['employees'])} employees\n")

    # =========================================================
    # STEP 7: CREATE DEMO WEBSTORES
    # =========================================================
    print("--- CREATING DEMO WEBSTORES ---")

    # 1. Creator Store - Laurel Highlands Racing
    ws1 = create_webstore(token,
        "DEMO - Laurel Highlands Racing Gear",
        "creator",
        "Official gear store for Laurel Highlands Motorsports. Hats, shirts, and decals.",
        owner_email="team@lhracing.example",
        owner_name="Laurel Highlands Racing"
    )

    # 2. Business Store - Champion Bakery
    ws2 = create_webstore(token,
        "DEMO - Champion Bakery Branded Merch",
        "business",
        "Champion Bakery branded merchandise and catering sign packages.",
        owner_email="champion@champbakery.example",
        owner_name="Champion Bakery"
    )

    # 3. Fundraiser Store - Mountain View Church
    ws3 = create_webstore(token,
        "DEMO - Mountain View Church Fundraiser",
        "fundraiser",
        "Fundraiser store to support church building fund.",
        owner_email="office@mountainviewchurch.example",
        owner_name="Mountain View Community Church",
        extra_fields={
            "fundraiser_enabled": True,
            "fundraiser_name": "New Fellowship Hall Fund",
            "fundraiser_description": "Help us raise funds for our new fellowship hall expansion.",
            "fundraiser_goal_amount": 5000.00,
            "show_progress_bar": True,
            "allow_checkout_donations": True,
            "donation_amount_options": "5,10,25,50",
            "allow_custom_donation": True
        }
    )

    # 4. Event Store - Johnson Benefit Dinner
    ws4 = create_webstore(token,
        "DEMO - Johnson Benefit Dinner Store",
        "event",
        "Official event store for the Johnson Family Annual Benefit Dinner 2026.",
        owner_email="event@johnsonfoundation.example",
        owner_name="Johnson Family Foundation",
        extra_fields={
            "event_name": "Johnson Family Annual Benefit Dinner",
            "event_type": "fundraiser_dinner",
            "event_start_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
            "event_end_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
            "event_location": "Uniontown Community Center, Uniontown PA",
            "order_deadline": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d"),
            "fundraiser_enabled": True,
            "fundraiser_name": "Johnson Family Scholarship Fund",
            "fundraiser_description": "Proceeds go directly to the Johnson Family Scholarship Fund for local students.",
            "fundraiser_goal_amount": 10000.00,
            "show_progress_bar": True,
            "allow_checkout_donations": True,
            "donation_amount_options": "10,25,50,100",
            "allow_custom_donation": True,
            "profit_allocation_enabled": True,
            "profit_allocation_type": "percentage",
            "profit_allocation_percentage": 50.0,
            "show_total_raised_publicly": True,
            "show_supporter_names": "yes_all",
            "include_donations_in_progress": True,
            "include_profit_allocation_in_progress": True,
            "locked_settings": {
                "shipping_fee": 5.00,
                "handling_fee": 2.00,
                "shipping_handling_enabled": True,
                "shipping_handling_fee": 7.00,
                "shipping_handling_label": "Event Handling Fee"
            }
        }
    )

    print(f"\n[DONE] Created {len(results['webstores'])} webstores\n")

    # =========================================================
    # FINAL REPORT
    # =========================================================
    print("\n" + "=" * 60)
    print("DEMO DATA CREATION COMPLETE - SUMMARY REPORT")
    print("=" * 60)
    
    print(f"\nCUSTOMERS CREATED: {len(results['customers'])}")
    for c in results["customers"]:
        print(f"  - {c['name']} ({c['email']})")
    
    print(f"\nORDERS CREATED: {len(results['orders'])}")
    for o in results["orders"]:
        print(f"  - {o['order_number']} | {o['title']} | Customer: {o['customer']}")

    print(f"\nPRICING CAPTURED:")
    total_captured = 0
    for p in results["pricing_captured"]:
        print(f"  - {p['item']}: ${p['price']:.2f}")
        total_captured += p['price']
    print(f"  TOTAL VALUE: ${total_captured:.2f}")

    print(f"\nINVOICES CREATED: {len(results['invoices'])}")
    paid_rev = 0
    for i in results["invoices"]:
        print(f"  - {i['status'].upper()} | {i['customer']} | ${i.get('total',0):.2f}")
        if i['status'] == 'paid':
            paid_rev += i.get('total', 0)
    print(f"  TODAY'S REVENUE (paid invoices): ${paid_rev:.2f}")

    print(f"\nAPPOINTMENTS CREATED: {len(results['appointments'])}")
    for a in results["appointments"]:
        print(f"  - {a['title']} on {a['date']}")

    print(f"\nEMPLOYEES CREATED: {len(results['employees'])}")
    for e in results["employees"]:
        print(f"  - {e['name']} ({e['role']})")

    print(f"\nWEBSTORES CREATED: {len(results['webstores'])}")
    for w in results["webstores"]:
        print(f"  - {w['name']} ({w['type']})")

    if results["errors"]:
        print(f"\nERRORS ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"  [ERR] {err}")
    else:
        print("\nNo errors encountered.")

    # Save report
    with open("/app/scripts/demo_data_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\n[SAVED] Report: /app/scripts/demo_data_report.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
