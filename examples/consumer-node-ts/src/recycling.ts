import {
  createValidator,
  type RecyclingOrganisationShape,
  type SchemaKeyCurrent,
} from "@blueroominnovation/ontology-contracts";

const validator = createValidator();

const schemaKey: SchemaKeyCurrent = "recycling";

const payload: RecyclingOrganisationShape = {
  "@type": "Recycler",
  managerCode: "laborum",
  nimaCode: "sit proident est sed cupidatat",
  name: "dolor reprehenderit eu laborum aute",
  streetAddress: "sed sunt incididunt nulla",
  addressLocality: "enim tempor fugiat et",
  postalCode: "28001",
  correspondeceAddress: "anim",
  correspondeceAddressLocality: "enim",
  correspondecePostalCode: "28002",
  telephone: "+34 987 567 564",
  faxNumber: "+34 912 345 678",
  email: "contacto@empresa.com",
  url: {
    "@id": "https://example.com",
  },
  wasteTreatmentActivity: "sit",
  adaptedToRD1102015: true,
  latitude: 22,
  longitude: 22,
};

const result = validator.validate(payload, schemaKey);

if (!result.ok) {
  console.error("Validation failed", result.errors);
  process.exit(1);
}

console.log("Validation OK :", result.value);
