"""
ACEest Fitness & Gym - Flask Web Application
DevOps Assignment 1 - CI/CD Pipeline Implementation
"""

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# ── In-memory data store ──────────────────────────────────────────────────────

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": (
            "Mon: Back Squat 5x5 + Core\n"
            "Tue: EMOM 20min Assault Bike\n"
            "Wed: Bench Press + 21-15-9\n"
            "Thu: Deadlift + Box Jumps\n"
            "Fri: Zone 2 Cardio 30min"
        ),
        "diet": (
            "Breakfast: Egg Whites + Oats\n"
            "Lunch: Grilled Chicken + Brown Rice\n"
            "Dinner: Fish Curry + Millet Roti\n"
            "Target: ~2000 kcal"
        ),
        "calorie_factor": 22,
    },
    "Muscle Gain (MG)": {
        "workout": (
            "Mon: Squat 5x5\n"
            "Tue: Bench 5x5\n"
            "Wed: Deadlift 4x6\n"
            "Thu: Front Squat 4x8\n"
            "Fri: Incline Press 4x10\n"
            "Sat: Barbell Rows 4x10"
        ),
        "diet": (
            "Breakfast: Eggs + Peanut Butter Oats\n"
            "Lunch: Chicken Biryani\n"
            "Dinner: Mutton Curry + Rice\n"
            "Target: ~3200 kcal"
        ),
        "calorie_factor": 35,
    },
    "Beginner (BG)": {
        "workout": (
            "Full Body Circuit:\n"
            "- Air Squats\n"
            "- Ring Rows\n"
            "- Push-ups\n"
            "Focus: Technique & Consistency"
        ),
        "diet": (
            "Balanced Tamil Meals\n"
            "Idli / Dosa / Rice + Dal\n"
            "Protein Target: 120g/day"
        ),
        "calorie_factor": 26,
    },
}

# In-memory client store keyed by name
clients = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def calculate_calories(weight_kg, program_key):
    """Return estimated daily calories based on weight and program."""
    factor = PROGRAMS[program_key]["calorie_factor"]
    return int(weight_kg * factor)


def validate_client_payload(data):
    """Return a list of validation error strings (empty list = valid)."""
    errors = []
    if not data.get("name", "").strip():
        errors.append("name is required")
    if data.get("program") not in PROGRAMS:
        errors.append("program must be one of {}".format(list(PROGRAMS.keys())))
    weight = data.get("weight_kg")
    if weight is None or not isinstance(weight, (int, float)) or weight <= 0:
        errors.append("weight_kg must be a positive number")
    age = data.get("age")
    if age is None or not isinstance(age, int) or age <= 0:
        errors.append("age must be a positive integer")
    return errors


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "service": "ACEest Fitness & Gym API",
        "version": "3.2.4",
        "status": "running",
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/programs", methods=["GET"])
def get_programs():
    """List all available fitness programs."""
    return jsonify({"programs": list(PROGRAMS.keys())})


@app.route("/programs/<path:program_name>", methods=["GET"])
def get_program(program_name):
    """Return details for a specific program."""
    if program_name not in PROGRAMS:
        abort(404, description="Program '{}' not found".format(program_name))
    prog = PROGRAMS[program_name]
    return jsonify({
        "name": program_name,
        "workout": prog["workout"],
        "diet": prog["diet"],
        "calorie_factor": prog["calorie_factor"],
    })


@app.route("/clients", methods=["GET"])
def list_clients():
    """Return all registered clients."""
    return jsonify({"clients": list(clients.values())})


@app.route("/clients", methods=["POST"])
def create_client():
    """Register a new client and compute their daily calorie target."""
    data = request.get_json(force=True, silent=True) or {}
    errors = validate_client_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    name = data["name"].strip()
    program = data["program"]
    weight = float(data["weight_kg"])
    age = int(data["age"])
    calories = calculate_calories(weight, program)

    client_record = {
        "name": name,
        "age": age,
        "weight_kg": weight,
        "program": program,
        "calories_per_day": calories,
        "adherence_pct": data.get("adherence_pct", 0),
    }
    clients[name] = client_record
    return jsonify(client_record), 201


@app.route("/clients/<client_name>", methods=["GET"])
def get_client(client_name):
    """Fetch a single client by name."""
    if client_name not in clients:
        abort(404, description="Client '{}' not found".format(client_name))
    return jsonify(clients[client_name])


@app.route("/clients/<client_name>", methods=["PUT"])
def update_client(client_name):
    """Update an existing client record."""
    if client_name not in clients:
        abort(404, description="Client '{}' not found".format(client_name))
    data = request.get_json(force=True, silent=True) or {}
    merged = dict(clients[client_name])
    merged.update(data)
    errors = validate_client_payload(merged)
    if errors:
        return jsonify({"errors": errors}), 400

    clients[client_name].update(data)
    if "weight_kg" in data or "program" in data:
        clients[client_name]["calories_per_day"] = calculate_calories(
            clients[client_name]["weight_kg"],
            clients[client_name]["program"]
        )
    return jsonify(clients[client_name])


@app.route("/clients/<client_name>", methods=["DELETE"])
def delete_client(client_name):
    """Remove a client record."""
    if client_name not in clients:
        abort(404, description="Client '{}' not found".format(client_name))
    clients.pop(client_name)
    return jsonify({"message": "Client '{}' deleted".format(client_name)}), 200


@app.route("/clients/<client_name>/calories", methods=["GET"])
def client_calories(client_name):
    """Return calorie target for a specific client."""
    if client_name not in clients:
        abort(404, description="Client '{}' not found".format(client_name))
    record = clients[client_name]
    return jsonify({
        "name": client_name,
        "program": record["program"],
        "weight_kg": record["weight_kg"],
        "calories_per_day": record["calories_per_day"],
    })


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e)}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
