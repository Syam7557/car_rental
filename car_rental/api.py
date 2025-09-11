import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def search_vehicles(q=None):
    """
    Public endpoint used by the homepage JS.
    Returns simple list of active vehicles with base_rate and a sample image.
    """
    filters = {'is_active': 1}
    # Basic fuzzy search on make/model/location
    if q:
        q_term = "%{}%".format(q)
        vehicles = frappe.db.sql("""
            SELECT name, make, model, year, transmission, seats, fuel_type, base_rate, location,
                   (SELECT file_url FROM `tabFile` WHERE attached_to_doctype='Vehicle' AND attached_to_name=v.name LIMIT 1) as image
            FROM `tabVehicle` v
            WHERE v.is_active=1 AND (v.make LIKE %(q)s OR v.model LIKE %(q)s OR v.location LIKE %(q)s)
            LIMIT 50
        """, {"q": q_term}, as_dict=True)
    else:
        vehicles = frappe.db.sql("""
            SELECT name, make, model, year, transmission, seats, fuel_type, base_rate, location,
                   (SELECT file_url FROM `tabFile` WHERE attached_to_doctype='Vehicle' AND attached_to_name=v.name LIMIT 1) as image
            FROM `tabVehicle` v
            WHERE v.is_active=1
            LIMIT 50
        """, as_dict=True)

    # normalize fields for frontend
    out = []
    for v in vehicles:
        out.append({
            "name": v.name,
            "make": v.make or "",
            "model": v.model or "",
            "year": v.year or "",
            "transmission": v.transmission or "",
            "seats": v.seats or "",
            "fuel_type": v.fuel_type or "",
            "base_rate": float(v.base_rate or 0),
            "location": v.location or "",
            "image": v.image or "/assets/car-placeholder.png"
        })
    return out


@frappe.whitelist()
def create_booking(vehicle, start, end, pickup_location=None, dropoff_location=None):
    """
    Create a simple Booking document (Draft). Requires login.
    This is intentionally minimal: production must check user, availability, and race conditions.
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.AuthenticationError)

    # validate times
    try:
        start_dt = frappe.utils.get_datetime(start)
        end_dt = frappe.utils.get_datetime(end)
    except Exception:
        frappe.throw(_("Invalid date format. Use YYYY-MM-DD or a valid datetime."))

    if end_dt <= start_dt:
        frappe.throw(_("End date must be after start date."))

    # naive conflict check
    conflict = frappe.db.exists("Booking", {
        "vehicle": vehicle,
        "status": ["!=", "Cancelled"],
        "start_datetime": ["<", end_dt],
        "end_datetime": [">", start_dt]
    })
    if conflict:
        frappe.throw(_("Vehicle not available for selected range."))

    booking = frappe.get_doc({
        "doctype": "Booking",
        "vehicle": vehicle,
        "start_datetime": start_dt,
        "end_datetime": end_dt,
        "pickup_location": pickup_location or "",
        "dropoff_location": dropoff_location or "",
        "user": frappe.session.user,
        "status": "Draft"
    })
    booking.insert()
    frappe.db.commit()
    return booking.name