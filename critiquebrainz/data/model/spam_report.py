from critiquebrainz.data import db
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class SpamReport(db.Model):
    __tablename__ = 'spam_report'

    user_id = db.Column(UUID, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    revision_id = db.Column(db.Integer, db.ForeignKey('revision.id', ondelete='CASCADE'), primary_key=True)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def create(cls, revision_id, user):
        report = cls(user=user, revision_id=revision_id)
        db.session.add(report)
        db.session.commit()
        return report

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self