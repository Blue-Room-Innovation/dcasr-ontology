#!/usr/bin/env node
// Cross-platform Docker wrapper for build and run operations

const { execSync, spawnSync } = require("child_process");
const path = require("path");

const IMAGE_NAME = "bri-ontology-tooling:latest";
const DOCKERFILE = path.join(__dirname, "Dockerfile");

// Mapping from script names to actual Python commands
const SCRIPT_COMMANDS = {
  cli: "python scripts/ontology_cli.py",
  help: "python scripts/ontology_cli.py --help",
  "validate:owl": "python scripts/ontology_cli.py validate owl",
  "validate:owl:quiet": "python scripts/ontology_cli.py validate owl --quiet",
  "validate:owl:with-codelists":
    "python scripts/ontology_cli.py validate owl --include-codelists",
  "validate:shacl": "python scripts/ontology_cli.py validate shacl",
  "validate:shacl:list": "python scripts/ontology_cli.py validate shacl --list",
  "generate:types": "python scripts/ontology_cli.py generate types",
  "generate:types:verbose":
    "python scripts/ontology_cli.py generate types --verbose",
  "generate:wiki": "python scripts/ontology_cli.py generate wiki",
  "generate:wiki:with-codelists":
    "python scripts/ontology_cli.py generate wiki --include-codelists",
  "generate:wiki:verbose":
    "python scripts/ontology_cli.py generate wiki --verbose",
  "generate:build-index": "python scripts/ontology_cli.py generate build-index",
  "generate:json-schema": "python scripts/ontology_cli.py convert json-schema",
  "convert:context": "python scripts/ontology_cli.py convert context",
  "convert:ts": "python scripts/ontology_cli.py convert ts",
  "release:version": "python scripts/release-version.py",
  "release:all": "python scripts/release-version.py --all",
  "config:show": "python scripts/show-config.py",
};

function showUsage() {
  console.log(`
Docker Wrapper - Build and run ontology tools in Docker

Usage:
  node docker.js build                Build the Docker image
  node docker.js run <script> [args]  Run a script in Docker
  node docker.js shell                Open interactive bash shell

Available scripts:
  ${Object.keys(SCRIPT_COMMANDS).join("\n  ")}

Examples:
  node docker.js build
  node docker.js run config:show
  node docker.js run generate:types
  node docker.js run validate:owl:with-codelists
  node docker.js run cli -- validate shacl -d data.ttl -s shapes.ttl
  node docker.js shell
`);
  process.exit(1);
}

function build() {
  console.log("🐳 Building Docker image:", IMAGE_NAME);

  const workspaceRoot = path.resolve(__dirname, "..");

  try {
    execSync(
      `docker build -t ${IMAGE_NAME} -f ${DOCKERFILE} ${workspaceRoot}`,
      {
        stdio: "inherit",
        shell: true,
      },
    );

    console.log("\n✅ Docker image built successfully!");
  } catch (error) {
    console.error("\n❌ Build failed!");
    process.exit(1);
  }
}

function run(scriptName, ...args) {
  if (!scriptName) {
    console.error("❌ Error: script name required");
    showUsage();
  }

  const command = SCRIPT_COMMANDS[scriptName];
  if (!command) {
    console.error(`❌ Unknown script: ${scriptName}`);
    console.error(
      "Available scripts:",
      Object.keys(SCRIPT_COMMANDS).join(", "),
    );
    process.exit(1);
  }

  // Special handling for validate:shacl - convert positional args to flags
  if (
    scriptName === "validate:shacl" &&
    args.length >= 2 &&
    !args[0].startsWith("-")
  ) {
    // User passed: npm run validate:shacl -- data.ttl shapes.ttl
    // Convert to: -d data.ttl -s shapes.ttl
    args = ["-d", args[0], "-s", args[1], ...args.slice(2)];
  }

  // Special handling for generate:json-schema - convert positional args to flags
  if (
    scriptName === "generate:json-schema" &&
    args.length >= 2 &&
    !args[0].startsWith("-")
  ) {
    // User passed: npm run generate:json-schema -- input.ttl output.json
    // Convert to: -i input.ttl -o output.json
    args = ["-i", args[0], "-o", args[1], ...args.slice(2)];
  }

  // Special handling for convert:context - convert positional args to flags
  if (
    scriptName === "convert:context" &&
    args.length >= 2 &&
    !args[0].startsWith("-")
  ) {
    // User passed: npm run convert:context -- input.ttl output.jsonld
    // Convert to: -i input.ttl -o output.jsonld
    args = ["-i", args[0], "-o", args[1], ...args.slice(2)];
  }

  // Special handling for convert:ts - convert positional args to flags
  if (
    scriptName === "convert:ts" &&
    args.length >= 2 &&
    !args[0].startsWith("-")
  ) {
    // User passed: npm run convert:ts -- input.json output.ts
    // Convert to: -i input.json -o output.ts
    args = ["-i", args[0], "-o", args[1], ...args.slice(2)];
  }

  const workspaceRoot = path.resolve(__dirname, "..");
  const commandParts = command.split(" ");
  const allArgs = [...commandParts, ...args];

  console.log("🐳 Running in Docker:", allArgs.join(" "));

  // Build docker run command - properly escape arguments for shell
  const escapedArgs = allArgs
    .map((arg) => {
      // Quote arguments that contain spaces or special chars
      if (arg.includes(" ") || arg.includes("|") || arg.includes("&")) {
        return `"${arg}"`;
      }
      return arg;
    })
    .join(" ");

  const cmd = `docker run --rm -v "${workspaceRoot}:/workspace" -w /workspace ${IMAGE_NAME} ${escapedArgs}`;

  try {
    execSync(cmd, { stdio: "inherit", shell: true });
  } catch (error) {
    if (error.status) {
      process.exit(error.status);
    }
    console.error("❌ Error running Docker:", error.message);
    process.exit(1);
  }
}

function shell() {
  console.log("🐳 Opening interactive shell in Docker container...");

  const workspaceRoot = path.resolve(__dirname, "..");
  const cmd = `docker run --rm -it -v "${workspaceRoot}:/workspace" -w /workspace ${IMAGE_NAME} bash`;

  try {
    execSync(cmd, { stdio: "inherit", shell: true });
  } catch (error) {
    process.exit(error.status || 1);
  }
}

// Main
const command = process.argv[2];

if (!command) {
  showUsage();
}

switch (command) {
  case "build":
    build();
    break;
  case "run":
    run(...process.argv.slice(3));
    break;
  case "shell":
    shell();
    break;
  case "help":
  case "--help":
  case "-h":
    showUsage();
    break;
  default:
    console.error(`❌ Unknown command: ${command}`);
    showUsage();
}
