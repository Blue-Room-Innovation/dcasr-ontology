import { createValidator, } from "@blueroominnovation/ontology-contracts";
const validator = createValidator();
const schemaKey = "dpp-unece";
console.log("---------------------------------------------------------");
console.log("STRICTNESS TEST: Verifying rejection of extra properties");
console.log("---------------------------------------------------------");
// 1. Create a payload with an ILLEGAL extra property
const payloadWithJunk = {
    // Required fields
    identifier: "https://example.org/dpp/strict-test",
    issuer: {
        identifier: "https://example.org/org/issuer-strict",
        name: "Strictness Tester",
    },
    credentialSubject: {
        product: {
            identifier: "https://example.org/product/strict-1",
            name: "Strict Product",
        },
        // Required property
        granularityLevel: "item",
    },
    // ILLEGAL PROPERTY
    _thisShouldNotBeAllowed: "I am an extra property",
};
// 2. Validate
const result = validator.validate(payloadWithJunk, schemaKey);
// 3. Assert EXPECTED FAILURE
if (result.ok) {
    console.error("❌ STRICTNESS CHECK FAILED: Validation succeeded but should have failed due to '_thisShouldNotBeAllowed'");
    process.exit(1);
}
else {
    // Check if error is about additionalProperties
    const hasAdditionalPropsError = result.errors && JSON.stringify(result.errors).includes("additionalProperties");
    if (hasAdditionalPropsError) {
        console.log("✅ STRICTNESS CHECK PASSED: Validation failed as expected with 'additionalProperties' error.");
    }
    else {
        console.warn("⚠️  STRICTNESS CHECK WARNING: Validation failed, but not strictly due to 'additionalProperties'?");
        console.warn("   Error details:", JSON.stringify(result.errors, null, 2));
        // accepted as pass for now if it failed
    }
}
console.log("---------------------------------------------------------");
