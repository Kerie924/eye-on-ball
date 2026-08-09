import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { AppDialog, type DialogTone } from '../components/AppDialog'
import { bindDialogHandlers } from '../utils/dialogs'

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

interface DialogContextValue {
  showMessage: (title: string, message: string, options?: MessageOptions) => Promise<void>
  confirmAction: (
    title: string,
    message: string,
    options?: ConfirmOptions,
  ) => Promise<boolean>
}

const DialogContext = createContext<DialogContextValue | null>(null)

type DialogState =
  | {
      kind: 'message'
      title: string
      message: string
      tone: DialogTone
      confirmLabel: string
      resolve: () => void
    }
  | {
      kind: 'confirm'
      title: string
      message: string
      tone: DialogTone
      confirmLabel: string
      cancelLabel: string
      destructive: boolean
      resolve: (value: boolean) => void
    }
  | null

export function DialogProvider({ children }: { children: ReactNode }) {
  const [dialog, setDialog] = useState<DialogState>(null)

  const showMessage = useCallback(
    (title: string, message: string, options?: MessageOptions) =>
      new Promise<void>((resolve) => {
        setDialog({
          kind: 'message',
          title,
          message,
          tone: options?.tone ?? inferTone(title),
          confirmLabel: options?.confirmLabel ?? 'OK',
          resolve,
        })
      }),
    [],
  )

  const confirmAction = useCallback(
    (title: string, message: string, options?: ConfirmOptions) =>
      new Promise<boolean>((resolve) => {
        setDialog({
          kind: 'confirm',
          title,
          message,
          tone: options?.tone ?? (options?.destructive ? 'danger' : 'default'),
          confirmLabel: options?.confirmLabel ?? 'Confirmar',
          cancelLabel: options?.cancelLabel ?? 'Cancelar',
          destructive: options?.destructive ?? false,
          resolve,
        })
      }),
    [],
  )

  useEffect(() => {
    bindDialogHandlers({ showMessage, confirmAction })
    return () => bindDialogHandlers(null)
  }, [showMessage, confirmAction])

  const value = useMemo(
    () => ({ showMessage, confirmAction }),
    [showMessage, confirmAction],
  )

  function closeMessage() {
    if (dialog?.kind !== 'message') return
    const { resolve } = dialog
    setDialog(null)
    resolve()
  }

  function closeConfirm(result: boolean) {
    if (dialog?.kind !== 'confirm') return
    const { resolve } = dialog
    setDialog(null)
    resolve(result)
  }

  return (
    <DialogContext.Provider value={value}>
      {children}
      <AppDialog
        visible={dialog != null}
        title={dialog?.title ?? ''}
        message={dialog?.message ?? ''}
        tone={dialog?.tone}
        onRequestClose={() => {
          if (dialog?.kind === 'message') closeMessage()
          else if (dialog?.kind === 'confirm') closeConfirm(false)
        }}
        actions={
          dialog?.kind === 'confirm'
            ? [
                {
                  label: dialog.cancelLabel,
                  variant: 'ghost',
                  onPress: () => closeConfirm(false),
                },
                {
                  label: dialog.confirmLabel,
                  variant: dialog.destructive ? 'danger' : 'primary',
                  onPress: () => closeConfirm(true),
                },
              ]
            : [
                {
                  label: dialog?.confirmLabel ?? 'OK',
                  variant: 'primary',
                  onPress: closeMessage,
                },
              ]
        }
      />
    </DialogContext.Provider>
  )
}

export function useDialog() {
  const context = useContext(DialogContext)
  if (!context) {
    throw new Error('useDialog must be used within DialogProvider')
  }
  return context
}

function inferTone(title: string): DialogTone {
  const normalized = title.toLowerCase()
  if (normalized.includes('erro') || normalized.includes('falha')) return 'danger'
  if (normalized.includes('indispon')) return 'warning'
  if (
    normalized.includes('enviada') ||
    normalized.includes('sucesso') ||
    normalized.includes('conclu')
  ) {
    return 'success'
  }
  return 'default'
}
