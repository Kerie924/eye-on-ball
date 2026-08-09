import type { DialogTone } from '../components/AppDialog'

interface MessageOptions {
  tone?: DialogTone
  confirmLabel?: string
}

interface ConfirmOptions {
  tone?: DialogTone
  confirmLabel?: string
  cancelLabel?: string
  destructive?: boolean
}

type DialogHandlers = {
  showMessage: (title: string, message: string, options?: MessageOptions) => Promise<void>
  confirmAction: (
    title: string,
    message: string,
    options?: ConfirmOptions,
  ) => Promise<boolean>
}

let handlers: DialogHandlers | null = null

export function bindDialogHandlers(next: DialogHandlers | null) {
  handlers = next
}

/**
 * Imperative helpers used across screens.
 * Requires DialogProvider to be mounted in the root layout.
 */
export async function showMessage(
  title: string,
  message: string,
  options?: MessageOptions,
): Promise<void> {
  if (!handlers) {
    console.warn('[dialogs] DialogProvider is not mounted')
    return
  }
  await handlers.showMessage(title, message, options)
}

export async function confirmAction(
  title: string,
  message: string,
  options?: ConfirmOptions,
): Promise<boolean> {
  if (!handlers) {
    console.warn('[dialogs] DialogProvider is not mounted')
    return false
  }
  return handlers.confirmAction(title, message, options)
}
