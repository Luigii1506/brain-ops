import { execFile } from "node:child_process";
import { promisify } from "node:util";

import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

const execFileAsync = promisify(execFile);

type BrainOpsConfig = {
  brainCommand?: string;
  workingDirectory?: string;
  configPath?: string;
};

type ToolSpec = {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  buildArgs: (input: Record<string, unknown>, cfg: BrainOpsConfig) => string[];
};

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function buildSharedArgs(cfg: BrainOpsConfig): string[] {
  const args: string[] = [];
  if (cfg.configPath) {
    args.push("--config", cfg.configPath);
  }
  args.push("--session-id", "telegram-main");
  return args;
}

async function runBrainOps(cfg: BrainOpsConfig, args: string[]) {
  const command = cfg.brainCommand || "/opt/anaconda3/bin/brain";
  const cwd = cfg.workingDirectory || process.cwd();
  const { stdout, stderr } = await execFileAsync(command, args, {
    cwd,
    env: {
      ...process.env,
      PYTHONPATH: process.env.PYTHONPATH || "src",
      PATH: ["/opt/anaconda3/bin", process.env.PATH || ""].filter(Boolean).join(":"),
    },
  });

  const trimmed = stdout.trim();
  const parsed = trimmed ? JSON.parse(trimmed) : {};
  return {
    ok: true,
    command,
    args,
    cwd,
    data: parsed,
    stderr: stderr.trim() || undefined,
  };
}

function asToolContent(result: unknown) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(result, null, 2),
      },
    ],
  };
}

const tools: ToolSpec[] = [
  {
    name: "brain_ops_handle_input",
    description: "MANDATORY first tool for personal operational requests. Use this before answering for daily status, meals, diet, macros, supplements, habits, workouts, expenses, body metrics, goals, reflections, and queries like 'como voy hoy' or 'que me falta hoy'.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["text"],
      properties: {
        text: { type: "string", description: "Natural-language user message." },
        useLlm: { type: "boolean", description: "Allow Ollama-assisted routing." },
        dryRun: { type: "boolean", description: "Preview without side effects." },
      },
    },
    buildArgs: (input, cfg) => {
      const text = asString(input.text) || "";
      const args = ["handle-input", text, "--json", ...buildSharedArgs(cfg)];
      if (input.dryRun) args.push("--dry-run");
      if (input.useLlm === true) args.push("--use-llm");
      if (input.useLlm === false) args.push("--no-use-llm");
      return args;
    },
  },
];

const plugin = {
  id: "brain-ops",
  name: "brain-ops",
  description: "Expose brain-ops as deterministic OpenClaw tools for Telegram-first Jarvis workflows.",
  configSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      brainCommand: { type: "string", description: "CLI executable used to run brain-ops." },
      workingDirectory: { type: "string", description: "Repository root or working directory where brain-ops should run." },
      configPath: { type: "string", description: "Optional path to the vault YAML config file." },
    },
  },
  register(api: OpenClawPluginApi) {
    const cfg = (api.config || {}) as BrainOpsConfig;

    for (const tool of tools) {
      api.registerTool({
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
        async execute(_id: string, input: Record<string, unknown>) {
          const result = await runBrainOps(cfg, tool.buildArgs(input, cfg));
          return asToolContent(result);
        },
      });
    }
  },
};

export default plugin;
