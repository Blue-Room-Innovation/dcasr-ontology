/**
 * Auto-generated TypeScript definitions from JSON Schema
 * DO NOT EDIT MANUALLY
 * Generated: 2026-02-06 14:15:44
 * Source: shapes/v0.1/recycling.shacl.ttl
 */

/**
 * This schema was automatically generated from SHACL shapes. It provides structural validation only. For semantic validation, use the original SHACL shapes.
 */
export type RecyclingOrganisationShape = RecyclingOrganisationShape1 & RecyclingOrganisationShape2;
export type RecyclingOrganisationShape1 =
  | {
      [k: string]: unknown;
    }
  | {
      latitude: number;
      longitude: number;
      [k: string]: unknown;
    };

export interface RecyclingOrganisationShape2 {
  /**
   * Type identifier for Recycler
   */
  "@type": "Recycler";
  managerCode: string;
  nimaCode: string;
  name: string;
  streetAddress: string;
  addressLocality: string;
  postalCode: string;
  correspondeceAddress: string;
  correspondeceAddressLocality: string;
  correspondecePostalCode: string;
  telephone?: string;
  faxNumber?: string;
  email?: string;
  url?:
    | string
    | {
        "@id": string;
        [k: string]: unknown;
      };
  adaptedToRD1102015?: boolean;
  wasteTreatmentActivity?: string;
  latitude?: number;
  longitude?: number;
}
