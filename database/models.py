from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import (
    Column, Integer, String,
    DateTime, Float, Text, 
    ForeignKey, Time, Date
)
from datetime import timedelta
from database.utils import current_date, expiry_date

Base = declarative_base()

class Hospital(Base):
    __tablename__ = "hospitals"
    hospital_id = Column(Integer, primary_key=True, index=True)
    hospital_name = Column(String, index=True)
    hospital_email = Column(String, index=True, unique=True)
    hospital_contact = Column(String, index=True)
    hospital_password = Column(String, nullable=False)
    diagnosis_fee = Column(Float, default=0)
    expiry_date = Column(DateTime, default=expiry_date)
    
    date_added = Column(DateTime, default=current_date)
    
    workers = relationship("Worker", back_populates="hospital", cascade="all, delete-orphan")
    expiry = relationship("Expiry", back_populates="hospital", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="hospital", cascade="all, delete-orphan")
    drugs = relationship("Drug", back_populates="hospital", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="hospital", cascade="all, delete-orphan")
    diagnoses = relationship("Diagnosis", back_populates="hospital", cascade="all, delete-orphan")
    tests = relationship("LaboratoryTest", back_populates="hospital", cascade="all, delete-orphan")
    lab_requests = relationship("LaboratoryRequest", back_populates="hospital", cascade="all, delete-orphan")
    lab_results = relationship("LaboratoryResult", back_populates="hospital", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="hospital", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="hospital", cascade="all, delete-orphan")
    billings = relationship("Billing", back_populates="hospital", cascade="all, delete-orphan")
    

class Worker(Base):
    __tablename__ = "workers"
    worker_id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    worker_name = Column(String, index=True)
    worker_email = Column(String, nullable=True, index=True)
    worker_phone = Column(String, index=True)
    worker_password = Column(String, nullable=True)
    worker_role = Column(String)
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="workers")
    diagnoses = relationship("Diagnosis", back_populates="diagnoser", cascade="all, delete-orphan")
    lab_requests = relationship("LaboratoryRequest", back_populates="doctor", cascade="all, delete-orphan")
    lab_results = relationship("LaboratoryResult", back_populates="tech", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="consultant", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="prescriber", cascade="all, delete-orphan")

class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    patient_name = Column(String, nullable=True, index=True)
    patient_email = Column(String, nullable=True, index=True)
    patient_phone = Column(String, nullable=True, index=True)
    patient_id_number = Column(String, index=True, nullable=True)
    patient_gender = Column(String, nullable=True)
    patient_address = Column(String, nullable=True)
    patient_dob = Column(Date)
    patient_weight = Column(Float, nullable=True, default=0)
    patient_avg_pulse = Column(Float, default=0)
    patient_bp = Column(Float, default=0)
    patient_chronic_condition = Column(String, nullable=True, default="Null")
    patient_allergy = Column(String, nullable=True, default="Null")
    patient_blood_type = Column(String, nullable=True)
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="patients")
    diagnoses = relationship("Diagnosis", back_populates="patient", cascade="all, delete-orphan")
    lab_requests = relationship("LaboratoryRequest", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LaboratoryResult", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    billings = relationship("Billing", back_populates="patient", cascade="all, delete-orphan")

class Drug(Base):
    __tablename__ = "drugs"
    drug_id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    drug_name = Column(String, index=True)
    drug_category = Column(String, index=True)
    drug_desc = Column(Text)
    drug_quantity = Column(Integer)
    drug_price = Column(Float)
    drug_expiry = Column(DateTime)
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="drugs")
    prescriptions = relationship("PrescriptionItem", back_populates="drug")

class Service(Base):
    __tablename__ = "services"
    service_id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    service_name = Column(String, nullable=False, index=True)
    service_price = Column(Float, nullable=False)
    service_desc = Column(Text, nullable=False)
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")

class Diagnosis(Base):
    __tablename__ = "diagnosis"
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    diagnosis_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete = "RESTRICT"))
    diagnoser_id = Column(Integer, ForeignKey("workers.worker_id", ondelete = "RESTRICT"))

    symptoms = Column(Text)
    findings = Column(Text)
    suggested_diagnosis = Column(String)
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="diagnoses")
    patient = relationship("Patient", back_populates="diagnoses")
    diagnoser = relationship("Worker", back_populates="diagnoses")

class LaboratoryTest(Base):
    __tablename__ = "lab_tests"
    test_id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    test_name = Column(String, nullable=False, index=True)
    test_desc = Column(Text, nullable=False)
    test_price = Column(Float, nullable=False)
    
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="tests")
    lab_requests = relationship("LaboratoryRequest", back_populates="test")

class LaboratoryRequest(Base):
    __tablename__ = "lab_requests"
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    request_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete = "RESTRICT"))
    doctor_id = Column(Integer, ForeignKey("workers.worker_id", ondelete = "RESTRICT"))
    test_id = Column(Integer, ForeignKey("lab_tests.test_id", ondelete = "RESTRICT"))
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="lab_requests")
    doctor = relationship("Worker", back_populates="lab_requests")
    patient = relationship("Patient", back_populates="lab_requests")
    test = relationship("LaboratoryTest", back_populates="lab_requests")

class LaboratoryResult(Base):
    __tablename__ = "lab_results"
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    result_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete = "RESTRICT"))
    tech_id = Column(Integer, ForeignKey("workers.worker_id", ondelete = "RESTRICT"))

    observations = Column(Text)
    conclusion = Column(Text)
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="lab_results")
    patient = relationship("Patient", back_populates="lab_results")
    tech = relationship("Worker", back_populates="lab_results")

class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete = "RESTRICT"))
    consultant_id = Column(Integer, ForeignKey("workers.worker_id", ondelete = "RESTRICT"))
    service_id = Column(Integer, ForeignKey("services.service_id", ondelete = "RESTRICT"))

    appointment_desc = Column(Text)
    date_requested = Column(Date)
    time_requested = Column(Time)
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    consultant = relationship("Worker", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

class Prescription(Base):
    __tablename__ = "prescriptions"
    prescription_id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete = "RESTRICT"))
    prescriber_id = Column(Integer, ForeignKey("workers.worker_id", ondelete = "RESTRICT"))
    date_added = Column(DateTime, default=current_date)

    hospital = relationship("Hospital", back_populates="prescriptions")
    patient = relationship("Patient", back_populates="prescriptions")
    prescriber = relationship("Worker", back_populates="prescriptions")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    item_id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.prescription_id", ondelete = "RESTRICT"))
    drug_id = Column(Integer, ForeignKey("drugs.drug_id", ondelete = "RESTRICT"))
    drug_qty = Column(Integer)
    notes = Column(Text, nullable=True)

    prescription = relationship("Prescription", back_populates="items")
    drug = relationship("Drug", back_populates="prescriptions")

class Billing(Base):
    __tablename__ = "billings"

    billing_id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=True)
    source = Column(String, nullable=True)
    item = Column(String, nullable=True)
    total = Column(Float, default=0)
    created_at = Column(DateTime, default=current_date)

    patient = relationship("Patient", back_populates="billings")
    hospital = relationship("Hospital", back_populates="billings")


class Expiry(Base):
    __tablename__ = "expiry"
    hospital_id = Column(Integer, ForeignKey("hospitals.hospital_id"))
    expiry_id = Column(Integer, primary_key=True)
    expiry_date = Column(DateTime, default=expiry_date)
    
    hospital = relationship("Hospital", back_populates="expiry")