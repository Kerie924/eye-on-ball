import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  type PressableProps,
} from 'react-native'

import { colors } from '../theme/colors'

interface ButtonProps extends Omit<PressableProps, 'style'> {
  label: string
  variant?: 'primary' | 'outline' | 'ghost' | 'danger'
  loading?: boolean
  style?: PressableProps['style']
}

export function Button({
  label,
  variant = 'primary',
  loading = false,
  disabled,
  style,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <Pressable
      style={(state) => {
        const { pressed } = state
        const extraStyle = typeof style === 'function' ? style(state) : style
        return [
          styles.base,
          variant === 'primary' && styles.primary,
          variant === 'outline' && styles.outline,
          variant === 'ghost' && styles.ghost,
          variant === 'danger' && styles.danger,
          pressed && !isDisabled && styles.pressed,
          isDisabled && styles.disabled,
          extraStyle,
        ]
      }}
      disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <ActivityIndicator
          color={
            variant === 'danger'
              ? colors.white
              : variant === 'primary'
                ? colors.textOnGreen
                : colors.grass
          }
        />
      ) : (
        <Text
          style={[
            styles.label,
            variant === 'primary' && styles.primaryLabel,
            variant === 'outline' && styles.outlineLabel,
            variant === 'ghost' && styles.ghostLabel,
            variant === 'danger' && styles.dangerLabel,
          ]}
        >
          {label}
        </Text>
      )}
    </Pressable>
  )
}

const styles = StyleSheet.create({
  base: {
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    backgroundColor: colors.grass,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: colors.grass,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  danger: {
    backgroundColor: colors.danger,
  },
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.99 }],
  },
  disabled: {
    opacity: 0.6,
  },
  label: {
    fontSize: 16,
    fontWeight: '700',
  },
  primaryLabel: {
    color: colors.textOnGreen,
  },
  outlineLabel: {
    color: colors.grass,
  },
  ghostLabel: {
    color: colors.textSecondary,
  },
  dangerLabel: {
    color: colors.white,
  },
})
