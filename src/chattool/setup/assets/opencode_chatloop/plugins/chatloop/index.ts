import { appendFile, mkdir, readFile, stat, unlink, writeFile } from "fs/promises"
import { dirname, join, resolve } from "path"
import { tool, type Plugin } from "@opencode-ai/plugin"

type State = {
  active: boolean
  sessionId?: string
  projectPath?: string
  iteration: number
  maxIterations: number
  initialMessage?: string
}

const STATE_FILE = "chatloop.local.md"
const COMPLETE_RE = /<complete>DONE<\/complete>/i

const statePath = (directory: string) => join(directory, ".opencode", STATE_FILE)
const logPath = (directory: string, sessionId: string) => join(directory, ".opencode", "logs", `${sessionId}.log`)

const parseStoredString = (value?: string) => {
  if (!value) return undefined
  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

const readState = async (directory: string): Promise<State> => {
  try {
    const text = await readFile(statePath(directory), "utf-8")
    const body = text.split(/^---$/m)[2] ?? ""
    const active = /active:\s*true/.test(text)
    const sessionId = text.match(/sessionId:\s*(.+)$/m)?.[1]?.trim()
    const projectPath = text.match(/projectPath:\s*(.+)$/m)?.[1]?.trim()
    const initialMessage = parseStoredString(text.match(/initialMessage:\s*(.+)$/m)?.[1]?.trim())
    const iteration = Number(text.match(/iteration:\s*(\d+)/m)?.[1] ?? 0)
    const maxIterations = Number(text.match(/maxIterations:\s*(\d+)/m)?.[1] ?? 20)
    return {
      active,
      sessionId,
      projectPath: projectPath || body.trim() || undefined,
      initialMessage,
      iteration,
      maxIterations,
    }
  } catch {
    return { active: false, iteration: 0, maxIterations: 20 }
  }
}

const writeState = async (directory: string, state: State) => {
  await mkdir(dirname(statePath(directory)), { recursive: true })
  await writeFile(
    statePath(directory),
    `---\nactive: ${state.active}\niteration: ${state.iteration}\nmaxIterations: ${state.maxIterations}\n${state.sessionId ? `sessionId: ${state.sessionId}\n` : ""}${state.projectPath ? `projectPath: ${state.projectPath}\n` : ""}${state.initialMessage ? `initialMessage: ${JSON.stringify(state.initialMessage)}\n` : ""}---\n\n${state.projectPath ?? ""}`,
    "utf-8",
  )
}

const clearState = async (directory: string) => {
  await unlink(statePath(directory)).catch(() => {})
}

const exists = async (path: string) => {
  try {
    await stat(path)
    return true
  } catch {
    return false
  }
}

const normalizeProjectPath = (directory: string) => resolve(directory)

const requirePrd = async (projectPath: string) => {
  const prd = join(projectPath, "PRD.md")
  if (!(await exists(prd))) throw new Error(`No PRD.md found in ${projectPath}. ChatLoop requires a project directory with PRD.md.`)
  return prd
}

const getLastAssistantText = async (client: any, sessionId: string) => {
  const response = await client.session.messages({
    path: { id: sessionId },
    query: { limit: 10 },
  })
  const messages = response.data ?? []
  const assistantMessages = messages.filter((msg: any) => msg.info?.role === "assistant")
  const lastAssistant = assistantMessages[assistantMessages.length - 1]
  if (!lastAssistant) return ""
  return (lastAssistant.parts || [])
    .filter((part: any) => part.type === "text")
    .map((part: any) => part.text ?? "")
    .join("\n")
}

const appendLog = async (directory: string, sessionId: string, level: string, event: string, detail: string) => {
  const target = logPath(directory, sessionId)
  await mkdir(dirname(target), { recursive: true })
  const line = `${new Date().toISOString()} | ${level} | ${event} | ${detail}\n`
  await appendFile(target, line, "utf-8")
}

const buildFreshStartPrompt = async (projectPath: string, iteration: number, initialMessage?: string) => {
  const optionalFiles = ["memory.md", "progress.md"]
    .map((name) => join(projectPath, name))
    .filter((_) => true)
  return [
    `Fresh start for iteration ${iteration}.`,
    "Read PRD.md from scratch before doing anything else.",
    "If memory.md or progress.md exist and are useful, re-read them from scratch as well.",
    "Do not rely on prior chat context. Use the current filesystem state as the source of truth.",
    initialMessage?.trim() ? `Original instruction:\n${initialMessage}` : "",
    "If the PRD is already satisfied, output exactly <complete>DONE</complete> on its own line.",
    `Project path: ${projectPath}`,
    `Required entry file: ${join(projectPath, "PRD.md")}`,
    optionalFiles.length ? `Optional files to inspect if useful: ${optionalFiles.join(", ")}` : "",
  ]
    .filter(Boolean)
    .join("\n\n")
}

const sendPrompt = async (client: any, sessionId: string, prompt: string) => {
  await client.session.promptAsync({
    path: { id: sessionId },
    body: { parts: [{ type: "text", text: prompt }] },
  })
}

const chatloop: Plugin = async (ctx) => {
  const start = tool({
    description: "Start PRD-driven chat loop in the current directory and send the user's message verbatim as the initial instruction",
    args: {
      message: tool.schema.string().optional().describe("Initial user message to forward verbatim"),
      maxIterations: tool.schema.number().optional().describe("Maximum loop iterations"),
    },
    async execute({ message = "", maxIterations = 20 }, context) {
      const projectPath = normalizeProjectPath(ctx.directory)
      await requirePrd(projectPath)
      const state: State = {
        active: true,
        sessionId: context.sessionID,
        projectPath,
        initialMessage: message,
        iteration: 1,
        maxIterations,
      }
      await writeState(ctx.directory, state)
      await appendLog(ctx.directory, context.sessionID, "INFO", "start", `path=${projectPath} maxIterations=${maxIterations}`)
      if (message.trim()) {
        await sendPrompt(ctx.client, context.sessionID, message)
        await appendLog(ctx.directory, context.sessionID, "INFO", "initial_message", "forwarded user message verbatim")
      } else {
        const prompt = await buildFreshStartPrompt(projectPath, 1)
        await sendPrompt(ctx.client, context.sessionID, prompt)
        await appendLog(ctx.directory, context.sessionID, "INFO", "initial_prompt", "started with PRD fresh-start prompt")
      }
      return `ChatLoop started for ${projectPath}.`
    },
  })

  const stop = tool({
    description: "Stop chat loop",
    args: {},
    async execute(_args, context) {
      const state = await readState(ctx.directory)
      if (state.sessionId && state.sessionId !== context.sessionID) return "No active ChatLoop in this session."
      await clearState(ctx.directory)
      if (context.sessionID) await appendLog(ctx.directory, context.sessionID, "INFO", "stop", "stopped by user")
      return "ChatLoop stopped."
    },
  })

  const help = tool({
    description: "Explain how chatloop works",
    args: {},
    async execute() {
      return [
        "ChatLoop usage:",
        "- /chatloop <message> starts a PRD-driven loop in the current directory.",
        "- The current directory must contain PRD.md.",
        "- The initial user message is forwarded verbatim when provided.",
        "- On each idle checkpoint, ChatLoop restarts from scratch by asking the model to re-read PRD.md and optional memory/progress files.",
        "- If the task is complete, the model must output <complete>DONE</complete>.",
        "- Logs are written to .opencode/logs/<session-id>.log.",
      ].join("\n")
    },
  })

  return {
    tool: {
      chatloop: start,
      "chatloop-stop": stop,
      "chatloop-help": help,
    },
    event: async ({ event }) => {
      if (event.type !== "session.idle") return
      const state = await readState(ctx.directory)
      if (!state.active || !state.sessionId || state.sessionId !== event.properties.sessionID) return
      if (state.iteration >= state.maxIterations) {
        await appendLog(ctx.directory, event.properties.sessionID, "WARN", "max_iterations", `iteration=${state.iteration}`)
        await clearState(ctx.directory)
        return
      }

      const lastText = await getLastAssistantText(ctx.client, event.properties.sessionID)
      if (COMPLETE_RE.test(lastText)) {
        await appendLog(ctx.directory, event.properties.sessionID, "INFO", "complete", "assistant emitted completion marker")
        await clearState(ctx.directory)
        return
      }

      const next = { ...state, iteration: state.iteration + 1 }
      await writeState(ctx.directory, next)
      const prompt = await buildFreshStartPrompt(state.projectPath || ctx.directory, next.iteration, state.initialMessage)
      await appendLog(ctx.directory, event.properties.sessionID, "INFO", "idle", `restarting fresh iteration=${next.iteration}`)
      await sendPrompt(ctx.client, event.properties.sessionID, prompt)
    },
  }
}

export default { id: "local.chatloop", server: chatloop }
