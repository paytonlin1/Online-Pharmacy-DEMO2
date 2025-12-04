-- For patients to see their balance: --
Select Patient.balance from Patient where patient.name = USER INPUT


-- For any user to see either their own (patient) or any (doctors and pharmacists) prescriptions: --
Select prescriptions.dosage, drug.name, drug.common_ailment 
	From prescriptions, drug, patient
	Where prescriptions.patient_id = patient.patient_id and 
	patient.name = USER INPUT and prescriptions.drug_id = drug.drug_id
    
-- For any user to see pickups NEEDS FIXED --
Select orders.request_date, orders.status, pharmacy.address, pharmacist.pharmacist_id, drug.name, drug.common_ailment
	From orders, pharmacy, pharmacist, drug, patient, prescription
	Where patient.name = USER INPUT and orders.patient_id = patient.patient_id 
	and orders.prescript_id = prescription.prescript_id and prescript.drug_id = drug.drug_id
    
-- For doctors and pharmacists to see patient health history  --
Select PatientHistory.allergies, PatientHistory.family_history, PatientHistory.notes
	From PatientHistory, Patient
	Where Patient.patient_id = PatientHistory.patient_id and 
	patient.name = USER INPUT
    
-- For doctors to change the health notes of a patient --
UPDATE PatientHistory, patient
	SET allergies = USER INPUT, family_history = USER INPUT, notes = USER INPUT
	Where patient.name = USER INPUT and PatientHistory.patient_id=patient.patient_id
    
-- For doctors to issue new prescriptions NEEDS FIXED --
Insert into prescriptions(prescript_id, patient_id, doctor_id, drug_id, dosage)
Select (select COUNT(*) from prescriptions)+1, patient.patient_id, doctor.doctor_id, drug.drug_id, USER INPUT
From patient, doctor, prescriptions, drug
Where patient.name = USER INPUT and doctor.doctor_name = USER INPUT and drug.name = USER INPUT

-- For pharmacists to schedule new pickups NEEDS FIXED --
Insert into orders(order_id, request_date, pharmacy_id, patient_id, prescript_id, pharmacist_id, status
	Select max(orders)+1, USER INPUT, pharmacy.pharmacy_id, patient.patient_id, 
	prescription.prescript_id, pharmacist.pharmacist_id, USER INPUT
	From prescription, pharmacy, patient, orders
	Where patient.patient_name = USER INPUT and prescription.prescript_id = patient.patient_id, and pharmacist.name = USER INPUT
