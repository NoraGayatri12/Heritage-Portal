from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import HeritageSite, Contribution, Feedback

public_bp = Blueprint("public", __name__, url_prefix="/api")


@public_bp.route("/heritage", methods=["GET"])
def public_heritage():
    sites = HeritageSite.query.filter_by(status="active").order_by(HeritageSite.name.asc()).all()
    return jsonify({"success": True, "count": len(sites), "data": [site.to_dict() for site in sites]}), 200


@public_bp.route("/heritage/<int:site_id>", methods=["GET"])
def heritage_details(site_id):
    site = HeritageSite.query.filter_by(id=site_id, status="active").first()
    if site is None:
        return jsonify({"success": False, "message": "Heritage site not found"}), 404
    return jsonify({"success": True, "data": site.to_dict()}), 200


@public_bp.route("/contributions", methods=["POST"])
@jwt_required()
def submit_contribution():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    description = data.get("description")
    if not isinstance(title, str) or not title.strip() or not isinstance(description, str) or not description.strip():
        return jsonify({"success": False, "message": "Title and description are required"}), 400

    contribution = Contribution(
        user_id=int(get_jwt_identity()),
        title=title.strip(),
        description=description.strip(),
        status="pending",
    )
    db.session.add(contribution)
    db.session.commit()
    return jsonify({"success": True, "message": "Contribution submitted for review", "data": contribution.to_dict()}), 201


@public_bp.route("/feedback", methods=["POST"])
@jwt_required()
def submit_feedback():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")
    rating = data.get("rating")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"success": False, "message": "Message is required"}), 400
    if rating is not None and (not isinstance(rating, int) or isinstance(rating, bool) or not 1 <= rating <= 5):
        return jsonify({"success": False, "message": "Rating must be an integer between 1 and 5"}), 400

    feedback = Feedback(
        user_id=int(get_jwt_identity()),
        name=name.strip() if isinstance(name, str) and name.strip() else None,
        email=email.strip().lower() if isinstance(email, str) and email.strip() else None,
        message=message.strip(),
        rating=rating,
    )
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"success": True, "message": "Feedback submitted successfully", "data": feedback.to_dict()}), 201


@public_bp.route("/heritage/search", methods=["GET"])
def search_heritage():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "success": False,
            "message": "Search query is required"
        }), 400

    sites = HeritageSite.query.filter(
        HeritageSite.status == "active",
        db.or_(
            HeritageSite.name.ilike(f"%{query}%"),
            HeritageSite.location.ilike(f"%{query}%"),
            HeritageSite.state.ilike(f"%{query}%")
        )
    ).all()

    return jsonify({
        "success": True,
        "count": len(sites),
        "data": [site.to_dict() for site in sites]
    }), 200


@public_bp.route("/heritage/filter", methods=["GET"])
def filter_heritage():

    category = request.args.get("category", "").strip()
    state = request.args.get("state", "").strip()

    query = HeritageSite.query.filter_by(status="active")

    if category:
        query = query.filter(
            HeritageSite.category.ilike(f"%{category}%")
        )

    if state:
        query = query.filter(
            HeritageSite.state.ilike(f"%{state}%")
        )

    sites = query.all()

    return jsonify({
        "success": True,
        "count": len(sites),
        "data": [site.to_dict() for site in sites]
    }), 200



@public_bp.route("/contributions/my", methods=["GET"])
@jwt_required()
def my_contributions():

    user_id = int(get_jwt_identity())

    contributions = Contribution.query.filter_by(
        user_id=user_id
    ).order_by(Contribution.created_at.desc()).all()

    return jsonify({
        "success": True,
        "count": len(contributions),
        "data": [contribution.to_dict() for contribution in contributions]
    }), 200