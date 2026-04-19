import { appendFile, mkdir, readFile, stat, unlink, writeFile } from "fs/promises"
import { dirname, join, resolve } from "path"
import { tool, type Plugin } from "@opencode-ai/plugin"

type State = {
  active: boolean
  sessionId?: string
  projectPath?: string
  originalTask?: string
  completed?: string
  nextSteps?: string
  iteration: number
  maxIterations: number
}

const STATE_FILE = "chatloop.local.md"
const EVENTS_FILE = "chatloop.events.log"
const COMPLETE_RE = /^\s*<complete>\s*DONE\s*<\/complete>\s*$/im
const STATUS_COMPLETE_RE = /^\s*STATUS:\s*COMPLETE\s*$/im
const STATUS_IN_PROGRESS_RE = /^\s*STATUS:\s*IN_PROGRESS\s*$/im
const IDLE_DEBOUNCE_MS = 1500

const statePath = (projectPath: string) => join(projectPath, ".opencode", STATE_FILE)
const eventsPath = (projectPath: string) => join(projectPath, ".opencode", EVENTS_FILE)
const prdPath = (projectPath: string) => join(projectPath, "PRD.md")
const optionalContextPaths = (projectPath: string) => ["memory.md", "progress.md"].map((name) => join(projectPath, name))

const describeError = (error: unknown) => {
  if (error instanceof Error) return `${error.name}: ${error.message}`
  return String(error)
}

const stripCodeFences = (text: string) =>
  text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`[^`]+`/g, "")

const normalizeMultiline = (value?: string) => {
  const trimmed = value?.trim()
  return trimmed ? trimmed : undefined
}

const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")

const extractSection = (title: string, text: string) => {
  const match = text.match(new RegExp(`^##\\s*${escapeRegex(title)}\\s*\\n([\\s\\S]*?)(?=\\n##\\s|$)`, "im"))
  return normalizeMultiline(match?.[1])
}

const extractNextSteps = (text: string) => {
  const cleaned = stripCodeFences(text)
  const section = extractSection("Next Steps", cleaned)
  if (section) return section

  const unchecked = cleaned
    .split("\n")
    .filter((line) => /^\s*-\s*\[ \]/.test(line))
    .map((line) => line.trim())
  return normalizeMultiline(unchecked.join("\n"))
}

const extractCompleted = (text: string) => {
  const cleaned = stripCodeFences(text)
  const section = extractSection("Completed", cleaned)
  if (section) return section

  const checked = cleaned
    .split("\n")
    .filter((line) => /^\s*-\s*\[x\]/i.test(line))
    .map((line) => line.trim())
  return normalizeMultiline(checked.join("\n"))
}

const mergeCompleted = (existing?: string, incoming?: string) => {
  if (!existing) return incoming
  if (!incoming) return existing

  const lines = existing
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
  const seen = new Set(lines.map((line) => line.replace(/^\s*-\s*\[x\]\s*/i, "").trim().toLowerCase()))

  incoming
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const normalized = line.replace(/^\s*-\s*\[x\]\s*/i, "").trim().toLowerCase()
      if (seen.has(normalized)) return
      seen.add(normalized)
      lines.push(line)
    })

  return normalizeMultiline(lines.join("\n"))
}

const getStatusSignals = (text: string) => {
  const cleaned = stripCodeFences(text)
  return {
    hasComplete: STATUS_COMPLETE_RE.test(cleaned),
    hasInProgress: STATUS_IN_PROGRESS_RE.test(cleaned),
  }
}

const hasUncheckedNextSteps = (text: string) => {
  const nextSteps = extractNextSteps(text)
  if (!nextSteps) return false
  return nextSteps
    .split("\n")
    .some((line) => /^\s*-\s*\[ \]/.test(line))
}

const validateCompletion = (text: string, iteration: number) => {
  if (iteration <= 0) {
    return { valid: false, reason: "bootstrap iteration cannot complete" }
  }
  if (!COMPLETE_RE.test(stripCodeFences(text))) {
    return { valid: false, reason: "missing completion tag" }
  }

  const signals = getStatusSignals(text)
  if (signals.hasInProgress) {
    return { valid: false, reason: "STATUS: IN_PROGRESS contradicts completion" }
  }
  if (!signals.hasComplete) {
    return { valid: false, reason: "missing STATUS: COMPLETE" }
  }
  if (hasUncheckedNextSteps(text)) {
    return { valid: false, reason: "unchecked next steps remain" }
  }
  return { valid: true }
}

const parseFrontmatterValue = (text: string, key: string) =>
  normalizeMultiline(text.match(new RegExp(`^${escapeRegex(key)}:\\s*(.+)$`, "m"))?.[1])

const serializeState = (state: State) => {
  const lines = [
    "---",
    `active: ${state.active}`,
    `iteration: ${state.iteration}`,
    `maxIterations: ${state.maxIterations}`,
    state.sessionId ? `sessionId: ${state.sessionId}` : "",
    state.projectPath ? `projectPath: ${state.projectPath}` : "",
    "---",
  ].filter(Boolean)

  if (state.originalTask) {
    lines.push("", "## Original Task", state.originalTask)
  }
  if (state.completed) {
    lines.push("", "## Completed", state.completed)
  }
  if (state.nextSteps) {
    lines.push("", "## Next Steps", state.nextSteps)
  }

  return `${lines.join("\n")}\n`
}

const readState = async (projectPath: string): Promise<State> => {
  try {
    const text = await readFile(statePath(projectPath), "utf-8")
    const body = text.split(/^---$/m).slice(2).join("---").trim()
    return {
      active: /active:\s*true/.test(text),
      sessionId: parseFrontmatterValue(text, "sessionId"),
      projectPath: parseFrontmatterValue(text, "projectPath") ?? projectPath,
      originalTask: extractSection("Original Task", body),
      completed: extractSection("Completed", body),
      nextSteps: extractSection("Next Steps", body),
      iteration: Number(text.match(/iteration:\s*(\d+)/m)?.[1] ?? 0),
      maxIterations: Number(text.match(/maxIterations:\s*(\d+)/m)?.[1] ?? 20),
    }
  } catch {
    return { active: false, iteration: 0, maxIterations: 20, projectPath }
  }
}

const writeState = async (projectPath: string, state: State) => {
  await mkdir(dirname(statePath(projectPath)), { recursive: true })
  await writeFile(statePath(projectPath), serializeState(state), "utf-8")
}

const clearState = async (projectPath: string) => {
  await unlink(statePath(projectPath)).catch(() => {})
}

const exists = async (path: string) => {
  try {
    await stat(path)
    return true
  } catch {
    return false
  }
}

const resolveProjectPath = async (directory: string) => {
  let current = resolve(directory)
  while (true) {
    const prd = prdPath(current)
    if (await exists(prd)) {
      return { projectPath: current, prdPath: prd }
    }
    const parent = dirname(current)
    if (parent === current) {
      throw new Error(`No PRD.md found in ${resolve(directory)} or its parent directories. ChatLoop requires a project root with PRD.md.`)
    }
    current = parent
  }
}

const tryResolveProjectPath = async (directory: string) => {
  try {
    return await resolveProjectPath(directory)
  } catch {
    return undefined
  }
}

const getLastAssistantText = async (client: any, sessionId: string, directory: string) => {
  const response = await client.session.messages({
    path: { id: sessionId },
    query: { directory, limit: 10 },
  })
  const messages = response.data ?? []
  const assistantMessages = messages.filter((message: any) => message.info?.role === "assistant")
  const lastAssistant = assistantMessages[assistantMessages.length - 1]
  if (!lastAssistant) return ""
  return (lastAssistant.parts || [])
    .filter((part: any) => part.type === "text")
    .map((part: any) => part.text ?? "")
    .join("\n")
}

const appendEvent = async (projectPath: string, sessionId: string | undefined, level: string, event: string, detail: string) => {
  await mkdir(dirname(eventsPath(projectPath)), { recursive: true })
  const sessionPart = sessionId ? ` | session=${sessionId}` : ""
  await appendFile(
    eventsPath(projectPath),
    `${new Date().toISOString()} | ${level.padEnd(5)} | ${event}${sessionPart} | ${detail}\n`,
    "utf-8",
  )
}

const buildProgressSection = (state: State) => {
  if (!state.completed && !state.nextSteps) {
    return "No structured progress recorded yet. Review the current repo state and keep moving toward the PRD completion criteria."
  }

  const sections = []
  if (state.completed) {
    sections.push(`## Completed\n${state.completed}`)
  }
  if (state.nextSteps) {
    sections.push(`## Next Steps\n${state.nextSteps}`)
  }
  return sections.join("\n\n")
}

const buildLoopPrompt = (state: State, projectPath: string, iteration: number, mode: "bootstrap" | "continue" | "compacted") => {
  const title =
    mode === "bootstrap"
      ? `[CHATLOOP ACTIVE — Iteration ${iteration}/${state.maxIterations}]`
      : mode === "compacted"
        ? `[CHATLOOP CONTEXT RESTORED — Iteration ${iteration}/${state.maxIterations}]`
        : `[CHATLOOP CONTINUE — Iteration ${iteration}/${state.maxIterations}]`
  const action =
    mode === "bootstrap"
      ? "Begin working on the task now under the PRD contract below."
      : mode === "compacted"
        ? "Session context was compacted. Re-read the PRD and continue from the latest structured progress below."
        : "Continue working on the task. Do not stop unless the completion gate is truly satisfied."

  return [
    title,
    action,
    `Project path: ${projectPath}`,
    `Required entry file: ${prdPath(projectPath)}`,
    `Optional files to inspect if useful: ${optionalContextPaths(projectPath).join(", ")}`,
    "",
    "IMPORTANT RULES:",
    "- Read PRD.md from scratch before doing anything else.",
    "- If memory.md or progress.md exist and are useful, re-read them from scratch as well.",
    "- Do not rely on prior chat context. Use the current filesystem state as the source of truth.",
    "- Do NOT call the chatloop tool again. The plugin handles continuation automatically.",
    "- Do NOT call /chatloop-status or explain that ChatLoop started unless the user explicitly asked for diagnostics.",
    "- Start acting on the repository immediately instead of summarizing the loop setup.",
    "- Pick up from the next incomplete step below and keep moving toward the PRD completion criteria.",
    "- Before going idle each iteration, output structured progress in this exact shape:",
    "",
    "```",
    "## Completed",
    "- [x] What finished this iteration",
    "",
    "## Next Steps",
    "- [ ] What remains, in priority order",
    "",
    "STATUS: IN_PROGRESS",
    "```",
    "",
    mode === "bootstrap"
      ? "- In this bootstrap iteration, you MUST use STATUS: IN_PROGRESS and you MUST NOT output STATUS: COMPLETE or <complete>DONE</complete>."
      : "- You MUST include either STATUS: IN_PROGRESS or STATUS: COMPLETE on its own line in every response.",
    mode === "bootstrap"
      ? "- Use the bootstrap iteration to start doing the work and establish the first structured Next Steps list."
      : "- You MUST NOT output <complete>DONE</complete> if there are any unchecked items (- [ ]) in Next Steps.",
    "- Only when every PRD requirement is satisfied and Next Steps is empty may you output both:",
    "  STATUS: COMPLETE",
    "  <complete>DONE</complete>",
    "- If completion is invalid, the plugin will reject it and continue the loop.",
    "",
    `Original task: ${state.originalTask?.trim() ? state.originalTask : "(no explicit task text; derive the task solely from PRD.md)"}`,
    "",
    buildProgressSection(state),
  ].join("\n")
}

const isSessionBusy = async (client: any, sessionId: string) => {
  try {
    const response = await client.session.status({})
    const statuses = response.data ?? {}
    const status = statuses[sessionId]
    return Boolean(status && status.type !== "idle")
  } catch {
    return false
  }
}

const formatStatus = async (directory: string, sessionId?: string) => {
  try {
    const { projectPath, prdPath: entryPath } = await resolveProjectPath(directory)
    const state = await readState(projectPath)
    const sessionMatches = !sessionId || !state.sessionId ? "unknown" : state.sessionId === sessionId ? "yes" : "no"
    const armed = state.active && (sessionMatches === "yes" || sessionMatches === "unknown")
    const pending = state.nextSteps
      ?.split("\n")
      .filter((line) => /^\s*-\s*\[ \]/.test(line))
      .length ?? 0
    return [
      "ChatLoop status:",
      "- Loaded: yes (this command is available)",
      `- Project root: ${projectPath}`,
      `- PRD entry: ${entryPath}`,
      `- State file: ${statePath(projectPath)}`,
      `- Events file: ${eventsPath(projectPath)}`,
      `- Completion marker: <complete>DONE</complete>`,
      `- State active flag: ${state.active ? "yes" : "no"}`,
      `- Armed for continuation: ${armed ? "yes" : "no"}`,
      `- Iteration: ${state.iteration}/${state.maxIterations}`,
      `- Structured next steps pending: ${pending}`,
      state.sessionId ? `- State session: ${state.sessionId}` : "",
      sessionId ? `- Current session: ${sessionId}` : "",
      sessionId ? `- Current session matches state: ${sessionMatches}` : "",
      state.originalTask ? `- Original task stored: yes` : `- Original task stored: no`,
      "- Use /chatloop to start, /chatloop-stop to stop, /chatloop-help for workflow details.",
    ]
      .filter(Boolean)
      .join("\n")
  } catch (error) {
    return [
      "ChatLoop status:",
      "- Loaded: yes (this command is available)",
      "- Active project: not found",
      `- Reason: ${describeError(error)}`,
      "- Run /chatloop inside a project directory that contains PRD.md or a subdirectory beneath it.",
    ].join("\n")
  }
}

const chatloop: Plugin = async (ctx) => {
  let handlingIdle = false
  let lastContinuationAt = 0

  const toast = (message: string, variant: "info" | "success" | "warning" | "error" = "info") => {
    try {
      ctx.client.tui.showToast({
        body: { message, variant },
      })
    } catch {
      // Non-critical UI feedback only.
    }
  }

  const handleIdleTrigger = async (projectPath: string, sessionId: string, source: string) => {
    if (handlingIdle) {
      await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.idle.skip", `source=${source} reason=handler_busy`)
      return
    }

    handlingIdle = true
    try {
      const state = await readState(projectPath)
      await appendEvent(
        projectPath,
        sessionId,
        "DEBUG",
        "chatloop.idle.observe",
        `source=${source} active=${state.active} state_session=${state.sessionId ?? "-"} iteration=${state.iteration}/${state.maxIterations}`,
      )

      if (!state.active) {
        await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.idle.skip", `source=${source} reason=inactive_state`)
        return
      }
      if (state.sessionId && state.sessionId !== sessionId) {
        await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.idle.skip", `source=${source} reason=session_mismatch state_session=${state.sessionId}`)
        return
      }
      if (Date.now() - lastContinuationAt < IDLE_DEBOUNCE_MS) {
        await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.idle.skip", `source=${source} reason=debounced delta_ms=${Date.now() - lastContinuationAt}`)
        return
      }
      if (await isSessionBusy(ctx.client, sessionId)) {
        await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.idle.skip", `source=${source} reason=session_not_idle`)
        return
      }

      const lastText = await getLastAssistantText(ctx.client, sessionId, ctx.directory)
      await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.idle.last_text", `source=${source} chars=${lastText.length}`)

      if (state.iteration > 0 && COMPLETE_RE.test(stripCodeFences(lastText))) {
        const validation = validateCompletion(lastText, state.iteration)
        if (validation.valid) {
          await appendEvent(projectPath, sessionId, "INFO", "chatloop.complete", `source=${source} iteration=${state.iteration}`)
          await clearState(projectPath)
          lastContinuationAt = 0
          toast(`ChatLoop completed after ${state.iteration} iteration(s)`, "success")
          return
        }
        await appendEvent(projectPath, sessionId, "WARN", "chatloop.complete.rejected", `source=${source} reason=${validation.reason}`)
        toast(`ChatLoop: completion rejected — ${validation.reason}`, "warning")
      }

      if (state.iteration >= state.maxIterations) {
        await appendEvent(projectPath, sessionId, "WARN", "chatloop.max_iterations", `source=${source} iteration=${state.iteration}`)
        await clearState(projectPath)
        lastContinuationAt = 0
        toast(`ChatLoop stopped — max iterations (${state.maxIterations}) reached`, "warning")
        return
      }

      const nextState: State = {
        ...state,
        iteration: state.iteration + 1,
        completed: mergeCompleted(state.completed, extractCompleted(lastText)),
        nextSteps: extractNextSteps(lastText) ?? state.nextSteps,
      }
      await writeState(projectPath, nextState)
      await appendEvent(
        projectPath,
        sessionId,
        "DEBUG",
        "chatloop.state.updated",
        `source=${source} iteration=${nextState.iteration}/${nextState.maxIterations} completed=${nextState.completed ? "yes" : "no"} next_steps=${nextState.nextSteps ? "yes" : "no"}`,
      )

      const prompt = buildLoopPrompt(nextState, projectPath, nextState.iteration, "continue")
      await appendEvent(projectPath, sessionId, "INFO", "chatloop.idle", `source=${source} sending continuation iteration=${nextState.iteration}`)
      await ctx.client.session.promptAsync({
        path: { id: sessionId },
        body: { parts: [{ type: "text", text: prompt }] },
      })
      lastContinuationAt = Date.now()
      await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.idle.prompt_sent", `source=${source} iteration=${nextState.iteration}`)
      toast(`ChatLoop iteration ${nextState.iteration}/${nextState.maxIterations}`, "info")
    } catch (error) {
      await appendEvent(projectPath, sessionId, "ERROR", "chatloop.idle.error", `source=${source} ${describeError(error)}`)
      toast(`ChatLoop: idle continuation failed — ${describeError(error)}`, "error")
    } finally {
      handlingIdle = false
    }
  }

  const start = tool({
    description: "Start a PRD-aware auto-continuation loop in the current directory",
    args: {
      message: tool.schema.string().optional().describe("Original task text to preserve alongside the PRD contract"),
      maxIterations: tool.schema.number().optional().describe("Maximum loop iterations"),
    },
    async execute({ message = "", maxIterations = 20 }, context) {
      const { projectPath, prdPath: entryPath } = await resolveProjectPath(ctx.directory)
      const existingState = await readState(projectPath)
      if (existingState.active && existingState.sessionId === context.sessionID) {
        await appendEvent(projectPath, context.sessionID, "WARN", "chatloop.start.ignored", `reason=already_active iteration=${existingState.iteration}/${existingState.maxIterations}`)
        toast(`ChatLoop already active (${existingState.iteration}/${existingState.maxIterations})`, "warning")
        return `ChatLoop is ALREADY ACTIVE (${existingState.iteration}/${existingState.maxIterations}). Do NOT call /chatloop again. Keep working under the existing PRD loop or stop it first with /chatloop-stop.`
      }

      const state: State = {
        active: true,
        sessionId: context.sessionID,
        projectPath,
        originalTask: normalizeMultiline(message),
        iteration: 0,
        maxIterations,
      }
      await writeState(projectPath, state)
      handlingIdle = false
      lastContinuationAt = 0
      await appendEvent(projectPath, context.sessionID, "INFO", "chatloop.start", `project=${projectPath} cwd=${resolve(ctx.directory)} maxIterations=${maxIterations}`)
      await appendEvent(projectPath, context.sessionID, "INFO", "chatloop.start.prompt", `mode=bootstrap prd=${entryPath} original_task=${state.originalTask ? "yes" : "no"}`)
      const prompt = buildLoopPrompt(state, projectPath, 0, "bootstrap")
      await ctx.client.session.promptAsync({
        path: { id: context.sessionID },
        body: { parts: [{ type: "text", text: prompt }] },
      })
      lastContinuationAt = Date.now()
      await appendEvent(projectPath, context.sessionID, "INFO", "chatloop.start.prompt_sent", `iteration=0/${maxIterations}`)

      return ""
    },
  })

  const stop = tool({
    description: "Stop chat loop",
    args: {},
    async execute(_args, context) {
      const resolved = await tryResolveProjectPath(ctx.directory)
      if (!resolved) return "No active ChatLoop project found from the current directory."
      const state = await readState(resolved.projectPath)
      if (state.sessionId && state.sessionId !== context.sessionID) return "No active ChatLoop in this session."
      await clearState(resolved.projectPath)
      handlingIdle = false
      lastContinuationAt = 0
      await appendEvent(resolved.projectPath, context.sessionID, "INFO", "chatloop.stop", "stopped by user")
      toast("ChatLoop stopped", "warning")
      return "ChatLoop stopped."
    },
  })

  const help = tool({
    description: "Explain how chatloop works",
    args: {},
    async execute() {
      return [
        "ChatLoop usage:",
        "- /chatloop <message> starts a PRD-aware auto-continuation loop in the current directory or the nearest parent that contains PRD.md.",
        "- The initial message is preserved as the original task, but startup ALWAYS injects the PRD contract, project path, and PRD entry path.",
        "- On each idle checkpoint, ChatLoop auto-continues with structured progress, completion validation, and the same PRD contract.",
        "- Every iteration must include ## Completed, ## Next Steps, and either STATUS: IN_PROGRESS or STATUS: COMPLETE.",
        "- ChatLoop only stops when STATUS: COMPLETE and <complete>DONE</complete> are both present and Next Steps has no unchecked items.",
        "- State is written to .opencode/chatloop.local.md under the resolved project root.",
        "- Event records are appended to .opencode/chatloop.events.log under the resolved project root.",
        "- Use /chatloop-status to verify the resolved project root, state file, events file, and whether the current session is armed for continuation.",
      ].join("\n")
    },
  })

  const status = tool({
    description: "Show chatloop status and debug paths",
    args: {},
    async execute(_args, context) {
      return formatStatus(ctx.directory, context.sessionID)
    },
  })

  return {
    tool: {
      chatloop: start,
      "chatloop-status": status,
      "chatloop-stop": stop,
      "chatloop-help": help,
    },
    event: async ({ event }) => {
      const resolved = await tryResolveProjectPath(ctx.directory)
      if (!resolved) return
      const sessionId = (event as any).properties?.sessionID as string | undefined
      const projectPath = resolved.projectPath

      try {
        if (event.type === "command.executed") {
          await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.observe.command.executed", `name=${(event as any).properties?.name ?? "-"} arguments=${(event as any).properties?.arguments ?? ""}`)
          return
        }

        if (event.type === "session.status") {
          const status = (event as any).properties?.status?.type ?? "unknown"
          await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.observe.session.status", `status=${status}`)
          if (status === "idle" && sessionId) {
            await handleIdleTrigger(projectPath, sessionId, "session.status")
          }
          return
        }

        if (event.type === "session.idle") {
          await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.observe.session.idle", "received session.idle event")
          if (sessionId) {
            await handleIdleTrigger(projectPath, sessionId, "session.idle")
          }
          return
        }

        if (event.type === "session.compacted") {
          await appendEvent(projectPath, sessionId, "WARN", "chatloop.observe.session.compacted", "session compacted")
          const state = await readState(projectPath)
          if (!state.active || !sessionId) return
          if (state.sessionId && state.sessionId !== sessionId) return
          const reminder = buildLoopPrompt(state, projectPath, state.iteration, "compacted")
          await ctx.client.session.promptAsync({
            path: { id: sessionId },
            body: { parts: [{ type: "text", text: reminder }] },
          })
          await appendEvent(projectPath, sessionId, "INFO", "chatloop.compacted.prompt_sent", `iteration=${state.iteration}`)
          toast(`ChatLoop context restored after compaction (${state.iteration}/${state.maxIterations})`, "info")
          return
        }

        if (event.type === "session.error") {
          await appendEvent(projectPath, sessionId, "ERROR", "chatloop.observe.session.error", describeError((event as any).properties?.error))
          const state = await readState(projectPath)
          if (state.active && (!state.sessionId || !sessionId || state.sessionId === sessionId)) {
            await writeState(projectPath, { ...state, active: false })
            handlingIdle = false
            lastContinuationAt = 0
            await appendEvent(projectPath, sessionId, "WARN", "chatloop.pause", `reason=session.error iteration=${state.iteration}`)
            toast(`ChatLoop paused — session error at iteration ${state.iteration}`, "error")
          }
          return
        }

        if (event.type === "session.deleted") {
          await appendEvent(projectPath, sessionId, "WARN", "chatloop.observe.session.deleted", `deleted_session=${(event as any).properties?.info?.id ?? sessionId ?? "-"}`)
          const state = await readState(projectPath)
          const deletedSessionId = (event as any).properties?.info?.id as string | undefined
          if (state.active && (!state.sessionId || !deletedSessionId || state.sessionId === deletedSessionId)) {
            await clearState(projectPath)
            handlingIdle = false
            lastContinuationAt = 0
            await appendEvent(projectPath, deletedSessionId, "INFO", "chatloop.cleanup", "cleared state after session deletion")
            toast("ChatLoop cleaned up after session deletion", "warning")
          }
          return
        }

        if (event.type === "permission.asked") {
          await appendEvent(
            projectPath,
            sessionId,
            "WARN",
            "chatloop.observe.permission.asked",
            `permission=${(event as any).properties?.permission ?? "-"} patterns=${((event as any).properties?.patterns ?? []).join(",")}`,
          )
          return
        }

        if (event.type === "message.updated") {
          const info = (event as any).properties?.info
          if ((event as any).properties?.sessionID === sessionId && info?.role === "assistant") {
            await appendEvent(projectPath, sessionId, "DEBUG", "chatloop.observe.message.updated", `role=assistant finish=${info?.finish ?? "-"} model=${info?.modelID ?? "-"}`)
          }
          return
        }

        if (event.type === "message.part.updated") {
          const part = (event as any).properties?.part
          if (!part?.sessionID) return
          if (part.type === "text" && part.time?.end) {
            await appendEvent(projectPath, part.sessionID, "DEBUG", "chatloop.observe.message.part.text", `text_completed chars=${String(part.text ?? "").length}`)
            return
          }
          if (part.type === "tool") {
            await appendEvent(projectPath, part.sessionID, "DEBUG", "chatloop.observe.message.part.tool", `tool=${part.tool} status=${part.state?.status ?? "unknown"}`)
          }
        }
      } catch (error) {
        await appendEvent(projectPath, sessionId, "ERROR", "chatloop.observe.error", `event=${event.type} ${describeError(error)}`)
      }
    },
  }
}

export default { id: "local.chatloop", server: chatloop }
