from datetime import datetime
from app.extensions import db


class HeritageSite(db.Model):
    __tablename__ = "heritage_sites"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(100))
    historical_significance = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="active")
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "state": self.state,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "image_url": self.image_url,
            "category": self.category,
            "historical_significance": self.historical_significance,
            "status": self.status,
            "admin_id": self.admin_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
