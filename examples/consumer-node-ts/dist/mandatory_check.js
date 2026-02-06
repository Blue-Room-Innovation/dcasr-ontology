import { createValidator, } from "@blueroominnovation/ontology-contracts";
const validator = createValidator();
const schemaKey = "dwp";
console.log("---------------------------------------------------------");
console.log("MANDATORY FIELD TEST: Verifying rejection of missing required fields");
console.log("---------------------------------------------------------");
// 1. Create a payload MISSING the required 'id' field
// validFrom is optional in SHACL (no minCount), but let's check 'id' which IS mandatory
const payloadMissingId = {
    // MISSING id
    issuer: {
        id: "https://example.org/org/issuer-1",
        name: "Demo Issuer",
    },
    validFrom: new Date().toISOString(),
    credentialSubject: {
        waste: {
            name: "Demo waste",
        },
    },
};
// 2. Validate
const result = validator.validate(payloadMissingId, schemaKey);
// 3. Assert EXPECTED FAILURE
if (result.ok) {
    console.error("❌ MANDATORY CHECK FAILED: Validation succeeded but should have failed due to missing 'id'");
    process.exit(1);
}
else {
    // Check if error is about required property
    const hasRequiredError = result.errors && JSON.stringify(result.errors).includes("must have required property 'id'");
    if (hasRequiredError) {
        console.log("✅ MANDATORY CHECK PASSED: Validation failed as expected with 'required property' error.");
    }
    else {
        console.warn("⚠️  MANDATORY CHECK WARNING: Validation failed, but not strictly due to 'id'?");
        console.warn("   Error details:", JSON.stringify(result.errors, null, 2));
        // check if it mentions 'required' generally
        if (JSON.stringify(result.errors).includes("required")) {
            console.log("✅ MANDATORY CHECK PASSED: Validation failed with 'required' error.");
        }
    }
}
console.log("---------------------------------------------------------");
