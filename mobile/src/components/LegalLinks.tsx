import { Linking, StyleSheet, Text } from 'react-native'

import { PRIVACY_URL, TERMS_URL } from '../config'
import { colors } from '../theme/colors'

export function LegalLinks({
  prefix = 'Ao continuar, voce aceita a ',
  align = 'center',
}: {
  prefix?: string
  align?: 'center' | 'left'
}) {
  return (
    <Text style={[styles.text, align === 'left' && styles.textLeft]}>
      {prefix}
      <Text style={styles.link} onPress={() => void Linking.openURL(PRIVACY_URL)}>
        Politica de privacidade
      </Text>
      {' e os '}
      <Text style={styles.link} onPress={() => void Linking.openURL(TERMS_URL)}>
        Termos de uso
      </Text>
      .
    </Text>
  )
}

const styles = StyleSheet.create({
  text: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
  textLeft: {
    textAlign: 'left',
  },
  link: {
    color: colors.grassBright,
    fontWeight: '700',
  },
})
