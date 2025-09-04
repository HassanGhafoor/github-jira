# app/models.py
from datetime import datetime
from .extensions import db

class WebhookLog(db.Model):
    __tablename__ = "webhook_logs"

    id = db.Column(db.Integer, primary_key=True)
    source_event = db.Column(db.String(64), nullable=False)
    delivery_id = db.Column(db.String(128), nullable=True)
    ticket_key = db.Column(db.String(64), nullable=True)
    payload = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WebhookLog id={self.id} event={self.source_event} ticket={self.ticket_key}>"

