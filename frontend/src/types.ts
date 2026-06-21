export type Row = Record<string, any>;

export type FormValues = Record<string, string>;

export type Option = {
  value: string;
  label: string;
};

export type FieldConfig = {
  name: string;
  label: string;
  type?: string;
  options?: Option[];
};

export type LookupData = {
  facilities: Row[];
  patients: Row[];
  departments: Row[];
  admissions: Row[];
  products: Row[];
  labTests: Row[];
  labOrders: Row[];
  invoices: Row[];
  maternityRecords: Row[];
  staff: Row[];
  indicators: Row[];
  shifts: Row[];
};

export const emptyLookups: LookupData = {
  facilities: [],
  patients: [],
  departments: [],
  admissions: [],
  products: [],
  labTests: [],
  labOrders: [],
  invoices: [],
  maternityRecords: [],
  staff: [],
  indicators: [],
  shifts: [],
};
