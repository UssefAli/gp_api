from enum import Enum



class SkillName(str , Enum):
    tiers_and_wheels = "tiers and wheels"
    Interior = "Interior"
    Glass = "Glass"
    Paint_and_Finish = "Paint & Finish"
    Body_Work = "Body Work"
    Preventive_Maintenance = "Preventive Maintenance" 
    Diagnostics = "Diagnostics"
    CLIMATE_CONTROL = "CLIMATE CONTROL"
    Drivetrain = "Drivetrain"
    Manual_Transmission = "Manual Transmission" 
    Automatic_Transmission = "Automatic Transmission"
    Suspension_and_Steering = "Suspension & Steering"
    Brake_Systems = "Brake Systems"
    Lighting_and_Accessories = "Lighting & Accessories"
    Computer_and_Sensors = "Computer & Sensors"
    Battery_and_Charging = "Battery & Charging"
    Cooling_System = "Cooling System"
    Exhaust_System = "Exhaust System"
    Fuel_System = "Fuel System"
    Core_Engine_Repair = "Core Engine Repair"
    Other = "Other"

class Status(str , Enum):
    accepted = "Accepted"
    completed = "Completed"
    pending = "Pending"
    canceled_user = "Canceled by User"
    canceled_mechanic = "Canceled by Mechanic"

def swagger_responses(
    *,
    success_message: dict,
    access_role : str,
    unauthorized: bool = True,
    forbidden: bool = True,
    validation: bool = False,
    not_found: bool = False,
    bad_request_message: str | None = None,
):
    responses = {
        200: {
            "description": "",
            "content": {
                "application/json": {
                    "example": success_message
                }
            },
        }
    }

    if unauthorized:
        responses[401] = {
            "description": "Unauthnticated",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized"
                    }
                }
            },
        }

    if forbidden:
        responses[403] = {
            "description": "",
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"{access_role} access required"
                    }
                }
            },
        }

    if bad_request_message:
        responses[400] = {
            "description": "",
            "content": {
                "application/json": {
                    "example": {
                        "detail": bad_request_message
                    }
                }
            },
        }

    if not_found:
        responses[404] = {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
                    }
                }
            },
        }

    if validation:
        responses[422] = {
            "description": "Validation error",
        }

    responses[500] = {
        "description": "Internal server error",
    }

    return responses