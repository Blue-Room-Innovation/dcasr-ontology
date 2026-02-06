import { createValidator, } from "@blueroominnovation/ontology-contracts";
const validator = createValidator();
const schemaKey = "dpp-unece";
const payload = {
    "@type": "DigitalProductPassport",
    id: "https://example.org/dpp/1",
    issuer: {
        "@type": "CredentialIssuer",
        id: "https://example.org/org/issuer-1",
        name: "Demo Issuer",
    },
    credentialSubject: {
        "@type": "ProductPassport",
        product: {
            "@type": "Product",
            id: "https://example.org/product/sku-123",
            name: "Demo Product",
        },
        granularityLevel: "item",
    },
    validFrom: new Date("2026-01-01T00:00:00Z").toISOString(),
    validUntil: new Date("2026-12-31T23:59:59Z").toISOString(),
};
const result = validator.validate(payload, schemaKey);
if (!result.ok) {
    console.error("Validation failed", result.errors);
    process.exit(1);
}
console.log("Validation OK :", result.value);
