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


class CustomValidationError(HTTPException):
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
    student_id = db.Column(db.Integer, db.ForeignKey(
        "student.student_id"), nullable=False, )
    course_id = db.Column(db.Integer, db.ForeignKey(
        "course.course_id"), nullable=False, )


course_output = {
    "course_id": fields.Integer,
    "course_name": fields.String,
    "course_code": fields.String,
    "course_description": fields.String
}
student_output = {
    "student_id": fields.Integer,
    "roll_number": fields.String,
    "first_name": fields.String,
    "last_name": fields.String
}

enrollment_output = {
    "enrollment_id": fields.Integer,
    "student_id": fields.Integer,
    "course_id": fields.Integer
}

create_course_parser = reqparse.RequestParser()
create_course_parser.add_argument("course_name")
create_course_parser.add_argument("course_code")
create_course_parser.add_argument("course_description")

create_student_parser = reqparse.RequestParser()
create_student_parser.add_argument("roll_number")
create_student_parser.add_argument("first_name")
create_student_parser.add_argument("last_name")

enrollment_parser = reqparse.RequestParser()
enrollment_parser.add_argument("course_id")


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
            raise CustomValidationError(400, "COURSE001", "Course Name is required")
        if course_code is None:
            raise CustomValidationError(400, "COURSE002", "Course Code is required")
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
            raise CustomValidationError(400, "COURSE001", "Course Name is required")
        if course_code is None:
            raise CustomValidationError(400, "COURSE002", "Course Code is required")
        try:
            Course.query.filter(Course.course_id == cid).update(
                {"course_code": course_code, "course_name": course_name, "course_description": course_description})
            db.session.add(course)
            db.session.commit()
            course = Course.query.filter(Course.course_id == cid).first()
        except Exception as e:
            raise CustomError(500, "Internal server error")
        return course, 201


class StudentAPI(Resource):
    @marshal_with(student_output)
    def get(self, sid):
        try:
            student = Student.query.filter(Student.student_id == sid).first()
        except Exception:
            raise CustomError(500, "")
        if student is None:
            raise CustomError(404, "")
        else:
            return student

    @marshal_with(student_output)
    def post(self):
        args = create_student_parser.parse_args()
        roll_number = args.get("roll_number", None)
        first_name = args.get("first_name", None)
        last_name = args.get("last_name", None)
        if roll_number is None:
            raise CustomValidationError(400, "STUDENT001", "Roll Number required")
        if first_name is None:
            raise CustomValidationError(400, "STUDENT002", "First Name is required")
        try:
            student = Student(roll_number=roll_number, first_name=first_name, last_name=last_name)
            db.session.add(student)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            raise CustomError(409, "Student already exist")
        except Exception as e:
            raise CustomError(500, "Internal Server Error")
        return student, 201

    def delete(self, sid):
        student = Student.query.filter(Student.student_id == sid).first()
        if not student:
            return "Student not found", 404
        try:
            Student.query.filter(Student.student_id == sid).delete()
            db.session.commit()
            return "Successfully Deleted", 200
        except Exception as e:
            raise CustomError(500, "Internal server error")

    @marshal_with(student_output)
    def put(self, sid):
        student = Student.query.filter(Student.student_id == sid).first()
        if not student:
            raise CustomError(404, "Student not found")
        args = create_student_parser.parse_args()
        roll_number = args.get("roll_number", None)
        first_name = args.get("first_name", None)
        last_name = args.get("last_name", None)
        if roll_number is None:
            raise CustomValidationError(400, "STUDENT001", "Roll Number required")
        if first_name is None:
            raise CustomValidationError(400, "STUDENT002", "First Name is required")
        try:
            Student.query.filter(Student.student_id == sid).update(
                {"roll_number": roll_number, "first_name": first_name, "last_name": last_name})
            db.session.commit()
            student = Student.query.filter(Student.student_id == sid).first()
        except Exception as e:
            raise CustomError(500, "Internal server error")
        return student, 201


class EnrollmentAPI(Resource):
    @marshal_with(enrollment_output)
    def get(self, sid):
        try:
            student = Student.query.filter(Student.student_id == sid).first()
            enrollments = Enrollments.query.filter(Enrollments.student_id == sid).all()
        except Exception as e:
            print(e)
            raise CustomError(500, "")
        if student is None:
            raise CustomValidationError(400, "ENROLLMENT002", "Student does not exist")
        if enrollments is None:
            raise CustomError(404, "Student is not enrolled in any course")
        else:
            return enrollments

    @marshal_with(enrollment_output)
    def post(self, sid):
        student = Student.query.filter(Student.student_id == sid).first()
        args = enrollment_parser.parse_args()
        cid = args.get("course_id", None)
        course = Course.query.filter(Course.course_id == cid).first()
        if cid is None or course is None:
            raise CustomValidationError(400, "ENROLLMENT001", "Course does not exist")
        if student is None:
            raise CustomValidationError(400, "ENROLLMENT002", "Student does not exist")
        existing_enrollment = Enrollments.query.filter(
            Enrollments.student_id == sid, Enrollments.course_id == cid).first()
        if existing_enrollment is not None:
            raise CustomError(404, "Enrollment already exists")
        try:
            enrollment = Enrollments(student_id=sid, course_id=cid)
            db.session.add(enrollment)
            db.session.commit()
        except Exception as e:
            print(e)
            raise CustomError(500, "Internal Server Error")
        return enrollment, 201

    def delete(self, sid, cid):
        student = Student.query.filter(Student.student_id == sid).first()
        course = Course.query.filter(Course.course_id == cid).first()
        if student is None:
            return CustomValidationError(400, "ENROLLMENT002", "Student does not exist")
        if course is None:
            return CustomValidationError(400, "ENROLLMENT001", "Course does not exist")
        existing_enrollment = Enrollments.query.filter(
            Enrollments.student_id == sid, Enrollments.course_id == cid).first()
        if not existing_enrollment:
            return "Enrollment for the student not found", 404
        try:
            Enrollments.query.filter(Enrollments.student_id == sid, Enrollments.course_id == cid).delete()
            db.session.commit()
        except Exception as e:
            print(e)
            raise CustomError(500, "Internal Server Error")
        return "Successfully deleted", 200


api.add_resource(StudentAPI, "/api/student", "/api/student/<string:sid>")
api.add_resource(CourseAPI, "/api/course", "/api/course/<string:cid>")
api.add_resource(EnrollmentAPI, "/api/student/<string:sid>/course", "/api/student/<string:sid>/course/<string:cid>")

if __name__ == "__main__":
    app.run(debug=True)
