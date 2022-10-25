import json

import sqlalchemy
from flask import Flask, make_response
from flask_cors import CORS
from flask_restful import Resource, Api, fields, marshal_with, HTTPException, reqparse
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.app_context().push()


class CustomError(HTTPException):
    def __init__(self, status_code, message):
        self.response = make_response(message, status_code)


class CourseValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)


class Student(db.Model):
    __tablename__ = "student"
    student_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)


class Course(db.Model):
    __tablename__ = "course"
    course_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)


class Enrollments(db.Model):
    __tablename__ = "enrollments"
    enrollment_id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    estudent_id = db.Column(db.Integer, db.ForeignKey(
        "student.student_id"), nullable=False, )
    ecourse_id = db.Column(db.Integer, db.ForeignKey(
        "course.course_id"), nullable=False, )


class StudentAPI(Resource):
    def get(self, sid):
        sid = int(sid)
        print("This method called")
        student = Student.query.filter(Student.student_id == sid).first()
        enrollments = Enrollments.query.filter(
            Enrollments.estudent_id == sid).all()
        course_ids = [i.ecourse_id for i in enrollments]
        course_list = []
        for index, cid in enumerate(course_ids):
            course = Course.query.filter(Course.course_id == cid).first()
            course_list.append([index + 1, course.course_code,
                                course.course_name, course.course_description])
        return {"name": student.first_name}


course_output = {
    "course_id": fields.Integer,
    "course_name": fields.String,
    "course_code": fields.String,
    "course_description": fields.String
}

create_course_parser = reqparse.RequestParser()
create_course_parser.add_argument("course_name")
create_course_parser.add_argument("course_code")
create_course_parser.add_argument("course_description")


class CourseAPI(Resource):

    @marshal_with(course_output)
    def get(self, cid):
        try:
            course = Course.query.filter(Course.course_id == cid).first()
        except Exception:
            raise CustomError(500, "")
        if course is None:
            raise CustomError(404, "")
        else:
            return course

    @marshal_with(course_output)
    def post(self):
        args = create_course_parser.parse_args()
        course_name = args.get("course_name", None)
        course_code = args.get("course_code", None)
        course_description = args.get("course_description", None)
        if course_name is None:
            raise CourseValidationError(400, "COURSE001", "Course Name is required")
        if course_code is None:
            raise CourseValidationError(400, "COURSE002", "Course Code is required")
        try:
            course = Course(course_code=course_code, course_name=course_name, course_description=course_description)
            db.session.add(course)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            raise CustomError(409, "Course_code already exist")
        except Exception as e:
            print(e)
            raise CustomError(500, "")
        return course, 201

    def delete(self, cid):
        course = Course.query.filter(Course.course_id == cid).first()
        if not course:
            return "Course not found", 404
        try:
            Course.query.filter(Course.course_id == cid).delete()
            Enrollments.query.filter(Enrollments.ecourse_id == cid).delete()
            db.session.commit()
            return "Successfully Deleted", 200
        except Exception as e:
            raise CustomError(500, "Internal server error")

    @marshal_with(course_output)
    def put(self, cid):
        course = Course.query.filter(Course.course_id == cid).first()
        if not course:
            raise CustomError(404, "Course not found")
        args = create_course_parser.parse_args()
        course_name = args.get("course_name", None)
        course_code = args.get("course_code", None)
        course_description = args.get("course_description", None)
        if course_name is None:
            raise CourseValidationError(400, "COURSE001", "Course Name is required")
        if course_code is None:
            raise CourseValidationError(400, "COURSE002", "Course Code is required")
        try:
            Course.query.filter(Course.course_id == cid).update(
                {"course_code": course_code, "course_name": course_name, "course_description": course_description})
            db.session.add(course)
            db.session.commit()
            course = Course.query.filter(Course.course_id == cid).first()
        except Exception as e:
            raise CustomError(500, "Internal server error")
        return course, 201


api.add_resource(StudentAPI, "/api/student", "/api/student/<string:sid>")
api.add_resource(CourseAPI, "/api/course", "/api/course/<string:cid>")

if __name__ == "__main__":
    app.run(debug=True)
