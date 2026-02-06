import { createValidator, } from "@blueroominnovation/ontology-contracts";
const validator = createValidator();
const schemaKey = "dmwp";
const payload = {
    "@type": "DigitalMarpolWastePassport",
    issued: new Date().toISOString(),
    publisher: {
        "@type": "AuthorizedParty",
    },
    credentialSubject: {
        "@type": "MarpolWastePassport",
        waste: {
            "@type": "MarpolWaste",
            ship: {
                "@type": "Ship",
                imoNumber: "1234567",
                name: "Demo ship",
                flag: "ES",
            },
            residue: {
                "@type": "ResidueInformation",
                typeCode: "OIL",
                subtypeCode: "SLU",
                quantityToDeliver: {
                    "@type": "Measure",
                },
            },
        },
    },
};
const result = validator.validate(payload, schemaKey);
if (!result.ok) {
    console.error("Validation failed", result.errors);
    process.exit(1);
}
console.log("Validation OK :", result.value);
