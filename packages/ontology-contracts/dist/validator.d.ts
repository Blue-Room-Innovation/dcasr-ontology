import type { Ajv as AjvClass } from "ajv";
import { CURRENT_BUILD_VERSION } from "./current/index.js";
import type { SchemaKeyCurrent, SchemaTypeCurrent } from "./current/index.js";
export type SchemaVersion = typeof CURRENT_BUILD_VERSION;
export type SchemaKey = SchemaKeyCurrent;
export type ValidationError = {
    instancePath: string;
    schemaPath: string;
    message?: string;
    params?: unknown;
};
export type ValidateResult<K extends SchemaKey> = {
    ok: true;
    schemaKey: K;
    value: SchemaTypeCurrent<K>;
} | {
    ok: false;
    schemaKey: K;
    errors: ValidationError[];
};
export type OntologyValidator = {
    version: SchemaVersion;
    ajv: AjvInstance;
    validate<K extends SchemaKey>(data: unknown, schemaKey: K): ValidateResult<K>;
    assertValid<K extends SchemaKey>(data: unknown, schemaKey: K): asserts data is SchemaTypeCurrent<K>;
};
export type CreateValidatorOptions = {
    ajv?: AjvInstance;
};
export type AjvInstance = AjvClass;
export declare function createValidator(options?: CreateValidatorOptions): OntologyValidator;
//# sourceMappingURL=validator.d.ts.map