import { Modal, Pressable, StyleSheet, Text, View } from 'react-native'

import { Button } from './Button'
import { colors } from '../theme/colors'

export type DialogTone = 'default' | 'success' | 'danger' | 'warning'

export interface DialogAction {
  label: string
  variant?: 'primary' | 'outline' | 'ghost' | 'danger'
  onPress: () => void
}

interface AppDialogProps {
  visible: boolean
  title: string
  message: string
  tone?: DialogTone
  actions: DialogAction[]
  onRequestClose?: () => void
}

export function AppDialog({
  visible,
  title,
  message,
  tone = 'default',
  actions,
  onRequestClose,
}: AppDialogProps) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onRequestClose}
    >
      <View style={styles.overlay}>
        <Pressable style={styles.backdrop} onPress={onRequestClose} />
        <View style={styles.card}>
          <View style={[styles.accent, toneStyles[tone]]} />
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.message}>{message}</Text>
          <View style={[styles.actions, actions.length > 1 && styles.actionsRow]}>
            {actions.map((action) => (
              <Button
                key={action.label}
                label={action.label}
                variant={action.variant ?? 'primary'}
                onPress={action.onPress}
                style={actions.length > 1 ? styles.actionBtn : undefined}
              />
            ))}
          </View>
        </View>
      </View>
    </Modal>
  )
}

const toneStyles = StyleSheet.create({
  default: { backgroundColor: colors.grass },
  success: { backgroundColor: colors.grass },
  danger: { backgroundColor: colors.danger },
  warning: { backgroundColor: colors.warning },
})

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    backgroundColor: 'rgba(5, 8, 14, 0.72)',
  },
  backdrop: {
    ...StyleSheet.absoluteFill,
  },
  card: {
    backgroundColor: colors.blackSoft,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 16,
    gap: 10,
    overflow: 'hidden',
  },
  accent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  title: {
    marginTop: 6,
    color: colors.white,
    fontSize: 20,
    fontWeight: '800',
  },
  message: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 22,
  },
  actions: {
    marginTop: 8,
    gap: 10,
  },
  actionsRow: {
    flexDirection: 'row',
  },
  actionBtn: {
    flex: 1,
  },
})
