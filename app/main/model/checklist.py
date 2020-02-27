from app.main import db

class CheckList(db.Model):
   __tablename__ = "checklist"

   id = db.Column(db.Integer, primary_key=True, autoincrement=True)
   title = db.Column(db.String(200), nullable=False)

