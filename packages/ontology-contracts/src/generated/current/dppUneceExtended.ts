/**
 * Auto-generated TypeScript definitions from JSON Schema
 * DO NOT EDIT MANUALLY
 * Generated: 2026-01-30 14:47:55
 * Source: shapes/v0.1/dpp-unece-extended.shacl.ttl
 */

/**
 * This schema was automatically generated from SHACL shapes. It provides structural validation only. For semantic validation, use the original SHACL shapes.
 */
export type DigitalProductPassportGovernedShape = DigitalProductPassportGovernedShape1 &
  DigitalProductPassportGovernedShape2;
export type DigitalProductPassportGovernedShape1 = DigitalProductPassportShape;

export interface DigitalProductPassportShape {
  identifier: string;
  issuer: CredentialIssuerShape;
  validFrom?: string;
  validUntil?: string;
  credentialSubject: ProductPassportShape;
  [k: string]: unknown;
}
export interface CredentialIssuerShape {
  identifier: string;
  name: string;
  [k: string]: unknown;
}
export interface ProductPassportShape {
  product: ProductShape;
  granularityLevel?: "item" | "batch" | "model";
  [k: string]: unknown;
}
export interface ProductShape {
  identifier: string;
  name: string;
  [k: string]: unknown;
}
export interface DigitalProductPassportGovernedShape2 {
  identifier: string;
  issuer: CredentialIssuerShape;
  credentialSubject: ProductPassportShape;
  /**
   * Governed rule: Digital Product Passport must declare validFrom.
   */
  validFrom: string;
  /**
   * Governed rule: Digital Product Passport must declare validUntil.
   */
  validUntil: string;
}
