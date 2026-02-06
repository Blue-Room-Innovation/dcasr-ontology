import type { SchemaKeyCurrent } from "./current/index.js";

export const schemaUrlsCurrent: Record<SchemaKeyCurrent, URL> = {
  "dpp-unece": new URL("../schemas/current/dppUnece.schema.json", import.meta.url),
  "dwp": new URL("../schemas/current/digitalWastePassport.schema.json", import.meta.url),
  "recycling": new URL("../schemas/current/recycling.schema.json", import.meta.url),
};
