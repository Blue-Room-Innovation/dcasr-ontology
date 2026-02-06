/**
 * Auto-generated TypeScript definitions from JSON Schema
 * DO NOT EDIT MANUALLY
 * Generated: 2026-02-06 14:15:43
 * Source: shapes/v0.1/digital-waste-passport.shacl.ttl
 */
/**
 * This schema was automatically generated from SHACL shapes. It provides structural validation only. For semantic validation, use the original SHACL shapes.
 */
export interface DigitalWastePassportShape {
    /**
     * Type identifier for DigitalWastePassport
     */
    "@type": "DigitalWastePassport";
    id: string;
    issuer: CredentialIssuerShape;
    /**
     * The data from which this version is valid.
     */
    validFrom?: string;
    /**
     * The date and time until which this version remains valid.
     */
    validUntil?: string;
    credentialSubject: WastePassportShape;
}
export interface CredentialIssuerShape {
    /**
     * Type identifier for CredentialIssuer
     */
    "@type": "CredentialIssuer";
    /**
     * The W3C DID of the ...
     */
    id: string;
    /**
     * An optional list of other ...
     */
    issuerAlsoKnownAs?: PartyShape;
    /**
     * The name of the issuer ...
     */
    name: string;
}
export interface PartyShape {
    /**
     * Type identifier for Party
     */
    "@type": "Party";
    /**
     * An optional short description of ...
     */
    description?: string;
    /**
     * The W3C DID of the ...
     */
    id: string;
    /**
     * The identifier scheme of the ...
     */
    idScheme?: IdentifierSchemeShape;
    /**
     * The industry categories for this ...
     */
    industryCategory?: ClassificationShape;
    /**
     * The name of the issuer ...
     */
    name: string;
    /**
     * Website for this organisation
     */
    organisationWebsite?: string;
    /**
     * An optional list of other ...
     */
    partyAlsoKnownAs?: PartyShape;
    /**
     * The registration number (alphanumeric) of ...
     */
    registeredId?: string;
    /**
     * the country in which this ...
     */
    registrationCountry?: string;
}
export interface IdentifierSchemeShape {
    /**
     * Type identifier for IdentifierScheme
     */
    "@type": "IdentifierScheme";
    /**
     * The W3C DID of the ...
     */
    id: string;
    /**
     * The name of the issuer ...
     */
    name: string;
}
export interface ClassificationShape {
    /**
     * Type identifier for Classification
     */
    "@type": "Classification";
    /**
     * classification code within the scheme ...
     */
    code: string;
    /**
     * The W3C DID of the ...
     */
    id: string;
    /**
     * The name of the issuer ...
     */
    name: string;
    /**
     * Classification scheme ID
     */
    schemeID: string;
    /**
     * The name of the classification ...
     */
    schemeName: string;
}
export interface WastePassportShape {
    /**
     * Type identifier for WastePassport
     */
    "@type": "WastePassport";
    /**
     * A circularity performance scorecard
     */
    circularityScorecard?: CircularityPerformanceShape;
    /**
     * An array of claim objects ...
     */
    conformityClaim?: ClaimShape;
    /**
     * The due diligence declaration that ...
     */
    dueDiligenceDeclaration?: LinkShape;
    /**
     * An emissions performance scorecard
     */
    emissionsScorecard?: EmissionsPerformanceShape;
    /**
     * Code to indicate the granularity ...
     */
    granularityLevel?: "item" | "batch" | "model";
    /**
     * An id is not required ...
     */
    id?: string;
    /**
     * An array of Provenance objects ...
     */
    materialsProvenance?: MaterialShape;
    /**
     * An array of traceability events ...
     */
    traceabilityInformation?: TraceabilityPerformanceShape;
    /**
     * The waste being documented in this passport
     */
    waste: WasteShape;
}
export interface CircularityPerformanceShape {
    /**
     * Type identifier for CircularityPerformance
     */
    "@type": "CircularityPerformance";
    /**
     * The overall circularity performance indicator ...
     */
    materialCircularityIndicator?: number;
    /**
     * The fraction of the this ...
     */
    recyclableContent?: number;
    /**
     * The fraction (by mass) of ...
     */
    recycledContent?: number;
    /**
     * A URI pointing to recycling ...
     */
    recyclingInformation?: LinkShape;
    /**
     * A URI pointing to repair ...
     */
    repairInformation?: LinkShape;
    /**
     * An indicator of durability defined ...
     */
    utilityFactor?: number;
}
export interface LinkShape {
    /**
     * Type identifier for Link
     */
    "@type": "Link";
    /**
     * A display name for the ...
     */
    linkName?: string;
    /**
     * The type of the target ...
     */
    linkType?: string;
    /**
     * The URL of the target ...
     */
    linkURL: string;
}
export interface ClaimShape {
    /**
     * Type identifier for Claim
     */
    "@type": "Claim";
    /**
     * The specification against which the ...
     */
    assessmentCriteria?: CriterionShape;
    /**
     * The date on which this ...
     */
    assessmentDate?: string;
    /**
     * An indicator of whether or ...
     */
    conformance?: boolean;
    /**
     * A URI pointing to the ...
     */
    conformityEvidence?: SecureLinkShape;
    /**
     * The conformity topic category for ...
     */
    conformityTopic?: string;
    /**
     * The list of specific values ...
     */
    declaredValue?: MetricShape;
    /**
     * An optional short description of ...
     */
    description?: string;
    /**
     * The W3C DID of the ...
     */
    id?: string;
    /**
     * The reference to the regulation ...
     */
    referenceRegulation?: RegulationShape;
    /**
     * The reference to the standard ...
     */
    referenceStandard?: StandardShape;
}
export interface CriterionShape {
    /**
     * Type identifier for Criterion
     */
    "@type": "Criterion";
    /**
     * A set of classification codes ...
     */
    category?: ClassificationShape;
    /**
     * The conformity topic category for ...
     */
    conformityTopic?: string;
    /**
     * An optional short description of ...
     */
    description?: string;
    /**
     * The W3C DID of the ...
     */
    id?: string;
    /**
     * The name of the issuer ...
     */
    name?: string;
    /**
     * A performance category code to ...
     */
    performanceLevel?: string;
    /**
     * The lifecycle status of this ...
     */
    status?: string;
    /**
     * List of criterion that are ...
     */
    subCriterion?: CriterionShape;
    /**
     * A set of tags that ...
     */
    tag?: string;
    /**
     * A threshold value that defines ...
     */
    thresholdValue?: MetricShape;
}
export interface MetricShape {
    /**
     * Type identifier for Metric
     */
    "@type": "Metric";
    /**
     * A percentage represented as a ...
     */
    accuracy?: number;
    /**
     * A human readable name for ...
     */
    metricName?: string;
    /**
     * A numeric value and unit ...
     */
    metricValue?: MeasureShape;
    /**
     * A score or rank associated ...
     */
    score?: string;
}
export interface MeasureShape {
    /**
     * Type identifier for Measure
     */
    "@type": "Measure";
    /**
     * Unit of measure drawn from ...
     */
    unit: string;
    /**
     * The numeric value of the ...
     */
    value: number;
}
export interface SecureLinkShape {
    /**
     * Type identifier for SecureLink
     */
    "@type": "SecureLink";
    /**
     * The symmetric encryption algorithm used ...
     */
    encryptionMethod?: string;
    /**
     * The hash of the file. ...
     */
    hashDigest?: string;
    /**
     * The hashing algorithm used to ...
     */
    hashMethod?: string;
    /**
     * A display name for the ...
     */
    linkName?: string;
    /**
     * The type of the target ...
     */
    linkType?: string;
    /**
     * The URL of the target ...
     */
    linkURL?: string;
}
export interface RegulationShape {
    /**
     * Type identifier for Regulation
     */
    "@type": "Regulation";
    /**
     * the issuing body of the ...
     */
    administeredBy?: PartyShape;
    /**
     * the date at which the ...
     */
    effectiveDate?: string;
    /**
     * The W3C DID of the ...
     */
    id?: string;
    /**
     * The legal jurisdiction (country) under ...
     */
    jurisdictionCountry?: string;
    /**
     * The name of the issuer ...
     */
    name?: string;
}
export interface StandardShape {
    /**
     * Type identifier for Standard
     */
    "@type": "Standard";
    /**
     * The W3C DID of the ...
     */
    id?: string;
    /**
     * The date when the standard ...
     */
    issueDate?: string;
    /**
     * The party that issued the ...
     */
    issuingParty?: PartyShape;
    /**
     * The name of the issuer ...
     */
    name?: string;
}
export interface EmissionsPerformanceShape {
    /**
     * Type identifier for EmissionsPerformance
     */
    "@type": "EmissionsPerformance";
    /**
     * The carbon footprint of the ...
     */
    carbonFootprint?: number;
    /**
     * The unit of product (EA, ...
     */
    declaredUnit?: string;
    /**
     * The operational scope of the ...
     */
    operationalScope?: "CradleToGate" | "CradleToGrave" | "None";
    /**
     * The ratio of emissions data ...
     */
    primarySourcedRatio?: number;
    /**
     * The reporting standard (eg GHG ...
     */
    reportingStandard?: StandardShape;
}
export interface MaterialShape {
    /**
     * Type identifier for Material
     */
    "@type": "Material";
    /**
     * Indicates whether this material is ...
     */
    hazardous?: boolean;
    /**
     * The mass of the material ...
     */
    mass?: MeasureShape;
    /**
     * The mass fraction of the ...
     */
    massFraction?: number;
    /**
     * Reference to further information about ...
     */
    materialSafetyInformation?: LinkShape;
    /**
     * The type of this material ...
     */
    materialType?: ClassificationShape;
    /**
     * The name of the issuer ...
     */
    name?: string;
    /**
     * A ISO 3166-1 code representing ...
     */
    originCountry?: string;
    /**
     * Mass fraction of this material ...
     */
    recycledMassFraction?: number;
    /**
     * Based 64 encoded binary used ...
     */
    symbol?: string;
}
export interface TraceabilityPerformanceShape {
    /**
     * Type identifier for TraceabilityPerformance
     */
    "@type": "TraceabilityPerformance";
    /**
     * A list of secure links ...
     */
    traceabilityEvent?: SecureLinkShape;
    /**
     * Human readable name for the ...
     */
    valueChainProcess?: string;
    /**
     * The proportion (0 to 1) ...
     */
    verifiedRatio?: number;
}
export interface WasteShape {
    /**
     * Type identifier for Waste
     */
    "@type": "Waste";
    /**
     * Identifier of the specific production batch
     */
    batchNumber?: string;
    /**
     * Extension point for waste specific characteristics
     */
    characteristics?: CharacteristicsShape;
    /**
     * The country in which this ...
     */
    countryOfProduction?: "AD" | "AE" | "AF" | "AG" | "AI" | "AL" | "AM" | "AO" | "AQ" | "AR" | "AS" | "AT" | "AU" | "AW" | "AX" | "AZ" | "BA" | "BB" | "BD" | "BE" | "BF" | "BG" | "BH" | "BI" | "BJ" | "BL" | "BM" | "BN" | "BO" | "BQ" | "BR" | "BS" | "BT" | "BV" | "BW" | "BY" | "BZ" | "CA" | "CC" | "CD" | "CF" | "CG" | "CH" | "CI" | "CK" | "CL" | "CM" | "CN" | "CO" | "CR" | "CU" | "CV" | "CW" | "CX" | "CY" | "CZ" | "DE" | "DJ" | "DK" | "DM" | "DO" | "DZ" | "EC" | "EE" | "EG" | "EH" | "ER" | "ES" | "ET" | "FI" | "FJ" | "FK" | "FM" | "FO" | "FR" | "GA" | "GB" | "GD" | "GE" | "GF" | "GG" | "GH" | "GI" | "GL" | "GM" | "GN" | "GP" | "GQ" | "GR" | "GS" | "GT" | "GU" | "GW" | "GY" | "HK" | "HM" | "HN" | "HR" | "HT" | "HU" | "ID" | "IE" | "IL" | "IM" | "IN" | "IO" | "IQ" | "IR" | "IS" | "IT" | "JE" | "JM" | "JO" | "JP" | "KE" | "KG" | "KH" | "KI" | "KM" | "KN" | "KP" | "KR" | "KW" | "KY" | "KZ" | "LA" | "LB" | "LC" | "LI" | "LK" | "LR" | "LS" | "LT" | "LU" | "LV" | "LY" | "MA" | "MC" | "MD" | "ME" | "MF" | "MG" | "MH" | "MK" | "ML" | "MM" | "MN" | "MO" | "MP" | "MQ" | "MR" | "MS" | "MT" | "MU" | "MV" | "MW" | "MX" | "MY" | "MZ" | "NA" | "NC" | "NE" | "NF" | "NG" | "NI" | "NL" | "NO" | "NP" | "NR" | "NU" | "NZ" | "OM" | "PA" | "PE" | "PF" | "PG" | "PH" | "PK" | "PL" | "PM" | "PN" | "PR" | "PS" | "PT" | "PW" | "PY" | "QA" | "RE" | "RO" | "RS" | "RU" | "RW" | "SA" | "SB" | "SC" | "SD" | "SE" | "SG" | "SH" | "SI" | "SJ" | "SK" | "SL" | "SM" | "SN" | "SO" | "SR" | "SS" | "ST" | "SV" | "SX" | "SY" | "SZ" | "TC" | "TD" | "TF" | "TG" | "TH" | "TJ" | "TK" | "TL" | "TM" | "TN" | "TO" | "TR" | "TT" | "TV" | "TW" | "TZ" | "UA" | "UG" | "UM" | "US" | "UY" | "UZ" | "VA" | "VC" | "VE" | "VG" | "VI" | "VN" | "VU" | "WF" | "WS" | "YE" | "YT" | "ZA" | "ZM" | "ZW";
    /**
     * An optional short description of the waste
     */
    description?: string;
    /**
     * The physical dimensions of the waste
     */
    dimensions?: DimensionShape;
    /**
     * A URL pointing to further information
     */
    furtherInformation?: LinkShape;
    /**
     * The W3C DID of the waste
     */
    id?: string;
    /**
     * The identifier scheme of the waste
     */
    idScheme?: IdentifierSchemeShape;
    /**
     * Name of the waste
     */
    name?: string;
    /**
     * The Facility where the waste was produced
     */
    producedAtFacility?: FacilityShape;
    /**
     * The Party entity that produced the waste
     */
    producedByParty?: PartyShape;
    /**
     * A code representing the waste category
     */
    productCategory?: ClassificationShape;
    /**
     * Reference information for product image
     */
    productImage?: LinkShape;
    /**
     * The ISO 8601 date on which the waste was produced
     */
    productionDate?: string;
    /**
     * The registration number of the waste
     */
    registeredId?: string;
    /**
     * A number or code representing the serial number
     */
    serialNumber?: string;
    /**
     * Weight of the waste
     */
    weightQuantity?: number;
    /**
     * The Facility where the waste ...
     */
    pickupFacility?: FacilityShape;
    /**
     * The Waste Party entity that manufactured ...
     */
    wasteAgentParty?: PartyShape;
}
export interface CharacteristicsShape {
    /**
     * Type identifier for Characteristics
     */
    "@type": "Characteristics";
}
export interface DimensionShape {
    /**
     * Type identifier for Dimension
     */
    "@type": "Dimension";
    /**
     * The height of the product ...
     */
    height?: MeasureShape;
    /**
     * The length of the product ...
     */
    length?: MeasureShape;
    /**
     * The displacement volume of the ...
     */
    volume?: MeasureShape;
    /**
     * the weight of the product. ...
     */
    weight?: MeasureShape;
    /**
     * The width of the product ...
     */
    width?: MeasureShape;
}
export interface FacilityShape {
    /**
     * Type identifier for Facility
     */
    "@type": "Facility";
    /**
     * The Postal address of the ...
     */
    address?: AddressShape;
    /**
     * The country in which this ...
     */
    countryOfOperation?: string;
    /**
     * An optional short description of ...
     */
    description?: string;
    /**
     * An optional list of other ...
     */
    facilityAlsoKnownAs?: FacilityShape;
    /**
     * The W3C DID of the ...
     */
    id: string;
    /**
     * The identifier scheme of the ...
     */
    idScheme?: IdentifierSchemeShape;
    /**
     * Geo-location information for this facility ...
     */
    locationInformation?: LocationShape;
    /**
     * The name of the issuer ...
     */
    name?: string;
    /**
     * The Party entity responsible for ...
     */
    operatedByParty?: PartyShape;
    /**
     * The industrial or production processes ...
     */
    processCategory?: ClassificationShape;
    /**
     * The registration number (alphanumeric) of ...
     */
    registeredId?: string;
}
export interface AddressShape {
    /**
     * Type identifier for Address
     */
    "@type": "Address";
    /**
     * The address country as an ...
     */
    addressCountry?: string;
    /**
     * The city, suburb or township ...
     */
    addressLocality?: string;
    /**
     * The state or territory or ...
     */
    addressRegion?: string;
    /**
     * The postal code or zip ...
     */
    postalCode?: string;
    /**
     * the street address as an ...
     */
    streetAddress?: string;
}
export interface LocationShape {
    /**
     * Type identifier for Location
     */
    "@type": "Location";
    /**
     * The list of ordered coordinates ...
     */
    geoBoundary?: string;
    /**
     * The latitude and longitude coordinates ...
     */
    geoLocation?: string;
    /**
     * An open location code (https://maps.google.com/pluscodes/) ...
     */
    plusCode?: string;
}
//# sourceMappingURL=digitalWastePassport.d.ts.map