from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.extensions import db
from app.models import HeritageSite, Contribution, Feedback, User

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def admin_required():
    """Return True only when the authenticated JWT contains the admin role."""
    return get_jwt().get("role") == "admin"


def admin_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def admin_denied():
    return jsonify({"success": False, "message": "Admin access required"}), 403


def get_json_body():
    return request.get_json(silent=True) or {}


@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    if not admin_required():
        return admin_denied()

    data = {
        "total_sites": HeritageSite.query.count(),
        "active_sites": HeritageSite.query.filter_by(status="active").count(),
        "total_users": User.query.count(),
        "pending_contributions": Contribution.query.filter_by(status="pending").count(),
        "approved_contributions": Contribution.query.filter_by(status="approved").count(),
        "rejected_contributions": Contribution.query.filter_by(status="rejected").count(),
        "total_feedback": Feedback.query.count(),
    }
    return jsonify({"success": True, "data": data}), 200


@admin_bp.route("/heritage", methods=["POST"])
@jwt_required()
def add_heritage():
    if not admin_required():
        return admin_denied()

    data = get_json_body()
    required = ("name", "description", "location", "state")
    missing = [field for field in required if not isinstance(data.get(field), str) or not data[field].strip()]
    if missing:
        return jsonify({"success": False, "message": "Required fields: " + ", ".join(missing)}), 400

    admin_id = admin_user_id()
    if admin_id is None:
        return jsonify({"success": False, "message": "Invalid admin identity in token"}), 401

    site = HeritageSite(
        name=data["name"].strip(),
        description=data["description"].strip(),
        location=data["location"].strip(),
        state=data["state"].strip(),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        image_url=data.get("image_url"),
        category=data.get("category"),
        historical_significance=data.get("historical_significance"),
        status=data.get("status", "active"),
        admin_id=admin_id,
    )
    db.session.add(site)
    db.session.commit()
    return jsonify({"success": True, "message": "Heritage site added successfully", "data": site.to_dict()}), 201


@admin_bp.route("/heritage", methods=["GET"])
@jwt_required()
def get_heritage():
    if not admin_required():
        return admin_denied()
    sites = HeritageSite.query.order_by(HeritageSite.id.desc()).all()
    return jsonify({"success": True, "count": len(sites), "data": [site.to_dict() for site in sites]}), 200


@admin_bp.route("/heritage/<int:site_id>", methods=["GET"])
@jwt_required()
def get_heritage_by_id(site_id):
    if not admin_required():
        return admin_denied()
    site = db.session.get(HeritageSite, site_id)
    if site is None:
        return jsonify({"success": False, "message": "Heritage site not found"}), 404
    return jsonify({"success": True, "data": site.to_dict()}), 200


@admin_bp.route("/heritage/<int:site_id>", methods=["PUT"])
@jwt_required()
def update_heritage(site_id):
    if not admin_required():
        return admin_denied()
    site = db.session.get(HeritageSite, site_id)
    if site is None:
        return jsonify({"success": False, "message": "Heritage site not found"}), 404

    data = get_json_body()
    allowed_fields = (
        "name", "description", "location", "state", "latitude", "longitude",
        "image_url", "category", "historical_significance", "status",
    )
    for field in allowed_fields:
        if field in data:
            value = data[field]
            if field in ("name", "description", "location", "state"):
                if not isinstance(value, str) or not value.strip():
                    return jsonify({"success": False, "message": f"{field} cannot be empty"}), 400
                value = value.strip()
            setattr(site, field, value)

    db.session.commit()
    return jsonify({"success": True, "message": "Heritage site updated successfully", "data": site.to_dict()}), 200


@admin_bp.route("/heritage/<int:site_id>", methods=["DELETE"])
@jwt_required()
def delete_heritage(site_id):
    if not admin_required():
        return admin_denied()
    site = db.session.get(HeritageSite, site_id)
    if site is None:
        return jsonify({"success": False, "message": "Heritage site not found"}), 404

    # Keep contribution history while removing the optional site reference.
    Contribution.query.filter_by(heritage_site_id=site.id).update({"heritage_site_id": None})
    db.session.delete(site)
    db.session.commit()
    return jsonify({"success": True, "message": "Heritage site deleted successfully"}), 200


@admin_bp.route("/contributions", methods=["GET"])
@jwt_required()
def get_contributions():
    if not admin_required():
        return admin_denied()
    status = request.args.get("status")
    query = Contribution.query
    if status:
        if status not in ("pending", "approved", "rejected"):
            return jsonify({"success": False, "message": "Invalid status filter"}), 400
        query = query.filter_by(status=status)
    contributions = query.order_by(Contribution.created_at.desc()).all()
    return jsonify({"success": True, "count": len(contributions), "data": [item.to_dict() for item in contributions]}), 200


@admin_bp.route("/contributions/<int:contribution_id>/approve", methods=["PUT"])
@jwt_required()
def approve_contribution(contribution_id):
    if not admin_required():
        return admin_denied()
    contribution = db.session.get(Contribution, contribution_id)
    if contribution is None:
        return jsonify({"success": False, "message": "Contribution not found"}), 404
    if contribution.status != "pending":
        return jsonify({"success": False, "message": "Only pending contributions can be approved"}), 400

    data = get_json_body()
    # Contributions only store title and description. Admin supplies the site location/state at approval.
    required = ("location", "state")
    missing = [field for field in required if not isinstance(data.get(field), str) or not data[field].strip()]
    if missing:
        return jsonify({
            "success": False,
            "message": "To publish this contribution, provide: " + ", ".join(missing),
            "required_fields": list(missing),
        }), 400

    admin_id = admin_user_id()
    if admin_id is None:
        return jsonify({"success": False, "message": "Invalid admin identity in token"}), 401

    duplicate = HeritageSite.query.filter(db.func.lower(HeritageSite.name) == contribution.title.strip().lower()).first()
    if duplicate:
        return jsonify({"success": False, "message": "A heritage site with this name already exists"}), 409

    site = HeritageSite(
        name=contribution.title.strip(),
        description=contribution.description,
        location=data["location"].strip(),
        state=data["state"].strip(),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        image_url=data.get("image_url"),
        category=data.get("category"),
        historical_significance=data.get("historical_significance"),
        status="active",
        admin_id=admin_id,
    )
    db.session.add(site)
    db.session.flush()

    contribution.status = "approved"
    contribution.heritage_site_id = site.id
    contribution.admin_remark = data.get("remark")
    contribution.reviewed_by = admin_id
    contribution.reviewed_at = datetime.utcnow()

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Contribution approved and heritage site published",
        "data": {"contribution": contribution.to_dict(), "heritage_site": site.to_dict()},
    }), 200


@admin_bp.route("/contributions/<int:contribution_id>/reject", methods=["PUT"])
@jwt_required()
def reject_contribution(contribution_id):
    if not admin_required():
        return admin_denied()
    contribution = db.session.get(Contribution, contribution_id)
    if contribution is None:
        return jsonify({"success": False, "message": "Contribution not found"}), 404
    if contribution.status != "pending":
        return jsonify({"success": False, "message": "Only pending contributions can be rejected"}), 400

    data = get_json_body()
    admin_id = admin_user_id()
    if admin_id is None:
        return jsonify({"success": False, "message": "Invalid admin identity in token"}), 401

    contribution.status = "rejected"
    contribution.admin_remark = data.get("remark")
    contribution.reviewed_by = admin_id
    contribution.reviewed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "message": "Contribution rejected successfully", "data": contribution.to_dict()}), 200


@admin_bp.route("/feedback", methods=["GET"])
@jwt_required()
def get_feedback():
    if not admin_required():
        return admin_denied()
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return jsonify({"success": True, "count": len(feedbacks), "data": [item.to_dict() for item in feedbacks]}), 200


@admin_bp.route("/feedback/<int:feedback_id>", methods=["DELETE"])
@jwt_required()
def delete_feedback(feedback_id):
    if not admin_required():
        return admin_denied()
    feedback = db.session.get(Feedback, feedback_id)
    if feedback is None:
        return jsonify({"success": False, "message": "Feedback not found"}), 404
    db.session.delete(feedback)
    db.session.commit()
    return jsonify({"success": True, "message": "Feedback deleted successfully"}), 200
