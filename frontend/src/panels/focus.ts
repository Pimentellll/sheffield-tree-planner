/** Stable focus targets for actions that remove the control the user just used. */
export const FOCUS_TARGET = {
  /** The scenario strip's "Edit scenario" toggle: always present while a scenario is loaded. */
  editorToggle: 'scenario-editor-toggle',
  /** The draft change list in the scenario editor. */
  draftChanges: 'draft-changes',
} as const

/** Move focus once React has committed the change (the clicked button may no longer exist). */
export function focusAfterRender(id: string): void {
  requestAnimationFrame(() => document.getElementById(id)?.focus())
}
