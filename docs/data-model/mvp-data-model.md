# Modèle de données MVP

## Objectif

Définir les principales entités nécessaires au premier MVP de GuinéeCare Hospital Suite.

## Socle

### facilities

Champs recommandés : id, code, name, type, region, prefecture, status, created_at.

### departments

Champs recommandés : id, facility_id, code, name, department_type, status, created_at.

### users

Champs recommandés : id, facility_id, email, password_hash, first_name, last_name, status, created_at.

### roles

Champs recommandés : id, code, name, description.

### permissions

Champs recommandés : id, code, name, module.

## Patient et admission

### patients

Champs recommandés : id, facility_id, patient_number, first_name, last_name, gender, date_of_birth, phone, address, status, created_at.

### admissions

Champs recommandés : id, facility_id, patient_id, department_id, admission_type, status, admitted_at, closed_at, created_by.

## Dossier clinique MVP

### clinical_notes

Champs recommandés : id, facility_id, patient_id, admission_id, note_text, created_by, created_at.

### patient_measurements

Champs recommandés : id, facility_id, patient_id, admission_id, measurement_type, value, unit, recorded_by, recorded_at.

### diagnoses

Champs recommandés : id, facility_id, patient_id, admission_id, diagnosis_code, diagnosis_label, diagnosis_type, created_by, created_at.

## Urgences

### emergency_visits

Champs recommandés : id, facility_id, patient_id, admission_id, arrival_time, priority_level, status, orientation, created_at.

## Hospitalisation

### rooms

Champs recommandés : id, facility_id, department_id, code, name, status.

### beds

Champs recommandés : id, facility_id, room_id, bed_number, status.

### hospital_stays

Champs recommandés : id, facility_id, patient_id, admission_id, bed_id, started_at, ended_at, status.

## Pharmacie

### products

Champs recommandés : id, facility_id, code, name, category, form, dosage, status.

### product_stock

Champs recommandés : id, facility_id, product_id, quantity_available, min_threshold, updated_at.

## Laboratoire

### lab_tests

Champs recommandés : id, facility_id, code, name, category, sample_type, status.

### lab_orders

Champs recommandés : id, facility_id, patient_id, admission_id, status, ordered_by, ordered_at.

### lab_results

Champs recommandés : id, facility_id, lab_order_id, result_value, status, validated_by, validated_at.

## Facturation

### tariff_items

Champs recommandés : id, facility_id, code, name, category, unit_price, status.

### invoices

Champs recommandés : id, facility_id, patient_id, admission_id, invoice_number, status, net_amount, paid_amount, balance_due.

### payments

Champs recommandés : id, facility_id, invoice_id, amount, payment_method, status, received_by, received_at.

## Audit

### audit_logs

Champs recommandés : id, facility_id, user_id, action, resource_type, resource_id, patient_id, ip_address, old_values, new_values, created_at.
