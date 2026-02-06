import fs from "node:fs";
import { createRequire } from "node:module";
import { CURRENT_BUILD_VERSION } from "./current/index.js";
import { schemaUrlsCurrent } from "./schema-registry.js";
const schemaObjectCache = new Map();
function loadSchemaObject(schemaKey) {
    const cacheKey = `${schemaKey}`;
    const cached = schemaObjectCache.get(cacheKey);
    if (cached)
        return cached;
    const url = schemaUrlsCurrent[schemaKey];
    const raw = fs.readFileSync(url, "utf8");
    const parsed = JSON.parse(raw);
    schemaObjectCache.set(cacheKey, parsed);
    return parsed;
}
const compiledValidatorsCache = new WeakMap();
function getCompiledValidator(ajv, schemaKey) {
    let perAjvCache = compiledValidatorsCache.get(ajv);
    if (!perAjvCache) {
        perAjvCache = new Map();
        compiledValidatorsCache.set(ajv, perAjvCache);
    }
    const cacheKey = `${schemaKey}`;
    const cached = perAjvCache.get(cacheKey);
    if (cached)
        return cached;
    const schema = loadSchemaObject(schemaKey);
    const validate = ajv.compile(schema);
    perAjvCache.set(cacheKey, validate);
    return validate;
}
function normalizeErrors(errors) {
    if (!errors || errors.length === 0)
        return [];
    return errors.map((e) => ({
        instancePath: e.instancePath,
        schemaPath: e.schemaPath,
        message: e.message,
        params: e.params
    }));
}
export function createValidator(options = {}) {
    const require = createRequire(import.meta.url);
    const Ajv = require("ajv");
    const addFormats = require("ajv-formats");
    const ajv = options.ajv ??
        new Ajv({
            allErrors: true,
            strict: false,
            strictSchema: false
        });
    addFormats(ajv);
    return {
        version: CURRENT_BUILD_VERSION,
        ajv,
        validate(data, schemaKey) {
            const validateFn = getCompiledValidator(ajv, schemaKey);
            const ok = validateFn(data);
            if (ok) {
                return { ok: true, schemaKey, value: data };
            }
            return { ok: false, schemaKey, errors: normalizeErrors(validateFn.errors) };
        },
        assertValid(data, schemaKey) {
            const result = this.validate(data, schemaKey);
            if (result.ok)
                return;
            const messages = result.errors
                .map((e) => `${e.instancePath || "<root>"} ${e.message ?? "is invalid"}`.trim())
                .join("\n");
            throw new Error(`Invalid payload for schema '${schemaKey}':\n${messages}`);
        }
    };
}
//# sourceMappingURL=validator.js.map